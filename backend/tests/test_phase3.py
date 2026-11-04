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
    TimeSlot,
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

class Phase3TimetablePlannerTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Roles
        self.admin_role = Role.objects.create(code=Role.Code.SUPER_ADMIN, name='Super Admin')
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

        # Faculty
        self.prof = User.objects.create_user(
            email='prof.sharma@university.edu',
            password='ProfPassword123!',
            full_name='Dr. Sharma'
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

        # Cohort & Lab Group
        self.cohort = Cohort.objects.create(
            branch=self.branch,
            term=self.term,
            semester_no=3,
            section_code='A',
            student_count=60
        )
        self.group_l1 = InstructionGroup.objects.create(cohort=self.cohort, code='3A-L1', size=30)
        self.group_l2 = InstructionGroup.objects.create(cohort=self.cohort, code='3A-L2', size=30)

        # Theory Course (3-credit, 3x1hr)
        self.theory_course = Course.objects.create(code='CS301', name='DBMS', credit=3, course_type=Course.CourseType.THEORY)
        CourseDeliveryRule.objects.create(course=self.theory_course, weekly_meetings=3, duration_slots=1, preferred_room_type='CLASSROOM')
        self.theory_curr = CurriculumItem.objects.create(branch=self.branch, semester_no=3, course=self.theory_course)
        self.theory_offering = CourseOffering.objects.create(term=self.term, cohort=self.cohort, curriculum_item=self.theory_curr)
        self.theory_asgn = TeachingAssignment.objects.create(course_offering=self.theory_offering, professor=self.prof, instruction_group=None)

        # Lab Course (2-credit, 2x3hr)
        self.lab_course = Course.objects.create(code='CS302L', name='DBMS Lab', credit=2, course_type=Course.CourseType.LAB)
        CourseDeliveryRule.objects.create(course=self.lab_course, weekly_meetings=2, duration_slots=3, preferred_room_type='COMPUTER_LAB')
        self.lab_curr = CurriculumItem.objects.create(branch=self.branch, semester_no=3, course=self.lab_course)
        self.lab_offering = CourseOffering.objects.create(term=self.term, cohort=self.cohort, curriculum_item=self.lab_curr)
        self.lab_asgn = TeachingAssignment.objects.create(course_offering=self.lab_offering, professor=self.prof, instruction_group=self.group_l1)

        # Schedule Version (Draft)
        self.version = ScheduleVersion.objects.create(term=self.term, version_no=1, status=ScheduleVersion.Status.DRAFT, name='Draft 1')

        # Login
        login_res = self.client.post('/api/auth/login', {'email': 'admin@university.edu', 'password': 'AdminPassword123!'}, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_res.data['access']}")

    def test_checklist_1_validate_free_slot(self):
        """Checklist #1: POST /api/timetable/validate for a free slot -> allowed: true"""
        res = self.client.post('/api/timetable/validate', {
            'schedule_version_id': self.version.id,
            'teaching_assignment_id': self.theory_asgn.id,
            'weekday': 1, # Monday
            'start_slot': 1, # 08:30 - 09:30
            'duration_slots': 1,
            'room_id': self.classroom.id,
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['allowed'])
        self.assertEqual(len(res.data['conflicts']), 0)

    def test_checklist_2_validate_professor_busy_conflict(self):
        """Checklist #2: Validate a slot where professor is already booked -> allowed: false, PROFESSOR_BUSY"""
        # Save a meeting first on Monday Slot 1
        self.client.post('/api/timetable/meetings/', {
            'schedule_version_id': self.version.id,
            'teaching_assignment_id': self.theory_asgn.id,
            'weekday': 1,
            'start_slot': 1,
            'duration_slots': 1,
            'room_id': self.classroom.id,
        }, format='json')

        # Now validate a second placement for same professor on Monday Slot 1 (in a different room)
        res = self.client.post('/api/timetable/validate', {
            'schedule_version_id': self.version.id,
            'teaching_assignment_id': self.theory_asgn.id,
            'weekday': 1,
            'start_slot': 1,
            'duration_slots': 1,
            'room_id': self.lab_room.id,
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.data['allowed'])
        types = [c['type'] for c in res.data['conflicts']]
        self.assertIn('PROFESSOR_BUSY', types)

    def test_checklist_3_validate_lunch_crossing_rejected(self):
        """Checklist #3: Validate a slot that crosses lunch (e.g. start slot 4, duration 2 -> crosses into slot 5) -> allowed: false, LUNCH_CROSSING"""
        res = self.client.post('/api/timetable/validate', {
            'schedule_version_id': self.version.id,
            'teaching_assignment_id': self.theory_asgn.id,
            'weekday': 1,
            'start_slot': 4, # 11:30 - 12:30
            'duration_slots': 2, # would cross into slot 5 (14:00)
            'room_id': self.classroom.id,
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.data['allowed'])
        types = [c['type'] for c in res.data['conflicts']]
        self.assertIn('LUNCH_CROSSING', types)

    def test_checklist_4_save_meeting_atomic_reservations(self):
        """Checklist #4: Save a meeting to a free slot -> 201 Created & reservation rows inserted"""
        res = self.client.post('/api/timetable/meetings/', {
            'schedule_version_id': self.version.id,
            'teaching_assignment_id': self.theory_asgn.id,
            'weekday': 2, # Tuesday
            'start_slot': 2,
            'duration_slots': 1,
            'room_id': self.classroom.id,
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        meeting_id = res.data['id']

        # Verify atomic reservation rows
        self.assertTrue(ProfessorSlotReservation.objects.filter(scheduled_meeting_id=meeting_id, slot_no=2, weekday=2).exists())
        self.assertTrue(RoomSlotReservation.objects.filter(scheduled_meeting_id=meeting_id, slot_no=2, weekday=2).exists())
        self.assertTrue(GroupSlotReservation.objects.filter(scheduled_meeting_id=meeting_id, slot_no=2, weekday=2).exists())

    def test_checklist_5_save_conflict_returns_409(self):
        """Checklist #5: Save a second meeting for same professor + slot -> 409 Conflict"""
        # First save
        self.client.post('/api/timetable/meetings/', {
            'schedule_version_id': self.version.id,
            'teaching_assignment_id': self.theory_asgn.id,
            'weekday': 3,
            'start_slot': 1,
            'duration_slots': 1,
            'room_id': self.classroom.id,
        }, format='json')

        # Second save attempt for same prof and same slot
        res2 = self.client.post('/api/timetable/meetings/', {
            'schedule_version_id': self.version.id,
            'teaching_assignment_id': self.theory_asgn.id,
            'weekday': 3,
            'start_slot': 1,
            'duration_slots': 1,
            'room_id': self.lab_room.id,
        }, format='json')
        self.assertEqual(res2.status_code, status.HTTP_409_CONFLICT)

    def test_checklist_6_edit_meeting_room(self):
        """Checklist #6: Edit a meeting's room -> old room reservation removed, new one created"""
        save_res = self.client.post('/api/timetable/meetings/', {
            'schedule_version_id': self.version.id,
            'teaching_assignment_id': self.theory_asgn.id,
            'weekday': 4,
            'start_slot': 2,
            'duration_slots': 1,
            'room_id': self.classroom.id,
        }, format='json')
        meeting_id = save_res.data['id']

        # Create another classroom
        room2 = Room.objects.create(building=self.building, room_no='102', room_type=Room.RoomType.CLASSROOM, capacity=60)

        # Patch room
        patch_res = self.client.patch(f'/api/timetable/meetings/{meeting_id}/', {
            'room_id': room2.id,
        }, format='json')
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)

        # Verify old room reservation deleted, new one exists
        self.assertFalse(RoomSlotReservation.objects.filter(room=self.classroom, scheduled_meeting_id=meeting_id).exists())
        self.assertTrue(RoomSlotReservation.objects.filter(room=room2, scheduled_meeting_id=meeting_id).exists())

    def test_checklist_7_delete_meeting(self):
        """Checklist #7: Delete a meeting -> reservation rows removed from DB"""
        save_res = self.client.post('/api/timetable/meetings/', {
            'schedule_version_id': self.version.id,
            'teaching_assignment_id': self.theory_asgn.id,
            'weekday': 5,
            'start_slot': 1,
            'duration_slots': 1,
            'room_id': self.classroom.id,
        }, format='json')
        meeting_id = save_res.data['id']

        del_res = self.client.delete(f'/api/timetable/meetings/{meeting_id}/')
        self.assertEqual(del_res.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(ProfessorSlotReservation.objects.filter(scheduled_meeting_id=meeting_id).exists())
        self.assertFalse(RoomSlotReservation.objects.filter(scheduled_meeting_id=meeting_id).exists())

    def test_checklist_8_save_3_hour_lab_creates_3_reservations(self):
        """Checklist #8: Save a 3-hour lab -> 3 reservation rows created per table"""
        res = self.client.post('/api/timetable/meetings/', {
            'schedule_version_id': self.version.id,
            'teaching_assignment_id': self.lab_asgn.id,
            'weekday': 1, # Monday
            'start_slot': 1, # 08:30 - 11:30 (slots 1, 2, 3)
            'duration_slots': 3,
            'room_id': self.lab_room.id,
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        meeting_id = res.data['id']

        self.assertEqual(ProfessorSlotReservation.objects.filter(scheduled_meeting_id=meeting_id).count(), 3)
        self.assertEqual(RoomSlotReservation.objects.filter(scheduled_meeting_id=meeting_id).count(), 3)
        self.assertEqual(GroupSlotReservation.objects.filter(scheduled_meeting_id=meeting_id).count(), 3)

    def test_checklist_9_grid_endpoint(self):
        """Checklist #9: GET /api/timetable/{version_id}/grid returns meetings"""
        self.client.post('/api/timetable/meetings/', {
            'schedule_version_id': self.version.id,
            'teaching_assignment_id': self.theory_asgn.id,
            'weekday': 1,
            'start_slot': 1,
            'duration_slots': 1,
            'room_id': self.classroom.id,
        }, format='json')

        res = self.client.get(f'/api/timetable/{self.version.id}/grid?cohort_id={self.cohort.id}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['meetings']), 1)

    def test_checklist_10_audit_logging(self):
        """Checklist #10: ScheduleChangeAudit record created on every save"""
        res = self.client.post('/api/timetable/meetings/', {
            'schedule_version_id': self.version.id,
            'teaching_assignment_id': self.theory_asgn.id,
            'weekday': 1,
            'start_slot': 1,
            'duration_slots': 1,
            'room_id': self.classroom.id,
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        meeting_id = res.data['id']

        audit = ScheduleChangeAudit.objects.filter(schedule_version=self.version, meeting_id=meeting_id).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.action, 'CREATE')
