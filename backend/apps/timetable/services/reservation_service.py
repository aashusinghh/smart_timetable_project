from typing import List, Dict, Any, Optional
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from rest_framework.exceptions import APIException
from rest_framework import status
from apps.accounts.models import User
from apps.academics.models import TeachingAssignment, InstructionGroup
from apps.facilities.models import Room
from ..models import (
    ScheduleVersion,
    ScheduledMeeting,
    MeetingInstructionGroup,
    ProfessorSlotReservation,
    RoomSlotReservation,
    GroupSlotReservation,
    ScheduleChangeAudit,
)
from .validator import TimetableValidator

class ConflictException(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'A scheduling collision occurred while reserving slots. Another user may have just booked this slot.'
    default_code = 'slot_conflict'


class TimetableReservationService:
    """
    Transactional Timetable Reservation Service.
    Implements the 10-step atomic save and reservation locking protocol (§8).
    """

    @classmethod
    @transaction.atomic
    def save_meeting(
        cls,
        schedule_version: ScheduleVersion,
        teaching_assignment: TeachingAssignment,
        weekday: int,
        start_slot: int,
        duration_slots: int,
        room: Room,
        instruction_group_ids: Optional[List[int]] = None,
        existing_meeting_id: Optional[int] = None,
        user: Optional[User] = None,
    ) -> ScheduledMeeting:
        # Step 2: Validate authoritative constraints
        val_result = TimetableValidator.validate_meeting_placement(
            schedule_version=schedule_version,
            teaching_assignment=teaching_assignment,
            weekday=weekday,
            start_slot=start_slot,
            duration_slots=duration_slots,
            room=room,
            instruction_group_ids=instruction_group_ids,
            exclude_meeting_id=existing_meeting_id,
            user=user,
        )

        if not val_result['allowed']:
            error_msg = "; ".join(c['message'] for c in val_result['conflicts'])
            conflict_types = [c['type'] for c in val_result['conflicts']]
            if any(t in ['PROFESSOR_BUSY', 'ROOM_BUSY', 'GROUP_BUSY'] for t in conflict_types):
                raise ConflictException(detail={'detail': error_msg, 'conflicts': val_result['conflicts']})
            if any(t in ['VERSION_LOCKED', 'VERSION_UNDER_REVIEW', 'PERMISSION_DENIED'] for t in conflict_types):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied(detail=error_msg)
            raise ValidationError(error_msg)

        # Step 3: Compute affected slots
        slot_numbers = list(range(start_slot, start_slot + duration_slots))

        # Resolve target groups
        target_groups = []
        if teaching_assignment.instruction_group:
            target_groups.append(teaching_assignment.instruction_group)
        elif instruction_group_ids:
            target_groups = list(InstructionGroup.objects.filter(id__in=instruction_group_ids))
        else:
            cohort = teaching_assignment.course_offering.cohort
            target_groups = list(cohort.instruction_groups.all())

        before_state = {}
        action = 'CREATE'

        # If editing an existing meeting, remove its prior reservation rows first
        if existing_meeting_id:
            action = 'UPDATE'
            meeting = ScheduledMeeting.objects.select_for_update().get(
                id=existing_meeting_id,
                schedule_version=schedule_version
            )
            before_state = {
                'weekday': meeting.weekday,
                'start_slot': meeting.start_slot,
                'duration_slots': meeting.duration_slots,
                'room_id': meeting.room_id,
            }
            # Clean up old reservations
            ProfessorSlotReservation.objects.filter(scheduled_meeting=meeting).delete()
            RoomSlotReservation.objects.filter(scheduled_meeting=meeting).delete()
            GroupSlotReservation.objects.filter(scheduled_meeting=meeting).delete()
            MeetingInstructionGroup.objects.filter(scheduled_meeting=meeting).delete()

            # Update meeting attributes
            meeting.teaching_assignment = teaching_assignment
            meeting.weekday = weekday
            meeting.start_slot = start_slot
            meeting.duration_slots = duration_slots
            meeting.room = room
            meeting.save()
        else:
            # Step 5: Insert scheduled_meeting
            meeting = ScheduledMeeting.objects.create(
                schedule_version=schedule_version,
                teaching_assignment=teaching_assignment,
                weekday=weekday,
                start_slot=start_slot,
                duration_slots=duration_slots,
                room=room,
                created_by=user,
            )

        # Link instruction groups
        for grp in target_groups:
            MeetingInstructionGroup.objects.create(
                scheduled_meeting=meeting,
                instruction_group=grp
            )

        # Step 6 & 7: Insert reservation rows in all 3 atomic tables
        try:
            # Professor reservations
            for s in slot_numbers:
                ProfessorSlotReservation.objects.create(
                    schedule_version=schedule_version,
                    professor=teaching_assignment.professor,
                    weekday=weekday,
                    slot_no=s,
                    scheduled_meeting=meeting
                )

            # Room reservations
            for s in slot_numbers:
                RoomSlotReservation.objects.create(
                    schedule_version=schedule_version,
                    room=room,
                    weekday=weekday,
                    slot_no=s,
                    scheduled_meeting=meeting
                )

            # Student group reservations
            for grp in target_groups:
                for s in slot_numbers:
                    GroupSlotReservation.objects.create(
                        schedule_version=schedule_version,
                        instruction_group=grp,
                        weekday=weekday,
                        slot_no=s,
                        scheduled_meeting=meeting
                    )

        except IntegrityError as exc:
            # Catch duplicate unique key in MySQL / SQLite -> HTTP 409 Conflict
            raise ConflictException(
                detail={
                    'detail': 'Concurrent slot reservation detected! Another user just reserved this professor, room, or student group.',
                    'database_error': str(exc)
                }
            )

        # Step 8: Audit log
        after_state = {
            'meeting_id': meeting.id,
            'weekday': weekday,
            'start_slot': start_slot,
            'duration_slots': duration_slots,
            'room_id': room.id,
            'professor_id': teaching_assignment.professor_id,
            'groups': [g.id for g in target_groups],
        }
        ScheduleChangeAudit.objects.create(
            schedule_version=schedule_version,
            meeting_id=meeting.id,
            action=action,
            before_json=before_state,
            after_json=after_state,
            user=user
        )

        # Step 9: Increment revision
        schedule_version.revision += 1
        schedule_version.save(update_fields=['revision', 'updated_at'])

        # Step 10: WebSocket broadcast trigger (stubbed for Phase 4)
        cls._broadcast_ws_event(schedule_version, f"meeting.{action.lower()}", after_state)

        return meeting

    @classmethod
    @transaction.atomic
    def delete_meeting(
        cls,
        schedule_version: ScheduleVersion,
        meeting_id: int,
        user: Optional[User] = None
    ) -> bool:
        from rest_framework.exceptions import PermissionDenied
        from apps.accounts.models import Role

        if schedule_version.status in [ScheduleVersion.Status.PUBLISHED, ScheduleVersion.Status.ARCHIVED]:
            raise PermissionDenied(f"Schedule version is {schedule_version.get_status_display()} and cannot be modified.")
        if schedule_version.status == ScheduleVersion.Status.UNDER_REVIEW:
            is_admin = user and (user.is_superuser or user.has_role(Role.Code.SUPER_ADMIN))
            if not is_admin:
                raise PermissionDenied("Schedule version is currently UNDER_REVIEW and cannot be modified by coordinators.")

        try:
            meeting = ScheduledMeeting.objects.select_for_update().get(
                id=meeting_id,
                schedule_version=schedule_version
            )
        except ScheduledMeeting.DoesNotExist:
            return False

        before_state = {
            'meeting_id': meeting.id,
            'course': meeting.teaching_assignment.course_offering.curriculum_item.course.code,
            'professor': meeting.teaching_assignment.professor.full_name,
            'weekday': meeting.weekday,
            'start_slot': meeting.start_slot,
            'duration_slots': meeting.duration_slots,
            'room_id': meeting.room_id,
        }

        # Reservations cascade on meeting deletion, but explicitly remove to guarantee clean atomic state
        ProfessorSlotReservation.objects.filter(scheduled_meeting=meeting).delete()
        RoomSlotReservation.objects.filter(scheduled_meeting=meeting).delete()
        GroupSlotReservation.objects.filter(scheduled_meeting=meeting).delete()
        meeting.delete()

        # Audit
        ScheduleChangeAudit.objects.create(
            schedule_version=schedule_version,
            meeting_id=meeting_id,
            action='DELETE',
            before_json=before_state,
            after_json={},
            user=user
        )

        schedule_version.revision += 1
        schedule_version.save(update_fields=['revision', 'updated_at'])

        cls._broadcast_ws_event(schedule_version, "meeting.deleted", {'meeting_id': meeting_id})
        return True

    @classmethod
    @transaction.atomic
    def batch_update(
        cls,
        schedule_version: ScheduleVersion,
        updates: List[Dict[str, Any]],
        user: Optional[User] = None
    ) -> List[ScheduledMeeting]:
        """
        Validates and updates multiple meetings in one single atomic transaction.
        If any clash occurs, the entire batch rolls back.
        """
        results = []
        for item in updates:
            meeting_id = item.get('meeting_id')
            teaching_assignment = TeachingAssignment.objects.get(id=item['teaching_assignment_id'])
            room = Room.objects.get(id=item['room_id'])
            saved = cls.save_meeting(
                schedule_version=schedule_version,
                teaching_assignment=teaching_assignment,
                weekday=item['weekday'],
                start_slot=item['start_slot'],
                duration_slots=item['duration_slots'],
                room=room,
                instruction_group_ids=item.get('instruction_group_ids'),
                existing_meeting_id=meeting_id,
                user=user
            )
            results.append(saved)
        cls._broadcast_ws_event(schedule_version, "meeting.batch_updated", {'count': len(results)})
        return results

    @staticmethod
    def _broadcast_ws_event(schedule_version: ScheduleVersion, event_type: str, payload: dict):
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"timetable_{schedule_version.id}",
                    {
                        "type": "timetable.broadcast",
                        "event_type": event_type,
                        "payload": payload,
                        "revision": schedule_version.revision,
                        "status": schedule_version.status,
                    }
                )
        except Exception:
            pass
