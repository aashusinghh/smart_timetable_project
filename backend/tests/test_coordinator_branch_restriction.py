import pytest
from datetime import date, time
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User, Role, UserRoleAssignment
from apps.academics.models import (
    Department, Branch, AcademicYear, AcademicTerm,
    Cohort, InstructionGroup, Course, CourseDeliveryRule,
    CurriculumItem, CourseOffering, TeachingAssignment, TimeSlot
)
from apps.facilities.models import Campus, Building, Room
from apps.timetable.models import ScheduleVersion, ScheduledMeeting


class TestBranchCoordinatorRestrictions(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Roles
        self.admin_role, _ = Role.objects.get_or_create(code=Role.Code.SUPER_ADMIN, defaults={'name': 'Super Admin'})
        self.coord_role, _ = Role.objects.get_or_create(code=Role.Code.BRANCH_COORDINATOR, defaults={'name': 'Branch Coordinator'})
        self.prof_role, _ = Role.objects.get_or_create(code=Role.Code.PROFESSOR, defaults={'name': 'Professor'})

        # Departments
        self.dept_cse = Department.objects.create(code='CSE', name='Computer Science & Engineering')
        self.dept_ece = Department.objects.create(code='ECE', name='Electronics & Communication Engineering')

        # Branches
        self.branch_cse = Branch.objects.create(
            department=self.dept_cse,
            code='BTECH_CSE',
            name='B.Tech CSE',
            max_semesters=8
        )
        self.branch_ece = Branch.objects.create(
            department=self.dept_ece,
            code='BTECH_ECE',
            name='B.Tech ECE',
            max_semesters=8
        )

        # Users
        self.admin_user = User.objects.create_superuser(
            email='admin@nitjsr.ac.in',
            password='AdminPassword123!',
            full_name='Super Admin'
        )

        self.cse_coord = User.objects.create_user(
            email='coord.cse@nitjsr.ac.in',
            password='CoordPassword123!',
            full_name='CSE Branch Coordinator'
        )
        UserRoleAssignment.objects.create(user=self.cse_coord, role=self.coord_role, branch=self.branch_cse)

        self.prof_cse = User.objects.create_user(
            email='prof.cse@nitjsr.ac.in',
            password='ProfPassword123!',
            full_name='Prof. CSE'
        )
        UserRoleAssignment.objects.create(user=self.prof_cse, role=self.prof_role)

        self.prof_ece = User.objects.create_user(
            email='prof.ece@nitjsr.ac.in',
            password='ProfPassword123!',
            full_name='Prof. ECE'
        )
        UserRoleAssignment.objects.create(user=self.prof_ece, role=self.prof_role)

        # Facility
        self.campus = Campus.objects.create(code='MAIN', name='Main Campus')
        self.bldg = Building.objects.create(campus=self.campus, code='ALB', name='Academic Block')
        self.room = Room.objects.create(
            building=self.bldg, room_no='CSE-101', capacity=60, room_type='CLASSROOM'
        )

        # Academic Calendar
        self.ay = AcademicYear.objects.create(name='2026-27', start_date=date(2026, 7, 1), end_date=date(2027, 6, 30))
        self.term = AcademicTerm.objects.create(
            academic_year=self.ay, name='Autumn 2026', term_type='ODD',
            start_date=date(2026, 8, 1), end_date=date(2026, 12, 15)
        )

        # Slots
        for i in range(1, 9):
            TimeSlot.objects.create(
                slot_no=i,
                start_time=time(8 + i, 0),
                end_time=time(9 + i, 0),
                session=TimeSlot.Session.MORNING if i <= 4 else TimeSlot.Session.AFTERNOON
            )

        # Cohorts
        self.cohort_cse = Cohort.objects.create(
            branch=self.branch_cse, term=self.term, semester_no=3, section_code='A', student_count=60
        )
        self.cohort_ece = Cohort.objects.create(
            branch=self.branch_ece, term=self.term, semester_no=3, section_code='A', student_count=60
        )

        # Courses
        self.course_cse = Course.objects.create(
            code='CS201', name='Data Structures', branch=self.branch_cse, department=self.dept_cse, semester=3, professor=self.prof_cse
        )
        CourseDeliveryRule.objects.create(course=self.course_cse, weekly_meetings=3, duration_slots=1)

        self.course_ece = Course.objects.create(
            code='EC201', name='Signals & Systems', branch=self.branch_ece, department=self.dept_ece, semester=3, professor=self.prof_ece
        )
        CourseDeliveryRule.objects.create(course=self.course_ece, weekly_meetings=3, duration_slots=1)

        # Curriculum items
        self.ci_cse = CurriculumItem.objects.create(branch=self.branch_cse, semester_no=3, course=self.course_cse)
        self.ci_ece = CurriculumItem.objects.create(branch=self.branch_ece, semester_no=3, course=self.course_ece)

        # Course offerings
        self.off_cse = CourseOffering.objects.create(term=self.term, cohort=self.cohort_cse, curriculum_item=self.ci_cse)
        self.asgn_cse = TeachingAssignment.objects.create(
            course_offering=self.off_cse, professor=self.prof_cse, is_primary=True
        )

        self.off_ece = CourseOffering.objects.create(term=self.term, cohort=self.cohort_ece, curriculum_item=self.ci_ece)
        self.asgn_ece = TeachingAssignment.objects.create(
            course_offering=self.off_ece, professor=self.prof_ece, is_primary=True
        )

        # Schedule Version
        self.version = ScheduleVersion.objects.create(
            term=self.term, version_no=1, status=ScheduleVersion.Status.DRAFT, created_by=self.admin_user
        )

    def test_coordinator_can_view_own_branch_schedule(self):
        login = self.client.post('/api/auth/login', {'email': 'coord.cse@nitjsr.ac.in', 'password': 'CoordPassword123!'}, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        res = self.client.get(f'/api/branches/{self.branch_cse.id}/timetable/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['branch_id'], self.branch_cse.id)

    def test_coordinator_cannot_view_other_branch_schedule(self):
        login = self.client.post('/api/auth/login', {'email': 'coord.cse@nitjsr.ac.in', 'password': 'CoordPassword123!'}, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        res = self.client.get(f'/api/branches/{self.branch_ece.id}/timetable/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('assigned branch', res.data['detail'])

    def test_coordinator_can_create_meeting_for_own_branch(self):
        login = self.client.post('/api/auth/login', {'email': 'coord.cse@nitjsr.ac.in', 'password': 'CoordPassword123!'}, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        res = self.client.post('/api/timetable/meetings/', {
            'schedule_version_id': self.version.id,
            'teaching_assignment_id': self.asgn_cse.id,
            'weekday': 1,
            'start_slot': 1,
            'duration_slots': 1,
            'room_id': self.room.id,
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_coordinator_cannot_create_meeting_for_other_branch(self):
        login = self.client.post('/api/auth/login', {'email': 'coord.cse@nitjsr.ac.in', 'password': 'CoordPassword123!'}, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        res = self.client.post('/api/timetable/meetings/', {
            'schedule_version_id': self.version.id,
            'teaching_assignment_id': self.asgn_ece.id,
            'weekday': 1,
            'start_slot': 1,
            'duration_slots': 1,
            'room_id': self.room.id,
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_coordinator_cannot_delete_other_branch_meeting(self):
        # Admin creates ECE meeting
        ece_meeting = ScheduledMeeting.objects.create(
            schedule_version=self.version,
            teaching_assignment=self.asgn_ece,
            weekday=2,
            start_slot=2,
            duration_slots=1,
            room=self.room
        )

        login = self.client.post('/api/auth/login', {'email': 'coord.cse@nitjsr.ac.in', 'password': 'CoordPassword123!'}, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        res = self.client.delete(f'/api/timetable/meetings/{ece_meeting.id}/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_coordinator_courses_list_only_contains_own_branch_courses(self):
        login = self.client.post('/api/auth/login', {'email': 'coord.cse@nitjsr.ac.in', 'password': 'CoordPassword123!'}, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        res = self.client.get('/api/courses/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        course_codes = [c['code'] for c in res.data['results']]
        self.assertIn('CS201', course_codes)
        self.assertNotIn('EC201', course_codes)
