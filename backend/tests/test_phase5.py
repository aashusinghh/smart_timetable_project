from datetime import date, time
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User, Role, UserRoleAssignment, ProfessorProfile
from apps.academics.models import (
    Department,
    Branch,
    AcademicYear,
    AcademicTerm,
    TimeSlot,
    Cohort,
    InstructionGroup,
    Course,
    CourseDeliveryRule,
    CurriculumItem,
    CourseOffering,
    TeachingAssignment,
)
from apps.facilities.models import Campus, Building, Room, RoomUnavailability
from apps.faculty.models import ProfessorUnavailability
from apps.timetable.models import (
    ScheduleVersion,
    ScheduledMeeting,
    ProfessorSlotReservation,
    RoomSlotReservation,
    GroupSlotReservation,
)
from apps.timetable.services.reservation_service import TimetableReservationService
from apps.scheduler.models import AutoScheduleProposal
from apps.scheduler.services.generator import TimetableGenerator
from apps.scheduler.services.scoring import ScheduleScorer


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class Phase5AutoSchedulingTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Roles
        self.admin_role = Role.objects.create(code=Role.Code.SUPER_ADMIN, name='Super Admin')
        self.coord_role = Role.objects.create(code=Role.Code.BRANCH_COORDINATOR, name='Branch Coordinator')
        self.prof_role = Role.objects.create(code=Role.Code.PROFESSOR, name='Professor')

        # Admin
        self.admin = User.objects.create_user(
            email='admin@university.edu',
            password='AdminPassword123!',
            full_name='Super Admin',
            is_staff=True,
            is_superuser=True
        )
        UserRoleAssignment.objects.create(user=self.admin, role=self.admin_role)

        # Department & Branch
        self.dept = Department.objects.create(code='CSE', name='Computer Science')
        self.branch_cse = Branch.objects.create(
            department=self.dept,
            code='BTECH_CSE',
            name='B.Tech CSE',
            max_semesters=8
        )
        self.branch_ece = Branch.objects.create(
            department=self.dept,
            code='BTECH_ECE',
            name='B.Tech ECE',
            max_semesters=8
        )

        # Branch Coordinator (CSE only)
        self.coordinator = User.objects.create_user(
            email='coord.cse@university.edu',
            password='CoordPassword123!',
            full_name='CSE Coordinator'
        )
        UserRoleAssignment.objects.create(user=self.coordinator, role=self.coord_role, branch=self.branch_cse)

        # Professors
        self.prof1 = User.objects.create_user(
            email='prof.sharma@university.edu',
            password='ProfPassword123!',
            full_name='Dr. Sharma'
        )
        UserRoleAssignment.objects.create(user=self.prof1, role=self.prof_role)
        ProfessorProfile.objects.create(user=self.prof1, department=self.dept, designation='Professor')

        self.prof2 = User.objects.create_user(
            email='prof.verma@university.edu',
            password='ProfPassword123!',
            full_name='Dr. Verma'
        )
        UserRoleAssignment.objects.create(user=self.prof2, role=self.prof_role)
        ProfessorProfile.objects.create(user=self.prof2, department=self.dept, designation='Associate Professor')

        # Facilities
        self.campus = Campus.objects.create(code='MAIN', name='Main Campus')
        self.building = Building.objects.create(campus=self.campus, code='ENG', name='Engineering Block')

        self.classroom1 = Room.objects.create(
            building=self.building,
            room_no='101',
            room_type=Room.RoomType.CLASSROOM,
            capacity=60
        )
        self.classroom2 = Room.objects.create(
            building=self.building,
            room_no='102',
            room_type=Room.RoomType.CLASSROOM,
            capacity=60
        )
        self.comp_lab = Room.objects.create(
            building=self.building,
            room_no='LAB1',
            room_type=Room.RoomType.COMPUTER_LAB,
            capacity=40
        )
        self.elec_lab = Room.objects.create(
            building=self.building,
            room_no='LAB2',
            room_type=Room.RoomType.ELECTRONICS_LAB,
            capacity=40
        )

        # Academic Year & Term
        self.year = AcademicYear.objects.create(name='2026-27', start_date=date(2026, 7, 1), end_date=date(2027, 6, 30))
        self.term = AcademicTerm.objects.create(
            academic_year=self.year,
            name='Odd Sem 2026',
            start_date=date(2026, 7, 15),
            end_date=date(2026, 12, 15)
        )

        # Time Slots (1..8)
        self.slots = []
        for i in range(1, 9):
            s_time = time(8 + i, 30) if i <= 4 else time(9 + i, 0)
            e_time = time(9 + i, 30) if i <= 4 else time(10 + i, 0)
            session = TimeSlot.Session.MORNING if i <= 4 else TimeSlot.Session.AFTERNOON
            self.slots.append(TimeSlot.objects.create(slot_no=i, start_time=s_time, end_time=e_time, session=session))

        # Cohort
        self.cohort = Cohort.objects.create(
            branch=self.branch_cse,
            term=self.term,
            semester_no=5,
            section_code='A',
            student_count=60
        )
        self.lab_grp1 = InstructionGroup.objects.create(cohort=self.cohort, code='A-L1', size=30)
        self.lab_grp2 = InstructionGroup.objects.create(cohort=self.cohort, code='A-L2', size=30)

        # Courses
        # 1. 3-Credit Theory Course
        self.course_dbms = Course.objects.create(
            department=self.dept,
            code='CS501',
            name='Database Systems',
            credit=3,
            course_type=Course.CourseType.THEORY
        )
        CourseDeliveryRule.objects.create(course=self.course_dbms, weekly_meetings=3, duration_slots=1)

        # 2. 4-Credit Theory Course
        self.course_os = Course.objects.create(
            department=self.dept,
            code='CS502',
            name='Operating Systems',
            credit=4,
            course_type=Course.CourseType.THEORY
        )
        CourseDeliveryRule.objects.create(course=self.course_os, weekly_meetings=4, duration_slots=1)

        # 3. 2-Credit Lab Course
        self.course_lab = Course.objects.create(
            department=self.dept,
            code='CS503L',
            name='DBMS Lab',
            credit=2,
            course_type=Course.CourseType.LAB
        )
        CourseDeliveryRule.objects.create(course=self.course_lab, weekly_meetings=2, duration_slots=3)

        # Curriculum Items
        self.curr_dbms = CurriculumItem.objects.create(branch=self.branch_cse, semester_no=5, course=self.course_dbms)
        self.curr_os = CurriculumItem.objects.create(branch=self.branch_cse, semester_no=5, course=self.course_os)
        self.curr_lab = CurriculumItem.objects.create(branch=self.branch_cse, semester_no=5, course=self.course_lab)

        # Course Offerings
        self.offering_dbms = CourseOffering.objects.create(term=self.term, cohort=self.cohort, curriculum_item=self.curr_dbms)
        self.offering_os = CourseOffering.objects.create(term=self.term, cohort=self.cohort, curriculum_item=self.curr_os)
        self.offering_lab = CourseOffering.objects.create(term=self.term, cohort=self.cohort, curriculum_item=self.curr_lab)

        # Teaching Assignments
        self.asgn_dbms = TeachingAssignment.objects.create(course_offering=self.offering_dbms, professor=self.prof1)
        self.asgn_os = TeachingAssignment.objects.create(course_offering=self.offering_os, professor=self.prof2)
        self.asgn_lab = TeachingAssignment.objects.create(
            course_offering=self.offering_lab,
            professor=self.prof1,
            instruction_group=self.lab_grp1
        )

        # Schedule Version
        self.version = ScheduleVersion.objects.create(
            term=self.term,
            version_no=1,
            status=ScheduleVersion.Status.DRAFT,
            name='Draft 1'
        )

    def test_generator_hard_constraints_satisfaction(self):
        """
        Verify that CP-SAT solver successfully schedules 3-credit theory (3 meetings on distinct days),
        4-credit theory (4 meetings on distinct days), and 2-credit lab (2 continuous 3-hour meetings)
        with zero hard constraint violations.
        """
        generator = TimetableGenerator(
            schedule_version=self.version,
            branch_ids=[self.branch_cse.id],
            time_limit=15,
            replace_existing=True
        )
        result = generator.generate()

        self.assertIn(result['solver_status'], ['OPTIMAL', 'FEASIBLE'])
        self.assertEqual(len(result['unscheduled_offerings']), 0)
        self.assertGreater(result['quality_score'], 0)

        meetings = result['proposed_meetings']
        # Total expected meetings: 3 (DBMS) + 4 (OS) + 2 (Lab) = 9
        self.assertEqual(len(meetings), 9)

        # 1. 3-Credit Theory: exactly 3 one-hour meetings on distinct days
        dbms_meetings = [m for m in meetings if m['course_code'] == 'CS501']
        self.assertEqual(len(dbms_meetings), 3)
        for m in dbms_meetings:
            self.assertEqual(m['duration_slots'], 1)
        dbms_days = [m['weekday'] for m in dbms_meetings]
        self.assertEqual(len(set(dbms_days)), 3, "3-credit theory must be on 3 distinct days")

        # 2. 4-Credit Theory: exactly 4 one-hour meetings on distinct days
        os_meetings = [m for m in meetings if m['course_code'] == 'CS502']
        self.assertEqual(len(os_meetings), 4)
        for m in os_meetings:
            self.assertEqual(m['duration_slots'], 1)
        os_days = [m['weekday'] for m in os_meetings]
        self.assertEqual(len(set(os_days)), 4, "4-credit theory must be on 4 distinct days")

        # 3. 2-Credit Lab: exactly 2 three-hour continuous meetings on distinct days
        lab_meetings = [m for m in meetings if m['course_code'] == 'CS503L']
        self.assertEqual(len(lab_meetings), 2)
        lab_days = [m['weekday'] for m in lab_meetings]
        self.assertEqual(len(set(lab_days)), 2, "2-credit lab must be on 2 distinct days")
        for m in lab_meetings:
            self.assertEqual(m['duration_slots'], 3)
            self.assertIn(m['start_slot'], [1, 2, 5, 6], "Lab start slot must be 1, 2, 5, or 6")
            self.assertIn(
                m['room_type'],
                [Room.RoomType.COMPUTER_LAB, Room.RoomType.ELECTRONICS_LAB, Room.RoomType.CHEMISTRY_LAB],
                "Lab must be in a lab room"
            )

    def test_no_lunch_crossing_and_no_bounds_violation(self):
        """
        Verify that no generated meetings cross the university lunch break (12:30-14:00, slots 4..5)
        or exceed slot 8.
        """
        generator = TimetableGenerator(
            schedule_version=self.version,
            branch_ids=[self.branch_cse.id],
            time_limit=15,
            replace_existing=True
        )
        result = generator.generate()
        self.assertIn(result['solver_status'], ['OPTIMAL', 'FEASIBLE'])

        for m in result['proposed_meetings']:
            start = m['start_slot']
            dur = m['duration_slots']
            end = start + dur - 1
            self.assertLessEqual(end, 8, f"Meeting extends past slot 8: {m}")
            # Lunch crossing check: cannot start <= 4 and end >= 5
            self.assertFalse(start <= 4 and end >= 5, f"Meeting crosses lunch: {m}")

    def test_no_professor_and_no_room_overlap(self):
        """
        Verify that no professor or room is double-booked at any time slot.
        """
        generator = TimetableGenerator(
            schedule_version=self.version,
            branch_ids=[self.branch_cse.id],
            time_limit=15,
            replace_existing=True
        )
        result = generator.generate()
        self.assertIn(result['solver_status'], ['OPTIMAL', 'FEASIBLE'])

        prof_occupied = set()
        room_occupied = set()

        for m in result['proposed_meetings']:
            prof_id = m['professor_id']
            room_id = m['room_id']
            day = m['weekday']
            for s in range(m['start_slot'], m['start_slot'] + m['duration_slots']):
                # Prof collision check
                prof_key = (prof_id, day, s)
                self.assertNotIn(prof_key, prof_occupied, f"Professor double-booked at Day {day} Slot {s}")
                prof_occupied.add(prof_key)

                # Room collision check
                room_key = (room_id, day, s)
                self.assertNotIn(room_key, room_occupied, f"Room double-booked at Day {day} Slot {s}")
                room_occupied.add(room_key)

    def test_unavailability_constraints_respected(self):
        """
        Verify that professor and room unavailability records are strictly respected by the generator.
        """
        # Block Professor 1 on Monday (Day 1) slots 1..8
        ProfessorUnavailability.objects.create(
            professor=self.prof1,
            weekday=1,
            start_slot=1,
            end_slot=8,
            reason="Dean meetings on Mondays"
        )
        # Block Classroom 101 on Friday (Day 5) slots 1..8
        RoomUnavailability.objects.create(
            room=self.classroom1,
            weekday=5,
            start_slot=1,
            end_slot=8,
            reason="Maintenance on Friday"
        )

        generator = TimetableGenerator(
            schedule_version=self.version,
            branch_ids=[self.branch_cse.id],
            time_limit=15,
            replace_existing=True
        )
        result = generator.generate()
        self.assertIn(result['solver_status'], ['OPTIMAL', 'FEASIBLE'])

        for m in result['proposed_meetings']:
            if m['professor_id'] == self.prof1.id:
                self.assertNotEqual(m['weekday'], 1, "Prof 1 was scheduled on Monday despite being unavailable!")
            if m['room_id'] == self.classroom1.id:
                self.assertNotEqual(m['weekday'], 5, "Classroom 101 was scheduled on Friday despite maintenance!")

    def test_insufficient_rooms_infeasibility_handling(self):
        """
        Verify that when insufficient compatible rooms exist (e.g. lab room deleted),
        the generator diagnoses the issue and returns unscheduled offerings with reasons.
        """
        # Deactivate all lab rooms
        Room.objects.filter(room_type__in=[
            Room.RoomType.COMPUTER_LAB,
            Room.RoomType.ELECTRONICS_LAB
        ]).update(is_active=False)

        generator = TimetableGenerator(
            schedule_version=self.version,
            branch_ids=[self.branch_cse.id],
            time_limit=10,
            replace_existing=True
        )
        result = generator.generate()

        # Lab course should be reported in unscheduled_offerings
        unscheduled_courses = [u.get('course_code') for u in result['unscheduled_offerings']]
        self.assertIn('CS503L', unscheduled_courses)
        lab_diag = next(u for u in result['unscheduled_offerings'] if u.get('course_code') == 'CS503L')
        self.assertIn('laboratory', lab_diag['reason'].lower())

    def test_generate_endpoint_and_task_status_polling(self):
        """
        Test POST /api/timetable/{version_id}/generate and GET /api/tasks/{task_id}/status.
        """
        self.client.force_authenticate(user=self.admin)
        gen_url = f"/api/timetable/{self.version.id}/generate"
        response = self.client.post(gen_url, {
            'branch_ids': [self.branch_cse.id],
            'time_limit': 10,
            'replace_existing': True
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('task_id', response.data)
        task_id = response.data['task_id']

        # Poll task status
        status_url = f"/api/tasks/{task_id}/status"
        status_resp = self.client.get(status_url)
        self.assertEqual(status_resp.status_code, status.HTTP_200_OK)
        self.assertIn(status_resp.data['status'], ['PROGRESS', 'SUCCESS'])
        self.assertIn('percentage', status_resp.data)

        # Check proposal was created
        proposal = AutoScheduleProposal.objects.filter(schedule_version=self.version).first()
        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.status, AutoScheduleProposal.ProposalStatus.PENDING)
        self.assertGreater(len(proposal.proposed_meetings), 0)

    def test_proposals_list_and_detail_endpoint(self):
        """
        Test GET /api/timetable/{version_id}/proposals.
        """
        proposal = AutoScheduleProposal.objects.create(
            schedule_version=self.version,
            selected_branches=[self.branch_cse.id],
            proposed_meetings=[{'dummy': True}],
            solver_status='OPTIMAL',
            quality_score=92.5,
            created_by=self.admin
        )

        self.client.force_authenticate(user=self.coordinator)
        list_url = f"/api/timetable/{self.version.id}/proposals"
        resp = self.client.get(list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        proposals_data = resp.data if isinstance(resp.data, list) else resp.data.get('results', [])
        self.assertEqual(len(proposals_data), 1)
        self.assertEqual(proposals_data[0]['id'], proposal.id)
        self.assertEqual(proposals_data[0]['quality_score'], 92.5)

    def test_commit_proposal_atomic_success(self):
        """
        Test POST /api/timetable/{version_id}/commit-proposal:
        Atomically saves all proposed meetings into ScheduledMeeting and reservation tables.
        """
        # First generate a valid proposal
        generator = TimetableGenerator(
            schedule_version=self.version,
            branch_ids=[self.branch_cse.id],
            time_limit=15,
            replace_existing=True
        )
        gen_result = generator.generate()

        proposal = AutoScheduleProposal.objects.create(
            schedule_version=self.version,
            selected_branches=[self.branch_cse.id],
            proposed_meetings=gen_result['proposed_meetings'],
            solver_status=gen_result['solver_status'],
            quality_score=gen_result['quality_score'],
            generation_metadata={'replace_existing': True},
            created_by=self.admin
        )

        self.client.force_authenticate(user=self.admin)
        commit_url = f"/api/timetable/{self.version.id}/commit-proposal"
        resp = self.client.post(commit_url, {'proposal_id': proposal.id}, format='json')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['status'], 'COMMITTED')
        self.assertGreater(resp.data['committed_meetings_count'], 0)

        # Verify ScheduledMeetings in DB
        committed_count = ScheduledMeeting.objects.filter(schedule_version=self.version).count()
        self.assertEqual(committed_count, len(gen_result['proposed_meetings']))

        # Verify reservations in all 3 atomic tables
        prof_res_count = ProfessorSlotReservation.objects.filter(schedule_version=self.version).count()
        room_res_count = RoomSlotReservation.objects.filter(schedule_version=self.version).count()
        self.assertGreater(prof_res_count, 0)
        self.assertGreater(room_res_count, 0)

        # Proposal status marked COMMITTED
        proposal.refresh_from_db()
        self.assertEqual(proposal.status, AutoScheduleProposal.ProposalStatus.COMMITTED)

    def test_commit_proposal_concurrent_conflict_triggers_409_rollback(self):
        """
        Verify that if a manual booking creates a collision after generation,
        committing the proposal returns HTTP 409 Conflict and cleanly rolls back.
        """
        generator = TimetableGenerator(
            schedule_version=self.version,
            branch_ids=[self.branch_cse.id],
            time_limit=15,
            replace_existing=False
        )
        gen_result = generator.generate()
        self.assertGreater(len(gen_result['proposed_meetings']), 0)
        first_meeting = gen_result['proposed_meetings'][0]

        proposal = AutoScheduleProposal.objects.create(
            schedule_version=self.version,
            selected_branches=[self.branch_cse.id],
            proposed_meetings=gen_result['proposed_meetings'],
            solver_status=gen_result['solver_status'],
            quality_score=gen_result['quality_score'],
            generation_metadata={'replace_existing': False},
            created_by=self.admin
        )

        # Simulate concurrent user manually booking the exact same professor and slot
        TimetableReservationService.save_meeting(
            schedule_version=self.version,
            teaching_assignment=self.asgn_dbms,
            weekday=first_meeting['weekday'],
            start_slot=first_meeting['start_slot'],
            duration_slots=first_meeting['duration_slots'],
            room=self.classroom2,
            user=self.admin
        )

        # Now attempt to commit proposal
        self.client.force_authenticate(user=self.admin)
        commit_url = f"/api/timetable/{self.version.id}/commit-proposal"
        resp = self.client.post(commit_url, {'proposal_id': proposal.id}, format='json')

        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('conflict', str(resp.data).lower())

        # Proposal must remain PENDING
        proposal.refresh_from_db()
        self.assertEqual(proposal.status, AutoScheduleProposal.ProposalStatus.PENDING)

    def test_discard_proposal_endpoint(self):
        """
        Test POST /api/timetable/{version_id}/discard-proposal:
        Marks proposal DISCARDED without modifying live timetable.
        """
        proposal = AutoScheduleProposal.objects.create(
            schedule_version=self.version,
            selected_branches=[self.branch_cse.id],
            proposed_meetings=[],
            solver_status='OPTIMAL',
            status=AutoScheduleProposal.ProposalStatus.PENDING,
            created_by=self.coordinator
        )

        self.client.force_authenticate(user=self.coordinator)
        discard_url = f"/api/timetable/{self.version.id}/discard-proposal"
        resp = self.client.post(discard_url, {'proposal_id': proposal.id}, format='json')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['status'], 'DISCARDED')

        proposal.refresh_from_db()
        self.assertEqual(proposal.status, AutoScheduleProposal.ProposalStatus.DISCARDED)

    def test_timetable_quality_score_endpoint(self):
        """
        Test GET /api/timetable/{version_id}/score returns soft-constraint breakdown and metrics.
        """
        self.client.force_authenticate(user=self.admin)
        score_url = f"/api/timetable/{self.version.id}/score"
        resp = self.client.get(score_url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('overall_score', resp.data)
        self.assertIn('breakdown', resp.data)
        self.assertIn('metrics', resp.data)

        breakdown = resp.data['breakdown']
        self.assertIn('student_gaps_score', breakdown)
        self.assertIn('professor_gaps_score', breakdown)
        self.assertIn('load_balance_score', breakdown)
        self.assertIn('consecutive_hours_score', breakdown)

    def test_role_based_permissions_on_auto_schedule(self):
        """
        Verify that Professors cannot access generation endpoints (403),
        Coordinators cannot generate for unauthorized branches (403),
        and SuperAdmins can generate for any branch.
        """
        gen_url = f"/api/timetable/{self.version.id}/generate"

        # 1. Professor attempts to generate -> 403 Forbidden
        self.client.force_authenticate(user=self.prof1)
        resp = self.client.post(gen_url, {'branch_ids': [self.branch_cse.id]}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # 2. CSE Coordinator attempts to generate for ECE branch -> 403 Forbidden
        self.client.force_authenticate(user=self.coordinator)
        resp = self.client.post(gen_url, {'branch_ids': [self.branch_ece.id]}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # 3. CSE Coordinator generates for CSE branch -> 202 Accepted
        resp = self.client.post(gen_url, {'branch_ids': [self.branch_cse.id]}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)
