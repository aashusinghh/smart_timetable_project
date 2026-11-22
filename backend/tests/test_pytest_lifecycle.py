import pytest
from rest_framework import status
from apps.timetable.models import (
    ScheduleVersion,
    ScheduledMeeting,
    ScheduleChangeAudit,
    DateOverride,
    HolidayCalendar,
)
from apps.timetable.services.reservation_service import TimetableReservationService


@pytest.mark.django_db
class TestScheduleLifecycleAndPublication:

    def test_version_transition_draft_to_under_review_to_published(
        self, api_client, admin_user, coordinator_user, timetable_environment, facilities
    ):
        """
        Verify the complete governance lifecycle:
        1. Draft can be edited by Coordinator.
        2. Coordinator submits draft for review -> Status becomes UNDER_REVIEW.
        3. Editing is locked while UNDER_REVIEW.
        4. Super Admin approves and publishes -> Status becomes PUBLISHED.
        """
        version = timetable_environment['version']
        asgn = timetable_environment['asgn_dbms']
        room = facilities['classroom1']

        # 1. Place a valid meeting while in DRAFT
        meeting = TimetableReservationService.save_meeting(
            schedule_version=version,
            teaching_assignment=asgn,
            weekday=1,
            start_slot=1,
            duration_slots=1,
            room=room,
            user=coordinator_user,
        )

        # 2. Coordinator submits for review
        api_client.force_authenticate(user=coordinator_user)
        submit_url = f"/api/timetable/versions/{version.id}/submit-review/"
        resp_submit = api_client.post(submit_url)
        assert resp_submit.status_code == status.HTTP_200_OK

        version.refresh_from_db()
        assert version.status == ScheduleVersion.Status.UNDER_REVIEW

        # 3. Coordinator attempts mutation while UNDER_REVIEW -> 403 Forbidden
        patch_url = f"/api/timetable/meetings/{meeting.id}/"
        resp_patch = api_client.patch(patch_url, {'start_slot': 2}, format='json')
        assert resp_patch.status_code == status.HTTP_403_FORBIDDEN

        # 4. Super Admin publishes version
        api_client.force_authenticate(user=admin_user)
        publish_url = f"/api/timetable/versions/{version.id}/publish/"
        resp_publish = api_client.post(publish_url)
        assert resp_publish.status_code == status.HTTP_200_OK

        version.refresh_from_db()
        assert version.status == ScheduleVersion.Status.PUBLISHED

    def test_publishing_new_version_archives_previous_published_version(
        self, api_client, admin_user, timetable_environment, academic_setup, facilities
    ):
        """
        Single Active Version Invariant:
        When a new version is published for a term, any existing published version
        for that same term must automatically transition to ARCHIVED.
        """
        term = academic_setup['term']

        # Create an existing published schedule version
        old_version = ScheduleVersion.objects.create(
            term=term,
            version_no=10,
            status=ScheduleVersion.Status.PUBLISHED,
            name='Old Published Version',
        )

        # Create a new draft version
        new_version = ScheduleVersion.objects.create(
            term=term,
            version_no=11,
            status=ScheduleVersion.Status.DRAFT,
            name='New Draft Version',
        )

        # Place a valid meeting in new version
        TimetableReservationService.save_meeting(
            schedule_version=new_version,
            teaching_assignment=timetable_environment['asgn_dbms'],
            weekday=2,
            start_slot=1,
            duration_slots=1,
            room=facilities['classroom1'],
            user=admin_user,
        )

        # Admin publishes new version
        api_client.force_authenticate(user=admin_user)
        resp = api_client.post(f"/api/timetable/versions/{new_version.id}/publish/")
        assert resp.status_code == status.HTTP_200_OK

        new_version.refresh_from_db()
        old_version.refresh_from_db()

        assert new_version.status == ScheduleVersion.Status.PUBLISHED
        assert old_version.status == ScheduleVersion.Status.ARCHIVED

    def test_publishing_version_with_unresolved_conflicts_rejected(
        self, api_client, admin_user, timetable_environment, facilities
    ):
        """
        Governance Safety Check:
        Attempting to publish a schedule version that contains hard conflicts
        must be rejected with HTTP 422 Unprocessable Entity and list remaining conflicts.
        """
        version = timetable_environment['version']
        asgn = timetable_environment['asgn_dbms']
        room = facilities['classroom1']

        # Force a meeting that violates lunch crossing directly into DB
        ScheduledMeeting.objects.create(
            schedule_version=version,
            teaching_assignment=asgn,
            weekday=1,
            start_slot=4,
            duration_slots=2,  # Crosses 12:30 lunch break
            room=room,
        )

        api_client.force_authenticate(user=admin_user)
        resp = api_client.post(f"/api/timetable/versions/{version.id}/publish/")

        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert 'conflicts' in resp.data
        assert len(resp.data['conflicts']) > 0

    def test_date_override_cancels_specific_meeting_instance(
        self, api_client, admin_user, timetable_environment, facilities
    ):
        """
        Calendar Exception Testing:
        Creating a DateOverride for a specific date (e.g. conference leave)
        records the cancellation status without destroying the master recurring weekly schedule.
        """
        api_client.force_authenticate(user=admin_user)
        version = timetable_environment['version']

        meeting = TimetableReservationService.save_meeting(
            schedule_version=version,
            teaching_assignment=timetable_environment['asgn_dbms'],
            weekday=1,
            start_slot=1,
            duration_slots=1,
            room=facilities['classroom1'],
            user=admin_user,
        )

        override_resp = api_client.post('/api/date-overrides/', {
            'scheduled_meeting': meeting.id,
            'original_date': '2026-09-14',
            'status': 'CANCELLED',
            'reason': 'Faculty presenting at IEEE conference',
        }, format='json')

        assert override_resp.status_code == status.HTTP_201_CREATED

        override = DateOverride.objects.get(scheduled_meeting=meeting)
        assert override.status == DateOverride.Status.CANCELLED
        # Master meeting still exists
        assert ScheduledMeeting.objects.filter(id=meeting.id).exists()

    def test_audit_logs_track_all_modifications_with_user_attribution(
        self, api_client, admin_user, timetable_environment, facilities
    ):
        """
        Regulatory Compliance & Auditability:
        Every meeting addition, modification, and deletion must produce
        immutable `ScheduleChangeAudit` rows detailing user, action, and diffs.
        """
        api_client.force_authenticate(user=admin_user)
        version = timetable_environment['version']

        # 1. Create meeting
        meeting = TimetableReservationService.save_meeting(
            schedule_version=version,
            teaching_assignment=timetable_environment['asgn_dbms'],
            weekday=4,
            start_slot=2,
            duration_slots=1,
            room=facilities['classroom1'],
            user=admin_user,
        )

        # 2. Delete meeting
        TimetableReservationService.delete_meeting(
            schedule_version=version,
            meeting_id=meeting.id,
            user=admin_user,
        )

        # Audit logs should exist for CREATE and DELETE
        create_audit = ScheduleChangeAudit.objects.filter(
            schedule_version=version, meeting_id=meeting.id, action='CREATE'
        ).first()
        delete_audit = ScheduleChangeAudit.objects.filter(
            schedule_version=version, meeting_id=meeting.id, action='DELETE'
        ).first()

        assert create_audit is not None
        assert create_audit.user == admin_user
        assert delete_audit is not None
        assert delete_audit.user == admin_user

    def test_under_review_sweep_and_publish_does_not_produce_false_version_under_review_conflicts(
        self, api_client, admin_user, coordinator_user, timetable_environment, academic_setup, facilities
    ):
        """
        Verify that a schedule version in UNDER_REVIEW status does not produce false
        VERSION_UNDER_REVIEW conflicts during full validation sweeps or publication,
        allowing authorized administrators to approve and publish without being falsely blocked.
        """
        term = academic_setup['term']
        version = ScheduleVersion.objects.create(
            term=term,
            version_no=30,
            status=ScheduleVersion.Status.DRAFT,
            name='Review Sweep Test Version',
        )
        asgn = timetable_environment['asgn_dbms']
        room = facilities['classroom1']

        # Place valid meeting in draft
        TimetableReservationService.save_meeting(
            schedule_version=version,
            teaching_assignment=asgn,
            weekday=1,
            start_slot=1,
            duration_slots=1,
            room=room,
            user=admin_user,
        )

        # Transition to UNDER_REVIEW
        api_client.force_authenticate(user=admin_user)
        resp_submit = api_client.post(f"/api/timetable/versions/{version.id}/submit-review/")
        assert resp_submit.status_code == status.HTTP_200_OK

        version.refresh_from_db()
        assert version.status == ScheduleVersion.Status.UNDER_REVIEW

        # 1. Validation Sweep must return valid=True, total_conflicts=0, and no VERSION_UNDER_REVIEW
        resp_sweep = api_client.get(f"/api/timetable/versions/{version.id}/validate-sweep/")
        assert resp_sweep.status_code == status.HTTP_200_OK
        assert resp_sweep.data['valid'] is True
        assert resp_sweep.data['total_conflicts'] == 0
        assert len(resp_sweep.data['conflicts']) == 0

        # 2. Coordinator attempting mutation while UNDER_REVIEW is still blocked with 403
        api_client.force_authenticate(user=coordinator_user)
        resp_coord_place = api_client.post('/api/timetable/meetings/', {
            'schedule_version_id': version.id,
            'teaching_assignment_id': asgn.id,
            'weekday': 2,
            'start_slot': 1,
            'duration_slots': 1,
            'room_id': room.id,
        }, format='json')
        assert resp_coord_place.status_code == status.HTTP_403_FORBIDDEN

        # 3. Super Admin approves and publishes the UNDER_REVIEW version cleanly
        api_client.force_authenticate(user=admin_user)
        resp_publish = api_client.post(f"/api/timetable/versions/{version.id}/publish/")
        assert resp_publish.status_code == status.HTTP_200_OK

        version.refresh_from_db()
        assert version.status == ScheduleVersion.Status.PUBLISHED
