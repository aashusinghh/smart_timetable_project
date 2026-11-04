from datetime import date, time
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User, Role, UserRoleAssignment, ProfessorProfile
from apps.academics.models import (
    Department,
    Branch,
    AcademicYear,
    AcademicTerm,
    Cohort,
    InstructionGroup,
    Course,
    CourseDeliveryRule,
    CurriculumItem,
    CourseOffering,
    TeachingAssignment,
)
from apps.facilities.models import Campus, Building, Room
from apps.timetable.models import (
    ScheduleVersion,
    ScheduledMeeting,
    ScheduleChangeAudit,
    HolidayCalendar,
    DateOverride,
)

class Phase4RealTimePublicationTests(TestCase):
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
            full_name='Admin User',
            is_staff=True,
            is_superuser=True
        )
        UserRoleAssignment.objects.create(user=self.admin, role=self.admin_role)

        # Department & Branch
        self.dept = Department.objects.create(code='CSE', name='Computer Science')
        self.branch = Branch.objects.create(
            department=self.dept,
            code='BTECH_CSE',
            name='B.Tech CSE',
            max_semesters=8
        )

        # Coordinator
        self.coord = User.objects.create_user(
            email='coord@university.edu',
            password='CoordPassword123!',
            full_name='CSE Coordinator'
        )
        UserRoleAssignment.objects.create(user=self.coord, role=self.coord_role, branch=self.branch)

        # Faculty Professor
        self.prof = User.objects.create_user(
            email='prof.sharma@university.edu',
            password='ProfPassword123!',
            full_name='Dr. Rajesh Sharma'
        )
        UserRoleAssignment.objects.create(user=self.prof, role=self.prof_role)
        ProfessorProfile.objects.create(user=self.prof, department=self.dept, designation='Professor')

        # Facilities
        self.campus = Campus.objects.create(code='MAIN', name='Main Campus')
        self.building = Building.objects.create(campus=self.campus, code='ENG', name='Eng Block')
        self.classroom = Room.objects.create(
            building=self.building,
            room_no='101',
            room_type=Room.RoomType.CLASSROOM,
            capacity=60
        )
        self.lab_room = Room.objects.create(
            building=self.building,
            room_no='LAB1',
            room_type=Room.RoomType.COMPUTER_LAB,
            capacity=40
        )

        # Term & Year
        self.year = AcademicYear.objects.create(name='2026-27', start_date=date(2026, 8, 1), end_date=date(2027, 6, 30))
        self.term = AcademicTerm.objects.create(academic_year=self.year, name='Odd Sem 2026', start_date=date(2026, 8, 1), end_date=date(2026, 12, 1))

        # Cohort
        self.cohort = Cohort.objects.create(
            branch=self.branch,
            term=self.term,
            semester_no=3,
            section_code='A',
            student_count=60
        )

        # Course & Offering
        self.course = Course.objects.create(code='CS301', name='Database Systems', credit=3, course_type=Course.CourseType.THEORY)
        CourseDeliveryRule.objects.create(course=self.course, weekly_meetings=3, duration_slots=1, preferred_room_type='CLASSROOM')
        self.curr = CurriculumItem.objects.create(branch=self.branch, semester_no=3, course=self.course)
        self.offering = CourseOffering.objects.create(term=self.term, cohort=self.cohort, curriculum_item=self.curr)
        self.asgn = TeachingAssignment.objects.create(course_offering=self.offering, professor=self.prof)

        # Schedule Version (Draft)
        self.version = ScheduleVersion.objects.create(term=self.term, version_no=1, status=ScheduleVersion.Status.DRAFT, name='Draft 1')

    def test_checklist_3_submit_draft_for_review(self):
        """Checklist #3: Submit a draft version for review -> Status becomes UNDER_REVIEW"""
        login_res = self.client.post('/api/auth/login', {'email': 'coord@university.edu', 'password': 'CoordPassword123!'}, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_res.data['access']}")

        res = self.client.post(f'/api/timetable/versions/{self.version.id}/submit-review/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.version.refresh_from_db()
        self.assertEqual(self.version.status, ScheduleVersion.Status.UNDER_REVIEW)

        # Verify audit log entry
        self.assertTrue(ScheduleChangeAudit.objects.filter(schedule_version=self.version, action='SUBMIT_FOR_REVIEW').exists())

    def test_checklist_4_coordinator_cannot_edit_under_review(self):
        """Checklist #4: Edit a meeting in UNDER_REVIEW as Coordinator -> 403 Forbidden"""
        # Place a meeting while in DRAFT
        login_admin = self.client.post('/api/auth/login', {'email': 'admin@university.edu', 'password': 'AdminPassword123!'}, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_admin.data['access']}")
        m_res = self.client.post('/api/timetable/meetings/', {
            'schedule_version_id': self.version.id,
            'teaching_assignment_id': self.asgn.id,
            'weekday': 1,
            'start_slot': 1,
            'duration_slots': 1,
            'room_id': self.classroom.id,
        }, format='json')
        meeting_id = m_res.data['id']

        # Transition to UNDER_REVIEW
        self.version.status = ScheduleVersion.Status.UNDER_REVIEW
        self.version.save()

        # Login as Coordinator
        login_coord = self.client.post('/api/auth/login', {'email': 'coord@university.edu', 'password': 'CoordPassword123!'}, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_coord.data['access']}")

        # Attempt to edit meeting
        patch_res = self.client.patch(f'/api/timetable/meetings/{meeting_id}/', {
            'start_slot': 2,
        }, format='json')
        self.assertEqual(patch_res.status_code, status.HTTP_403_FORBIDDEN)

        # Attempt to delete meeting
        del_res = self.client.delete(f'/api/timetable/meetings/{meeting_id}/')
        self.assertEqual(del_res.status_code, status.HTTP_403_FORBIDDEN)

    def test_checklist_5_publish_version_clean(self):
        """Checklist #5: Publish clean version as Admin -> Status becomes PUBLISHED, archives prior published"""
        # Create an existing published version
        old_published = ScheduleVersion.objects.create(
            term=self.term,
            version_no=99,
            status=ScheduleVersion.Status.PUBLISHED,
            name='Old Published'
        )

        # Save a valid meeting in our draft
        login_admin = self.client.post('/api/auth/login', {'email': 'admin@university.edu', 'password': 'AdminPassword123!'}, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_admin.data['access']}")

        self.client.post('/api/timetable/meetings/', {
            'schedule_version_id': self.version.id,
            'teaching_assignment_id': self.asgn.id,
            'weekday': 1,
            'start_slot': 1,
            'duration_slots': 1,
            'room_id': self.classroom.id,
        }, format='json')

        # Publish
        res = self.client.post(f'/api/timetable/versions/{self.version.id}/publish/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.version.refresh_from_db()
        self.assertEqual(self.version.status, ScheduleVersion.Status.PUBLISHED)

        # Old published version must now be ARCHIVED
        old_published.refresh_from_db()
        self.assertEqual(old_published.status, ScheduleVersion.Status.ARCHIVED)

    def test_checklist_6_publish_with_conflict_rejected(self):
        """Checklist #6: Publish version with conflict -> 422 Unprocessable Entity"""
        login_admin = self.client.post('/api/auth/login', {'email': 'admin@university.edu', 'password': 'AdminPassword123!'}, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_admin.data['access']}")

        # Force a meeting that violates rules (e.g. crossing lunch slot 4 to 5) directly in DB
        ScheduledMeeting.objects.create(
            schedule_version=self.version,
            teaching_assignment=self.asgn,
            weekday=1,
            start_slot=4,
            duration_slots=2, # crosses lunch
            room=self.classroom,
        )

        res = self.client.post(f'/api/timetable/versions/{self.version.id}/publish/')
        self.assertEqual(res.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn('conflicts', res.data)
        self.assertGreater(len(res.data['conflicts']), 0)

    def test_checklist_7_my_timetable_endpoint(self):
        """Checklist #7: GET /api/my-timetable/ for professor returns only their own scheduled classes"""
        # Save a meeting for Dr. Sharma
        ScheduledMeeting.objects.create(
            schedule_version=self.version,
            teaching_assignment=self.asgn,
            weekday=2,
            start_slot=1,
            duration_slots=1,
            room=self.classroom,
        )

        # Login as Dr. Sharma
        login_prof = self.client.post('/api/auth/login', {'email': 'prof.sharma@university.edu', 'password': 'ProfPassword123!'}, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_prof.data['access']}")

        res = self.client.get('/api/my-timetable/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['professor_id'], self.prof.id)
        self.assertEqual(len(res.data['meetings']), 1)
        self.assertEqual(res.data['meetings'][0]['course_code'], 'CS301')

    def test_checklist_8_branch_timetable_endpoint(self):
        """Checklist #8: GET /api/branches/{id}/timetable/ returns branch cohort meetings"""
        ScheduledMeeting.objects.create(
            schedule_version=self.version,
            teaching_assignment=self.asgn,
            weekday=3,
            start_slot=2,
            duration_slots=1,
            room=self.classroom,
        )

        login_admin = self.client.post('/api/auth/login', {'email': 'admin@university.edu', 'password': 'AdminPassword123!'}, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_admin.data['access']}")

        res = self.client.get(f'/api/branches/{self.branch.id}/timetable/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['branch_code'], 'BTECH_CSE')
        self.assertEqual(len(res.data['meetings']), 1)

    def test_checklist_9_holiday_calendar_crud(self):
        """Checklist #9: Add and list holidays via /api/holidays/"""
        login_admin = self.client.post('/api/auth/login', {'email': 'admin@university.edu', 'password': 'AdminPassword123!'}, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_admin.data['access']}")

        create_res = self.client.post('/api/holidays/', {
            'term': self.term.id,
            'date': '2026-10-02',
            'name': 'Gandhi Jayanti',
            'is_academic_holiday': True,
        }, format='json')
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)

        list_res = self.client.get(f'/api/holidays/?term={self.term.id}')
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        results = list_res.data if isinstance(list_res.data, list) else list_res.data.get('results', [])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'Gandhi Jayanti')

    def test_checklist_10_date_override_creation(self):
        """Checklist #10: Create DateOverride (cancel a class on a specific date)"""
        meeting = ScheduledMeeting.objects.create(
            schedule_version=self.version,
            teaching_assignment=self.asgn,
            weekday=1,
            start_slot=1,
            duration_slots=1,
            room=self.classroom,
        )

        login_admin = self.client.post('/api/auth/login', {'email': 'admin@university.edu', 'password': 'AdminPassword123!'}, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_admin.data['access']}")

        res = self.client.post('/api/date-overrides/', {
            'scheduled_meeting': meeting.id,
            'original_date': '2026-09-14',
            'status': 'CANCELLED',
            'reason': 'Faculty attending academic conference',
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        override = DateOverride.objects.get(scheduled_meeting=meeting)
        self.assertEqual(override.status, DateOverride.Status.CANCELLED)

    def test_checklist_11_audit_log_endpoint(self):
        """Checklist #11 & #12: Audit log listing and filtering via /api/audit-logs/"""
        ScheduleChangeAudit.objects.create(
            schedule_version=self.version,
            meeting_id=101,
            action='CREATE',
            before_json={},
            after_json={'course': 'CS301'},
            user=self.admin
        )

        login_admin = self.client.post('/api/auth/login', {'email': 'admin@university.edu', 'password': 'AdminPassword123!'}, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_admin.data['access']}")

        res = self.client.get('/api/audit-logs/?action=CREATE')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data if isinstance(res.data, list) else res.data.get('results', [])
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]['action'], 'CREATE')
