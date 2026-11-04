import io
from datetime import date, time
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
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

class Phase2AcademicDataTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Seed roles
        self.admin_role = Role.objects.create(code=Role.Code.SUPER_ADMIN, name='Super Admin')
        self.prof_role = Role.objects.create(code=Role.Code.PROFESSOR, name='Professor')

        # Admin user
        self.admin = User.objects.create_user(
            email='admin@university.edu',
            password='AdminPassword123!',
            full_name='Admin User',
            is_staff=True,
            is_superuser=True
        )
        UserRoleAssignment.objects.create(user=self.admin, role=self.admin_role)

        # Department & Branch (max_semesters = 8)
        self.dept = Department.objects.create(code='CSE', name='Computer Science & Engineering')
        self.branch = Branch.objects.create(
            department=self.dept,
            code='BTECH_CSE',
            name='B.Tech Computer Science',
            degree_name='B.Tech',
            max_semesters=8
        )

        # Professor user
        self.prof = User.objects.create_user(
            email='prof.sharma@university.edu',
            password='ProfPassword123!',
            full_name='Dr. Sharma',
            employee_code='PRF101'
        )
        UserRoleAssignment.objects.create(user=self.prof, role=self.prof_role)
        self.prof_profile = ProfessorProfile.objects.create(
            user=self.prof,
            department=self.dept,
            designation='Associate Professor',
            max_hours_per_day=6
        )

        # Authenticate admin by default
        login_res = self.client.post('/api/auth/login', {
            'email': 'admin@university.edu',
            'password': 'AdminPassword123!'
        }, format='json')
        self.token = login_res.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_checklist_1_create_campus_building_room(self):
        """Checklist #1: Create campus -> building -> room via API"""
        # Campus
        res_camp = self.client.post('/api/campuses/', {
            'code': 'NORTH',
            'name': 'North Campus',
            'address': 'North Ring Road'
        }, format='json')
        self.assertEqual(res_camp.status_code, status.HTTP_201_CREATED)
        campus_id = res_camp.data['id']

        # Building
        res_bld = self.client.post('/api/buildings/', {
            'campus': campus_id,
            'code': 'TECH_1',
            'name': 'Technology Tower 1',
            'floors_count': 5
        }, format='json')
        self.assertEqual(res_bld.status_code, status.HTTP_201_CREATED)
        bld_id = res_bld.data['id']

        # Room
        res_rm = self.client.post('/api/rooms/', {
            'building': bld_id,
            'room_no': 'TT101',
            'name': 'Computer Lab 1',
            'room_type': 'COMPUTER_LAB',
            'capacity': 45,
            'floor': 1
        }, format='json')
        self.assertEqual(res_rm.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_rm.data['room_type'], 'COMPUTER_LAB')
        self.assertEqual(res_rm.data['capacity'], 45)

    def test_checklist_2_create_academic_year_and_term(self):
        """Checklist #2: Create AcademicYear and AcademicTerm"""
        res_yr = self.client.post('/api/academic-years/', {
            'name': '2026-27',
            'start_date': '2026-08-01',
            'end_date': '2027-06-30',
            'is_current': True
        }, format='json')
        self.assertEqual(res_yr.status_code, status.HTTP_201_CREATED)
        year_id = res_yr.data['id']

        res_term = self.client.post('/api/academic-terms/', {
            'academic_year': year_id,
            'name': 'Odd Semester 2026-27',
            'term_type': 'ODD',
            'start_date': '2026-08-10',
            'end_date': '2026-12-20'
        }, format='json')
        self.assertEqual(res_term.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_term.data['name'], 'Odd Semester 2026-27')

    def test_checklist_3_seed_time_slots(self):
        """Checklist #3: Seed 8 time slots via management command"""
        from django.core.management import call_command
        call_command('seed_phase2_data')
        self.assertEqual(TimeSlot.objects.count(), 8)
        self.assertTrue(TimeSlot.objects.filter(slot_no=1).exists())
        self.assertTrue(TimeSlot.objects.filter(slot_no=8).exists())

    def test_checklist_4_cohort_invalid_semester_rejected(self):
        """Checklist #4: Create cohort with semester_no > max_semesters -> 400 Bad Request"""
        term = AcademicTerm.objects.create(
            academic_year=AcademicYear.objects.create(
                name='2026-27',
                start_date=date(2026, 8, 1),
                end_date=date(2027, 6, 30)
            ),
            name='Odd Term',
            start_date=date(2026, 8, 1),
            end_date=date(2026, 12, 1)
        )
        # Branch max_semesters is 8. Trying semester 9.
        res = self.client.post('/api/cohorts/', {
            'branch': self.branch.id,
            'term': term.id,
            'semester_no': 9,
            'section_code': 'A',
            'student_count': 60
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('semester_no', res.data)

    def test_checklist_5_cohort_valid_semester(self):
        """Checklist #5: Create cohort with valid semester_no -> 201 Created"""
        term = AcademicTerm.objects.create(
            academic_year=AcademicYear.objects.create(
                name='2026-27',
                start_date=date(2026, 8, 1),
                end_date=date(2027, 6, 30)
            ),
            name='Odd Term',
            start_date=date(2026, 8, 1),
            end_date=date(2026, 12, 1)
        )
        res = self.client.post('/api/cohorts/', {
            'branch': self.branch.id,
            'term': term.id,
            'semester_no': 3,
            'section_code': 'A',
            'student_count': 60
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['semester_no'], 3)
        self.assertEqual(res.data['section_code'], 'A')

    def test_checklist_6_course_with_lab_delivery_rule(self):
        """Checklist #6: Add course with course_type=LAB, assign delivery rule (2x3)"""
        res = self.client.post('/api/courses/', {
            'code': 'CS303L',
            'name': 'Database Systems Lab',
            'credit': 2,
            'course_type': 'LAB',
            'department': self.dept.id,
            'delivery_rule': {
                'weekly_meetings': 2,
                'duration_slots': 3,
                'preferred_room_type': 'COMPUTER_LAB'
            }
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['delivery_rule']['weekly_meetings'], 2)
        self.assertEqual(res.data['delivery_rule']['duration_slots'], 3)
        self.assertEqual(res.data['delivery_rule']['total_contact_hours'], 6)

    def test_checklist_7_add_curriculum_item(self):
        """Checklist #7: Add curriculum item to branch/semester"""
        course = Course.objects.create(
            code='CS301',
            name='DBMS',
            credit=3,
            course_type='THEORY'
        )
        res = self.client.post('/api/curriculum/', {
            'branch': self.branch.id,
            'semester_no': 3,
            'course': course.id,
            'is_elective': False
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['course_code'], 'CS301')

    def test_checklist_8_course_offering_and_teaching_assignment(self):
        """Checklist #8: Create a course offering and assign a professor"""
        term = AcademicTerm.objects.create(
            academic_year=AcademicYear.objects.create(
                name='2026-27',
                start_date=date(2026, 8, 1),
                end_date=date(2027, 6, 30)
            ),
            name='Odd Term',
            start_date=date(2026, 8, 1),
            end_date=date(2026, 12, 1)
        )
        cohort = Cohort.objects.create(
            branch=self.branch,
            term=term,
            semester_no=3,
            section_code='A',
            student_count=60
        )
        course = Course.objects.create(code='CS301', name='DBMS', credit=3)
        curriculum_item = CurriculumItem.objects.create(
            branch=self.branch,
            semester_no=3,
            course=course
        )

        res_offering = self.client.post('/api/course-offerings/', {
            'term': term.id,
            'cohort': cohort.id,
            'curriculum_item': curriculum_item.id
        }, format='json')
        self.assertEqual(res_offering.status_code, status.HTTP_201_CREATED)
        offering_id = res_offering.data['id']

        res_assignment = self.client.post('/api/teaching-assignments/', {
            'course_offering': offering_id,
            'professor': self.prof.id,
            'is_primary': True
        }, format='json')
        self.assertEqual(res_assignment.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_assignment.data['professor_name'], 'Dr. Sharma')

    def test_checklist_9_upload_valid_professors_csv(self):
        """Checklist #9: Upload a valid professor CSV -> 200 OK & created"""
        csv_content = (
            "email,full_name,employee_code,department_code,designation,max_hours_per_day\n"
            "dr.alan.turing@university.edu,Dr. Alan Turing,EMP009,CSE,Professor,6\n"
            "dr.grace.hopper@university.edu,Dr. Grace Hopper,EMP010,CSE,Associate Professor,5\n"
        )
        csv_file = SimpleUploadedFile("professors.csv", csv_content.encode('utf-8'), content_type="text/csv")
        res = self.client.post('/api/professors/import', {'file': csv_file}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])
        self.assertEqual(res.data['imported_count'], 2)
        self.assertTrue(User.objects.filter(email='dr.alan.turing@university.edu').exists())

    def test_checklist_10_upload_invalid_csv_rejected(self):
        """Checklist #10: Upload a CSV with a bad row -> reports error per row, nothing saved"""
        initial_user_count = User.objects.count()
        csv_content = (
            "email,full_name,employee_code,department_code,designation,max_hours_per_day\n"
            "dr.good@university.edu,Dr. Good,EMP011,CSE,Professor,6\n"
            "invalid-email-address,Dr. Bad,EMP012,INVALID_DEPT,Professor,6\n"
        )
        csv_file = SimpleUploadedFile("professors_bad.csv", csv_content.encode('utf-8'), content_type="text/csv")
        res = self.client.post('/api/professors/import', {'file': csv_file}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data['success'])
        self.assertGreater(len(res.data['errors']), 0)
        # Transaction rolled back: dr.good should NOT be saved
        self.assertEqual(User.objects.count(), initial_user_count)

    def test_professor_unavailability_endpoint(self):
        """Test professor unavailability get and post"""
        res = self.client.post(f'/api/professors/{self.prof.id}/unavailability/', {
            'weekday': 2,
            'start_slot': 1,
            'end_slot': 2,
            'reason': 'Academic Council Meeting'
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['weekday'], 2)

        res_get = self.client.get(f'/api/professors/{self.prof.id}/unavailability/')
        self.assertEqual(res_get.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_get.data), 1)
