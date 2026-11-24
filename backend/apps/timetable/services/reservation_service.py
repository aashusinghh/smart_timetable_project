from typing import List, Dict, Any, Optional
from django.db import transaction, IntegrityError
from rest_framework.exceptions import ValidationError, APIException
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
            raise ValidationError(detail={'detail': error_msg, 'conflicts': val_result['conflicts']})

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

        if user and not user.is_superuser and not user.has_role(Role.Code.SUPER_ADMIN):
            cohort_branch = meeting.teaching_assignment.course_offering.cohort.branch
            coord_branch_ids = user.get_coordinated_branch_ids() if hasattr(user, 'get_coordinated_branch_ids') else None
            has_branch_coord = (
                cohort_branch.id in coord_branch_ids
                if coord_branch_ids is not None
                else user.role_assignments.filter(
                    role__code=Role.Code.BRANCH_COORDINATOR,
                    branch=cohort_branch
                ).exists()
            )
            if not has_branch_coord:
                raise PermissionDenied(f"You do not have coordinator permissions for branch {cohort_branch.code}.")

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
    def clear_department_semester_meetings(
        cls,
        schedule_version: ScheduleVersion,
        department_id: Optional[int] = None,
        semester_no: Optional[int] = None,
        branch_id: Optional[int] = None,
        cohort_id: Optional[int] = None,
        clear_all: bool = False,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        Clears scheduled meetings and associated reservations for a specified
        cohort, branch, semester, department, or entire draft schedule.
        """
        from rest_framework.exceptions import PermissionDenied
        from apps.accounts.models import Role

        if schedule_version.status in [ScheduleVersion.Status.PUBLISHED, ScheduleVersion.Status.ARCHIVED]:
            raise PermissionDenied(f"Schedule version is {schedule_version.get_status_display()} and cannot be modified.")
        if schedule_version.status == ScheduleVersion.Status.UNDER_REVIEW:
            is_admin = user and (user.is_superuser or user.has_role(Role.Code.SUPER_ADMIN))
            if not is_admin:
                raise PermissionDenied("Schedule version is currently UNDER_REVIEW and cannot be modified by coordinators.")

        if user and not user.is_superuser and not user.has_role(Role.Code.SUPER_ADMIN):
            coord_branch_ids = user.get_coordinated_branch_ids() if hasattr(user, 'get_coordinated_branch_ids') else None
            if coord_branch_ids is not None:
                if clear_all or department_id:
                    raise PermissionDenied("Branch coordinators can only clear schedule meetings of their assigned branch.")
                if branch_id and branch_id not in coord_branch_ids:
                    raise PermissionDenied("You can only clear schedule meetings for your assigned branch.")
                if cohort_id:
                    from apps.academics.models import Cohort
                    cohort = Cohort.objects.filter(id=cohort_id).first()
                    if cohort and cohort.branch_id not in coord_branch_ids:
                        raise PermissionDenied("You can only clear schedule meetings for your assigned branch.")

        meetings_qs = ScheduledMeeting.objects.filter(schedule_version=schedule_version)

        if not clear_all:
            if cohort_id:
                meetings_qs = meetings_qs.filter(
                    teaching_assignment__course_offering__cohort_id=cohort_id
                )
            elif branch_id:
                meetings_qs = meetings_qs.filter(
                    teaching_assignment__course_offering__cohort__branch_id=branch_id
                )
                if semester_no is not None:
                    meetings_qs = meetings_qs.filter(
                        teaching_assignment__course_offering__cohort__semester_no=semester_no
                    )
            elif department_id:
                meetings_qs = meetings_qs.filter(
                    teaching_assignment__course_offering__cohort__branch__department_id=department_id
                )
                if semester_no is not None:
                    meetings_qs = meetings_qs.filter(
                        teaching_assignment__course_offering__cohort__semester_no=semester_no
                    )
            elif semester_no is not None:
                meetings_qs = meetings_qs.filter(
                    teaching_assignment__course_offering__cohort__semester_no=semester_no
                )

        meeting_ids = list(meetings_qs.select_for_update().values_list('id', flat=True))
        deleted_count = len(meeting_ids)

        if deleted_count > 0:
            # Explicitly remove slot reservations
            ProfessorSlotReservation.objects.filter(scheduled_meeting_id__in=meeting_ids).delete()
            RoomSlotReservation.objects.filter(scheduled_meeting_id__in=meeting_ids).delete()
            GroupSlotReservation.objects.filter(scheduled_meeting_id__in=meeting_ids).delete()

            # Delete the meeting records
            ScheduledMeeting.objects.filter(id__in=meeting_ids).delete()

            # Audit record
            ScheduleChangeAudit.objects.create(
                schedule_version=schedule_version,
                meeting_id=None,
                action='CLEAR_TIMETABLE',
                before_json={
                    'department_id': department_id,
                    'semester_no': semester_no,
                    'branch_id': branch_id,
                    'cohort_id': cohort_id,
                    'clear_all': clear_all,
                    'deleted_count': deleted_count,
                    'deleted_meeting_ids': meeting_ids,
                },
                after_json={},
                user=user
            )

            # Bump version revision for live sync
            schedule_version.revision += 1
            schedule_version.save(update_fields=['revision', 'updated_at'])

            cls._broadcast_ws_event(
                schedule_version,
                "schedule.cleared",
                {
                    'schedule_version_id': schedule_version.id,
                    'department_id': department_id,
                    'semester_no': semester_no,
                    'branch_id': branch_id,
                    'cohort_id': cohort_id,
                    'clear_all': clear_all,
                    'deleted_count': deleted_count,
                }
            )

        return {
            'deleted_count': deleted_count,
            'message': f"Successfully removed {deleted_count} class(es) from the timetable.",
            'department_id': department_id,
            'semester_no': semester_no,
            'branch_id': branch_id,
            'cohort_id': cohort_id,
            'clear_all': clear_all,
        }

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
            # InMemoryChannelLayer deadlocks with async_to_sync across synchronous worker threads on Windows; only broadcast when external layer (e.g. Redis) is used
            if channel_layer and 'InMemoryChannelLayer' not in type(channel_layer).__name__:
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
