from typing import Dict, Any, List
from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError, APIException
from rest_framework import status
from apps.accounts.models import Role, User
from ..models import ScheduleVersion, ScheduledMeeting, ScheduleChangeAudit
from .validator import TimetableValidator
from .reservation_service import TimetableReservationService

class PublicationConflictException(APIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = 'Cannot publish schedule: unresolved collisions or constraint violations exist.'
    default_code = 'schedule_has_conflicts'

class TimetablePublicationService:
    @classmethod
    def submit_for_review(cls, schedule_version: ScheduleVersion, user: User) -> ScheduleVersion:
        """
        Transition schedule from DRAFT -> UNDER_REVIEW.
        Allows branch coordinators and super admins to lock drafting and submit for review.
        """
        if schedule_version.status != ScheduleVersion.Status.DRAFT:
            raise ValidationError(f"Only DRAFT schedules can be submitted for review (current status: {schedule_version.status}).")

        # Permission check: must be coordinator or admin
        is_admin = user.is_superuser or user.has_role(Role.Code.SUPER_ADMIN)
        is_coord = user.has_role(Role.Code.BRANCH_COORDINATOR)
        if not (is_admin or is_coord):
            raise PermissionDenied("Only Branch Coordinators or Super Administrators can submit schedules for review.")

        schedule_version.status = ScheduleVersion.Status.UNDER_REVIEW
        schedule_version.revision += 1
        schedule_version.save(update_fields=['status', 'revision', 'updated_at'])

        ScheduleChangeAudit.objects.create(
            schedule_version=schedule_version,
            meeting_id=None,
            action='SUBMIT_FOR_REVIEW',
            before_json={'status': ScheduleVersion.Status.DRAFT},
            after_json={'status': ScheduleVersion.Status.UNDER_REVIEW},
            user=user
        )

        TimetableReservationService._broadcast_ws_event(
            schedule_version,
            "schedule.status_changed",
            {'status': ScheduleVersion.Status.UNDER_REVIEW, 'message': 'Schedule submitted for review.'}
        )

        return schedule_version

    @classmethod
    def send_back_to_draft(cls, schedule_version: ScheduleVersion, user: User, reason: str = '') -> ScheduleVersion:
        """
        Admin rejects/sends back an UNDER_REVIEW schedule to DRAFT so coordinators can adjust it.
        """
        is_admin = user.is_superuser or user.has_role(Role.Code.SUPER_ADMIN)
        if not is_admin:
            raise PermissionDenied("Only Super Administrators can send a schedule back to draft.")

        if schedule_version.status != ScheduleVersion.Status.UNDER_REVIEW:
            raise ValidationError(f"Only schedules currently UNDER_REVIEW can be sent back to draft (current: {schedule_version.status}).")

        schedule_version.status = ScheduleVersion.Status.DRAFT
        schedule_version.revision += 1
        schedule_version.save(update_fields=['status', 'revision', 'updated_at'])

        ScheduleChangeAudit.objects.create(
            schedule_version=schedule_version,
            meeting_id=None,
            action='SEND_BACK_DRAFT',
            before_json={'status': ScheduleVersion.Status.UNDER_REVIEW},
            after_json={'status': ScheduleVersion.Status.DRAFT, 'reason': reason},
            user=user
        )

        TimetableReservationService._broadcast_ws_event(
            schedule_version,
            "schedule.status_changed",
            {'status': ScheduleVersion.Status.DRAFT, 'message': 'Schedule returned to draft status.', 'reason': reason}
        )

        return schedule_version

    @classmethod
    def full_sweep_validation(cls, schedule_version: ScheduleVersion) -> List[Dict[str, Any]]:
        """
        Performs a full authoritative validation sweep across all meetings in this schedule version.
        Returns a list of any clashes or rule violations found.
        """
        all_conflicts = []
        meetings = ScheduledMeeting.objects.filter(schedule_version=schedule_version).select_related(
            'teaching_assignment__course_offering__cohort__branch',
            'teaching_assignment__course_offering__curriculum_item__course',
            'teaching_assignment__professor',
            'room'
        ).prefetch_related('meeting_instruction_groups__instruction_group')

        for m in meetings:
            group_ids = [mig.instruction_group_id for mig in m.meeting_instruction_groups.all()]
            val_res = TimetableValidator.validate_meeting_placement(
                schedule_version=schedule_version,
                teaching_assignment=m.teaching_assignment,
                weekday=m.weekday,
                start_slot=m.start_slot,
                duration_slots=m.duration_slots,
                room=m.room,
                instruction_group_ids=group_ids,
                exclude_meeting_id=m.id,
                user=None, # System validation bypasses coordinator branch restriction
            )
            if not val_res['allowed']:
                for c in val_res['conflicts']:
                    c['meeting_id'] = m.id
                    c['course_code'] = m.teaching_assignment.course_offering.curriculum_item.course.code
                    all_conflicts.append(c)

        return all_conflicts

    @classmethod
    @transaction.atomic
    def publish_schedule(cls, schedule_version: ScheduleVersion, user: User) -> ScheduleVersion:
        """
        Super Admin publishes schedule version after verifying 0 clashes exist.
        Archives any previously published version for this academic term.
        """
        is_admin = user.is_superuser or user.has_role(Role.Code.SUPER_ADMIN)
        if not is_admin:
            raise PermissionDenied("Only Super Administrators can publish timetable schedules.")

        if schedule_version.status == ScheduleVersion.Status.PUBLISHED:
            raise ValidationError("This schedule version is already PUBLISHED.")

        # 1. Full-sweep validation check
        conflicts = cls.full_sweep_validation(schedule_version)
        if conflicts:
            raise PublicationConflictException(detail={
                'detail': f'Cannot publish schedule: found {len(conflicts)} unresolved collision(s) or constraint violation(s).',
                'conflicts': conflicts
            })

        # 2. Archive any previous published version for the same term
        ScheduleVersion.objects.filter(
            term=schedule_version.term,
            status=ScheduleVersion.Status.PUBLISHED
        ).exclude(id=schedule_version.id).update(status=ScheduleVersion.Status.ARCHIVED)

        # 3. Transition current version to PUBLISHED
        schedule_version.status = ScheduleVersion.Status.PUBLISHED
        schedule_version.revision += 1
        schedule_version.save(update_fields=['status', 'revision', 'updated_at'])

        # 4. Audit Log
        ScheduleChangeAudit.objects.create(
            schedule_version=schedule_version,
            meeting_id=None,
            action='PUBLISH',
            before_json={'status': ScheduleVersion.Status.UNDER_REVIEW},
            after_json={'status': ScheduleVersion.Status.PUBLISHED},
            user=user
        )

        # 5. Broadcast WebSocket publication event
        TimetableReservationService._broadcast_ws_event(
            schedule_version,
            "schedule.published",
            {
                'schedule_version_id': schedule_version.id,
                'term_id': schedule_version.term_id,
                'term_name': schedule_version.term.name,
                'status': 'PUBLISHED',
                'message': f"Timetable for {schedule_version.term.name} is now officially PUBLISHED!"
            }
        )

        return schedule_version
