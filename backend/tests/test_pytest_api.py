import pytest
from rest_framework import status
from apps.scheduler.models import AutoScheduleProposal


@pytest.mark.django_db
class TestTimetableApiEndpoints:

    def test_auth_login_and_me_flow(self, api_client, admin_user):
        """Verify JWT login issue and /api/auth/me response contains correct roles."""
        login_resp = api_client.post('/api/auth/login', {
            'email': admin_user.email,
            'password': 'AdminPassword123!',
        }, format='json')

        assert login_resp.status_code == status.HTTP_200_OK
        assert 'access' in login_resp.data
        token = login_resp.data['access']

        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        me_resp = api_client.get('/api/auth/me')
        assert me_resp.status_code == status.HTTP_200_OK
        assert me_resp.data['email'] == admin_user.email
        assert 'SUPER_ADMIN' in me_resp.data['roles']

    def test_validate_slot_endpoint(self, api_client, admin_user, timetable_environment, facilities):
        """Test POST /api/timetable/validate returns JSON allow decision and conflict lists."""
        api_client.force_authenticate(user=admin_user)
        version = timetable_environment['version']
        asgn = timetable_environment['asgn_dbms']
        room = facilities['classroom1']

        resp = api_client.post('/api/timetable/validate', {
            'schedule_version_id': version.id,
            'teaching_assignment_id': asgn.id,
            'weekday': 1,
            'start_slot': 1,
            'duration_slots': 1,
            'room_id': room.id,
        }, format='json')

        assert resp.status_code == status.HTTP_200_OK
        assert 'allowed' in resp.data
        assert resp.data['allowed'] is True
        assert isinstance(resp.data['conflicts'], list)

    def test_slots_availability_endpoint(self, api_client, admin_user, timetable_environment, facilities):
        """Test POST /api/timetable/slots-availability returns availability for all 40 weekly slots."""
        api_client.force_authenticate(user=admin_user)
        version = timetable_environment['version']
        asgn = timetable_environment['asgn_dbms']
        room = facilities['classroom1']

        resp = api_client.post('/api/timetable/slots-availability', {
            'schedule_version_id': version.id,
            'teaching_assignment_id': asgn.id,
            'room_id': room.id,
            'duration_slots': 1,
        }, format='json')

        assert resp.status_code == status.HTTP_200_OK
        assert 'slots' in resp.data
        slots = resp.data['slots']
        assert len(slots) == 40  # 5 weekdays * 8 slots

        # Verify weekday 1, slot 1 is initially available
        slot_w1_s1 = next(s for s in slots if s['weekday'] == 1 and s['slot_no'] == 1)
        assert slot_w1_s1['allowed'] is True
        assert slot_w1_s1['status'] == 'AVAILABLE'

        # Now place a meeting at weekday 1, slot 1
        save_resp = api_client.post('/api/timetable/meetings/', {
            'schedule_version_id': version.id,
            'teaching_assignment_id': asgn.id,
            'weekday': 1,
            'start_slot': 1,
            'duration_slots': 1,
            'room_id': room.id,
        }, format='json')
        assert save_resp.status_code == status.HTTP_201_CREATED

        # Re-check slot availability
        resp2 = api_client.post('/api/timetable/slots-availability', {
            'schedule_version_id': version.id,
            'teaching_assignment_id': asgn.id,
            'room_id': room.id,
            'duration_slots': 1,
        }, format='json')
        assert resp2.status_code == status.HTTP_200_OK
        slots2 = resp2.data['slots']
        slot_w1_s1_after = next(s for s in slots2 if s['weekday'] == 1 and s['slot_no'] == 1)
        assert slot_w1_s1_after['allowed'] is False
        assert slot_w1_s1_after['status'] == 'BUSY'
        assert slot_w1_s1_after['conflict_type'] in ['ROOM_BUSY', 'PROFESSOR_BUSY', 'COHORT_BUSY']

    def test_role_based_generation_permissions(
        self, api_client, professor_user, coordinator_user, admin_user, timetable_environment, academic_setup
    ):
        """
        Verify strict role permissions:
        1. Professor is forbidden (403) from generating timetables.
        2. Coordinator is forbidden (403) from generating timetables for other branches.
        3. Coordinator can generate for their assigned branch (202 Accepted).
        """
        version = timetable_environment['version']
        branch_cse = academic_setup['branch_cse']
        branch_ece = academic_setup['branch_ece']
        gen_url = f"/api/timetable/{version.id}/generate"

        # 1. Professor forbidden
        api_client.force_authenticate(user=professor_user)
        resp = api_client.post(gen_url, {'branch_ids': [branch_cse.id]}, format='json')
        assert resp.status_code == status.HTTP_403_FORBIDDEN

        # 2. Coordinator for CSE attempts ECE branch -> 403 Forbidden
        api_client.force_authenticate(user=coordinator_user)
        resp = api_client.post(gen_url, {'branch_ids': [branch_ece.id]}, format='json')
        assert resp.status_code == status.HTTP_403_FORBIDDEN

        # 3. Coordinator for CSE generates CSE branch -> 202 Accepted
        resp = api_client.post(gen_url, {
            'branch_ids': [branch_cse.id],
            'time_limit': 10,
            'replace_existing': True,
        }, format='json')
        assert resp.status_code == status.HTTP_202_ACCEPTED
        assert 'task_id' in resp.data

    def test_discard_proposal_endpoint(self, api_client, coordinator_user, timetable_environment, academic_setup):
        """Test POST /api/timetable/{version_id}/discard-proposal sets status to DISCARDED."""
        version = timetable_environment['version']
        branch_cse = academic_setup['branch_cse']

        proposal = AutoScheduleProposal.objects.create(
            schedule_version=version,
            selected_branches=[branch_cse.id],
            proposed_meetings=[],
            solver_status='OPTIMAL',
            status=AutoScheduleProposal.ProposalStatus.PENDING,
            created_by=coordinator_user,
        )

        api_client.force_authenticate(user=coordinator_user)
        discard_url = f"/api/timetable/{version.id}/discard-proposal"
        resp = api_client.post(discard_url, {'proposal_id': proposal.id}, format='json')

        assert resp.status_code == status.HTTP_200_OK
        assert resp.data['status'] == 'DISCARDED'

        proposal.refresh_from_db()
        assert proposal.status == AutoScheduleProposal.ProposalStatus.DISCARDED

    def test_timetable_score_endpoint(self, api_client, admin_user, timetable_environment):
        """Test GET /api/timetable/{version_id}/score returns 200 OK and metric keys."""
        api_client.force_authenticate(user=admin_user)
        version = timetable_environment['version']

        resp = api_client.get(f"/api/timetable/{version.id}/score")
        assert resp.status_code == status.HTTP_200_OK
        assert 'overall_score' in resp.data
        assert 'breakdown' in resp.data
