import pytest
from datetime import date, time
from rest_framework import status
from apps.accounts.models import User, Role, UserRoleAssignment
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
    ProfessorSlotReservation,
    RoomSlotReservation,
    GroupSlotReservation,
    ScheduleChangeAudit,
)


@pytest.mark.django_db
class TestClearTimetableAPI:
    def setup_method(self):
        # Roles
        self.admin_role = Role.objects.create(code=Role.Code.SUPER_ADMIN, name='Super Admin')
        self.coord_role = Role.objects.create(code=Role.Code.BRANCH_COORDINATOR, name='Branch Coordinator')
        self.prof_role = Role.objects.create(code=Role.Code.PROFESSOR, name='Professor')

        # Users
        self.admin = User.objects.create_user(
            email='admin@university.edu',
            password='AdminPassword123!',
            full_name='Admin User',
            is_staff=True,
            is_superuser=True
        )
        UserRoleAssignment.objects.create(user=self.admin, role=self.admin_role)

        self.coord = User.objects.create_user(
            email='coord@university.edu',
            password='CoordPassword123!',
            full_name='Branch Coordinator'
        )
        UserRoleAssignment.objects.create(user=self.coord, role=self.coord_role)

        self.prof = User.objects.create_user(
            email='prof@university.edu',
            password='ProfPassword123!',
            full_name='Prof Verma'
        )
        UserRoleAssignment.objects.create(user=self.prof, role=self.prof_role)

        # Structure
        self.dept_cse = Department.objects.create(code='CSE', name='Computer Science & Engineering')
        self.dept_ece = Department.objects.create(code='ECE', name='Electronics & Communication')

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

        # Term
        self.ay = AcademicYear.objects.create(name='2026-2027', start_date=date(2026, 7, 1), end_date=date(2027, 6, 30))
        self.term = AcademicTerm.objects.create(
            academic_year=self.ay,
            name='Odd Semester 2026',
            term_type='ODD',
            start_date=date(2026, 8, 1),
            end_date=date(2026, 12, 15)
        )

        # Cohorts
        # CSE Sem 3
        self.cohort_cse_s3 = Cohort.objects.create(
            branch=self.branch_cse,
            term=self.term,
            semester_no=3,
            section_code='A',
            student_count=60
        )
        self.group_cse_s3 = InstructionGroup.objects.create(
            cohort=self.cohort_cse_s3,
            name='Group 1',
            code='CSE3-G1',
            size=60
        )

        # CSE Sem 5
        self.cohort_cse_s5 = Cohort.objects.create(
            branch=self.branch_cse,
            term=self.term,
            semester_no=5,
            section_code='A',
            student_count=60
        )
        self.group_cse_s5 = InstructionGroup.objects.create(
            cohort=self.cohort_cse_s5,
            name='Group 1',
            code='CSE5-G1',
            size=60
        )

        # ECE Sem 3 (Different department)
        self.cohort_ece_s3 = Cohort.objects.create(
            branch=self.branch_ece,
            term=self.term,
            semester_no=3,
            section_code='A',
            student_count=60
        )

        # Facilities
        self.campus = Campus.objects.create(code='MAIN', name='Main Campus')
        self.building = Building.objects.create(campus=self.campus, code='ENGG', name='Engineering Block')
        self.room1 = Room.objects.create(
            building=self.building,
            room_no='101',
            name='Room 101',
            room_type='CLASSROOM',
            capacity=70,
            is_active=True
        )
        self.room2 = Room.objects.create(
            building=self.building,
            room_no='102',
            name='Room 102',
            room_type='CLASSROOM',
            capacity=70,
            is_active=True
        )

        # Courses
        self.course_cse3 = Course.objects.create(
            department=self.dept_cse,
            code='CS301',
            name='Data Structures',
            credit=3,
            course_type='THEORY'
        )
        self.course_cse5 = Course.objects.create(
            department=self.dept_cse,
            code='CS501',
            name='Operating Systems',
            credit=3,
            course_type='THEORY'
        )
        self.course_ece3 = Course.objects.create(
            department=self.dept_ece,
            code='EC301',
            name='Signals & Systems',
            credit=3,
            course_type='THEORY'
        )

        # Curriculums
        self.ci_cse3 = CurriculumItem.objects.create(
            branch=self.branch_cse,
            semester_no=3,
            course=self.course_cse3
        )
        self.ci_cse5 = CurriculumItem.objects.create(
            branch=self.branch_cse,
            semester_no=5,
            course=self.course_cse5
        )
        self.ci_ece3 = CurriculumItem.objects.create(
            branch=self.branch_ece,
            semester_no=3,
            course=self.course_ece3
        )

        # Course Offerings
        self.offering_cse3 = CourseOffering.objects.create(
            term=self.term,
            cohort=self.cohort_cse_s3,
            curriculum_item=self.ci_cse3
        )
        self.offering_cse5 = CourseOffering.objects.create(
            term=self.term,
            cohort=self.cohort_cse_s5,
            curriculum_item=self.ci_cse5
        )
        self.offering_ece3 = CourseOffering.objects.create(
            term=self.term,
            cohort=self.cohort_ece_s3,
            curriculum_item=self.ci_ece3
        )

        # Teaching Assignments
        self.asgn_cse3 = TeachingAssignment.objects.create(
            course_offering=self.offering_cse3,
            professor=self.prof,
            is_primary=True
        )
        self.asgn_cse5 = TeachingAssignment.objects.create(
            course_offering=self.offering_cse5,
            professor=self.prof,
            is_primary=True
        )
        self.asgn_ece3 = TeachingAssignment.objects.create(
            course_offering=self.offering_ece3,
            professor=self.prof,
            is_primary=True
        )

        # Schedule Version
        self.version = ScheduleVersion.objects.create(
            term=self.term,
            version_no=1,
            name='Draft Schedule 1',
            status=ScheduleVersion.Status.DRAFT
        )

    def test_clear_department_and_semester_meetings_success(self, api_client):
        # Create meetings in CSE Sem 3
        m1 = ScheduledMeeting.objects.create(
            schedule_version=self.version,
            teaching_assignment=self.asgn_cse3,
            weekday=1,
            start_slot=1,
            duration_slots=1,
            room=self.room1
        )
        m1.meeting_instruction_groups.create(instruction_group=self.group_cse_s3)
        ProfessorSlotReservation.objects.create(
            schedule_version=self.version,
            professor=self.prof,
            weekday=1,
            slot_no=1,
            scheduled_meeting=m1
        )
        RoomSlotReservation.objects.create(
            schedule_version=self.version,
            room=self.room1,
            weekday=1,
            slot_no=1,
            scheduled_meeting=m1
        )
        GroupSlotReservation.objects.create(
            schedule_version=self.version,
            instruction_group=self.group_cse_s3,
            weekday=1,
            slot_no=1,
            scheduled_meeting=m1
        )

        # Create meeting in CSE Sem 5 (different semester, same department)
        m2 = ScheduledMeeting.objects.create(
            schedule_version=self.version,
            teaching_assignment=self.asgn_cse5,
            weekday=2,
            start_slot=2,
            duration_slots=1,
            room=self.room1
        )

        # Create meeting in ECE Sem 3 (same semester, different department)
        m3 = ScheduledMeeting.objects.create(
            schedule_version=self.version,
            teaching_assignment=self.asgn_ece3,
            weekday=3,
            start_slot=3,
            duration_slots=1,
            room=self.room2
        )

        assert ScheduledMeeting.objects.filter(schedule_version=self.version).count() == 3

        # Clear CSE Sem 3
        api_client.force_authenticate(user=self.coord)
        res = api_client.post('/api/timetable/clear', {
            'schedule_version_id': self.version.id,
            'department_id': self.dept_cse.id,
            'semester_no': 3,
        }, format='json')

        assert res.status_code == status.HTTP_200_OK
        assert res.data['deleted_count'] == 1

        # Check CSE Sem 3 meeting and its reservations were deleted
        assert not ScheduledMeeting.objects.filter(id=m1.id).exists()
        assert not ProfessorSlotReservation.objects.filter(scheduled_meeting_id=m1.id).exists()
        assert not RoomSlotReservation.objects.filter(scheduled_meeting_id=m1.id).exists()
        assert not GroupSlotReservation.objects.filter(scheduled_meeting_id=m1.id).exists()

        # Check other meetings still exist
        assert ScheduledMeeting.objects.filter(id=m2.id).exists()
        assert ScheduledMeeting.objects.filter(id=m3.id).exists()
        assert ScheduledMeeting.objects.filter(schedule_version=self.version).count() == 2

        # Check audit log was recorded
        audit = ScheduleChangeAudit.objects.filter(
            schedule_version=self.version,
            action='CLEAR_TIMETABLE'
        ).first()
        assert audit is not None
        assert audit.before_json['deleted_count'] == 1
        assert audit.before_json['department_id'] == self.dept_cse.id
        assert audit.before_json['semester_no'] == 3

    def test_clear_when_no_meetings_exist(self, api_client):
        api_client.force_authenticate(user=self.coord)
        res = api_client.post('/api/timetable/clear', {
            'schedule_version_id': self.version.id,
            'department_id': self.dept_cse.id,
            'semester_no': 3,
        }, format='json')

        assert res.status_code == status.HTTP_200_OK
        assert res.data['deleted_count'] == 0

    def test_clear_published_schedule_forbidden(self, api_client):
        self.version.status = ScheduleVersion.Status.PUBLISHED
        self.version.save()

        api_client.force_authenticate(user=self.admin)
        res = api_client.post('/api/timetable/clear', {
            'schedule_version_id': self.version.id,
            'department_id': self.dept_cse.id,
            'semester_no': 3,
        }, format='json')

        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_clear_by_term_id(self, api_client):
        m1 = ScheduledMeeting.objects.create(
            schedule_version=self.version,
            teaching_assignment=self.asgn_cse3,
            weekday=1,
            start_slot=1,
            duration_slots=1,
            room=self.room1
        )
        api_client.force_authenticate(user=self.coord)
        res = api_client.post('/api/timetable/clear', {
            'term_id': self.term.id,
            'department_id': self.dept_cse.id,
            'semester_no': 3,
        }, format='json')

        assert res.status_code == status.HTTP_200_OK
        assert res.data['deleted_count'] == 1
        assert not ScheduledMeeting.objects.filter(id=m1.id).exists()

    def test_clear_by_cohort_id(self, api_client):
        m1 = ScheduledMeeting.objects.create(
            schedule_version=self.version,
            teaching_assignment=self.asgn_cse3,
            weekday=1,
            start_slot=1,
            duration_slots=1,
            room=self.room1
        )
        m2 = ScheduledMeeting.objects.create(
            schedule_version=self.version,
            teaching_assignment=self.asgn_cse5,
            weekday=2,
            start_slot=2,
            duration_slots=1,
            room=self.room1
        )
        api_client.force_authenticate(user=self.coord)
        res = api_client.post('/api/timetable/clear', {
            'schedule_version_id': self.version.id,
            'cohort_id': self.cohort_cse_s3.id,
        }, format='json')

        assert res.status_code == status.HTTP_200_OK
        assert res.data['deleted_count'] == 1
        assert not ScheduledMeeting.objects.filter(id=m1.id).exists()
        assert ScheduledMeeting.objects.filter(id=m2.id).exists()

    def test_clear_all_classes_in_schedule(self, api_client):
        m1 = ScheduledMeeting.objects.create(
            schedule_version=self.version,
            teaching_assignment=self.asgn_cse3,
            weekday=1,
            start_slot=1,
            duration_slots=1,
            room=self.room1
        )
        m2 = ScheduledMeeting.objects.create(
            schedule_version=self.version,
            teaching_assignment=self.asgn_cse5,
            weekday=2,
            start_slot=2,
            duration_slots=1,
            room=self.room1
        )
        m3 = ScheduledMeeting.objects.create(
            schedule_version=self.version,
            teaching_assignment=self.asgn_ece3,
            weekday=3,
            start_slot=3,
            duration_slots=1,
            room=self.room2
        )
        api_client.force_authenticate(user=self.coord)
        res = api_client.post('/api/timetable/clear', {
            'schedule_version_id': self.version.id,
            'clear_all': True,
        }, format='json')

        assert res.status_code == status.HTTP_200_OK
        assert res.data['deleted_count'] == 3
        assert ScheduledMeeting.objects.filter(schedule_version=self.version).count() == 0

