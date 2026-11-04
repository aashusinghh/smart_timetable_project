from datetime import time, date
from django.core.management.base import BaseCommand
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

class Command(BaseCommand):
    help = 'Seeds Phase 2 academic structure: time slots, campuses, rooms, terms, curriculum, cohorts, and teaching assignments'

    def handle(self, *args, **options):
        self.stdout.write("Seeding Phase 2 data...")

        # 1. Daily 8 Time Slots per Architecture Spec §6
        slots_data = [
            (1, time(8, 30), time(9, 30), TimeSlot.Session.MORNING),
            (2, time(9, 30), time(10, 30), TimeSlot.Session.MORNING),
            (3, time(10, 30), time(11, 30), TimeSlot.Session.MORNING),
            (4, time(11, 30), time(12, 30), TimeSlot.Session.MORNING),
            (5, time(14, 0), time(15, 0), TimeSlot.Session.AFTERNOON),
            (6, time(15, 0), time(16, 0), TimeSlot.Session.AFTERNOON),
            (7, time(16, 0), time(17, 0), TimeSlot.Session.AFTERNOON),
            (8, time(17, 0), time(18, 0), TimeSlot.Session.AFTERNOON),
        ]
        for slot_no, start_t, end_t, sess in slots_data:
            TimeSlot.objects.update_or_create(
                slot_no=slot_no,
                defaults={
                    'start_time': start_t,
                    'end_time': end_t,
                    'session': sess,
                    'is_active': True,
                }
            )
        self.stdout.write(self.style.SUCCESS("  [OK] Seeded 8 daily Time Slots"))

        # 2. Campus & Buildings
        main_campus, _ = Campus.objects.get_or_create(
            code='MAIN',
            defaults={'name': 'University Main Campus', 'address': '124 University Ave, Knowledge Park'}
        )

        eng_block, _ = Building.objects.get_or_create(
            campus=main_campus,
            code='ENG_A',
            defaults={'name': 'Engineering Block A', 'floors_count': 4}
        )

        cs_block, _ = Building.objects.get_or_create(
            campus=main_campus,
            code='CS_BLK',
            defaults={'name': 'Computer Science Complex', 'floors_count': 5}
        )

        # 3. Rooms across all room types
        rooms_data = [
            (eng_block, '101', 'Lecture Hall 101', Room.RoomType.CLASSROOM, 70, 1),
            (eng_block, '102', 'Lecture Hall 102', Room.RoomType.CLASSROOM, 70, 1),
            (eng_block, '201', 'Electronics Lab 1', Room.RoomType.ELECTRONICS_LAB, 36, 2),
            (eng_block, '301', 'Applied Chemistry Lab', Room.RoomType.CHEMISTRY_LAB, 36, 3),
            (eng_block, 'AUD', 'Main Auditorium', Room.RoomType.SEMINAR_HALL, 200, 1),
            (cs_block, 'CL1', 'Software Lab Alpha', Room.RoomType.COMPUTER_LAB, 40, 1),
            (cs_block, 'CL2', 'Systems Lab Beta', Room.RoomType.COMPUTER_LAB, 40, 1),
            (cs_block, '201', 'Smart Classroom 201', Room.RoomType.CLASSROOM, 65, 2),
            (cs_block, '202', 'Smart Classroom 202', Room.RoomType.CLASSROOM, 65, 2),
        ]
        for bld, r_no, r_name, r_type, cap, fl in rooms_data:
            Room.objects.update_or_create(
                building=bld,
                room_no=r_no,
                defaults={
                    'name': r_name,
                    'room_type': r_type,
                    'capacity': cap,
                    'floor': fl,
                    'is_active': True,
                }
            )
        self.stdout.write(self.style.SUCCESS("  [OK] Seeded Campus, Buildings & Rooms"))

        # 4. Academic Year & Term
        curr_year, _ = AcademicYear.objects.get_or_create(
            name='2026-27',
            defaults={
                'start_date': date(2026, 8, 1),
                'end_date': date(2027, 6, 30),
                'is_current': True,
                'is_active': True,
            }
        )
        odd_term, _ = AcademicTerm.objects.get_or_create(
            academic_year=curr_year,
            name='Odd Semester 2026-27',
            defaults={
                'term_type': AcademicTerm.TermType.ODD,
                'start_date': date(2026, 8, 10),
                'end_date': date(2026, 12, 22),
                'is_active': True,
            }
        )
        even_term, _ = AcademicTerm.objects.get_or_create(
            academic_year=curr_year,
            name='Even Semester 2026-27',
            defaults={
                'term_type': AcademicTerm.TermType.EVEN,
                'start_date': date(2027, 1, 10),
                'end_date': date(2027, 5, 25),
                'is_active': True,
            }
        )
        self.stdout.write(self.style.SUCCESS("  [OK] Seeded Academic Year & Terms"))

        # 5. Courses & Required Delivery Rules (§5.3)
        cse_dept = Department.objects.filter(code='CSE').first()
        courses_data = [
            # code, name, credit, course_type, weekly_meetings, duration_slots, room_type
            ('CS301', 'Database Management Systems', 3, Course.CourseType.THEORY, 3, 1, 'CLASSROOM'),
            ('CS302', 'Operating Systems', 4, Course.CourseType.THEORY, 4, 1, 'CLASSROOM'),
            ('CS303', 'Database Management Lab', 2, Course.CourseType.LAB, 2, 3, 'COMPUTER_LAB'),
            ('CS304', 'Computer Networks', 3, Course.CourseType.THEORY, 3, 1, 'CLASSROOM'),
            ('CS305', 'Computer Networks Lab', 2, Course.CourseType.LAB, 2, 3, 'COMPUTER_LAB'),
            ('CS306', 'Technical Seminar', 1, Course.CourseType.SEMINAR, 1, 1, 'SEMINAR_HALL'),
        ]
        created_courses = {}
        for c_code, c_name, cr, c_type, w_meet, dur, pref_room in courses_data:
            course, _ = Course.objects.update_or_create(
                code=c_code,
                defaults={
                    'name': c_name,
                    'credit': cr,
                    'course_type': c_type,
                    'department': cse_dept,
                    'is_active': True,
                }
            )
            CourseDeliveryRule.objects.update_or_create(
                course=course,
                defaults={
                    'weekly_meetings': w_meet,
                    'duration_slots': dur,
                    'preferred_room_type': pref_room,
                }
            )
            created_courses[c_code] = course
        self.stdout.write(self.style.SUCCESS("  [OK] Seeded Courses & Delivery Rules (2x3 lab, 3x1 & 4x1 theory)"))

        # 6. Curriculum Items for Branch BTECH_CSE
        btech_cse = Branch.objects.filter(code='BTECH_CSE').first()
        if btech_cse:
            # Sem 3 curriculum: CS301, CS302, CS303
            curriculum_sem3 = []
            for code in ['CS301', 'CS302', 'CS303']:
                item, _ = CurriculumItem.objects.update_or_create(
                    branch=btech_cse,
                    semester_no=3,
                    course=created_courses[code],
                    defaults={'is_elective': False, 'is_active': True}
                )
                curriculum_sem3.append(item)

            # Sem 5 curriculum: CS304, CS305, CS306
            curriculum_sem5 = []
            for code in ['CS304', 'CS305', 'CS306']:
                item, _ = CurriculumItem.objects.update_or_create(
                    branch=btech_cse,
                    semester_no=5,
                    course=created_courses[code],
                    defaults={'is_elective': False, 'is_active': True}
                )
                curriculum_sem5.append(item)

            self.stdout.write(self.style.SUCCESS("  [OK] Seeded Curriculum Items for B.Tech CSE (Sem 3 & Sem 5)"))

            # 7. Cohorts & Instruction Groups
            cohort_sem3, _ = Cohort.objects.update_or_create(
                branch=btech_cse,
                term=odd_term,
                semester_no=3,
                section_code='A',
                defaults={'student_count': 60, 'is_active': True}
            )
            InstructionGroup.objects.update_or_create(cohort=cohort_sem3, code='3A-L1', defaults={'name': 'Lab Batch 1', 'size': 30})
            InstructionGroup.objects.update_or_create(cohort=cohort_sem3, code='3A-L2', defaults={'name': 'Lab Batch 2', 'size': 30})
            InstructionGroup.objects.update_or_create(cohort=cohort_sem3, code='ALL', defaults={'name': 'Whole Class', 'size': 60})

            cohort_sem5, _ = Cohort.objects.update_or_create(
                branch=btech_cse,
                term=odd_term,
                semester_no=5,
                section_code='A',
                defaults={'student_count': 60, 'is_active': True}
            )
            InstructionGroup.objects.update_or_create(cohort=cohort_sem5, code='5A-L1', defaults={'name': 'Lab Batch 1', 'size': 30})
            InstructionGroup.objects.update_or_create(cohort=cohort_sem5, code='5A-L2', defaults={'name': 'Lab Batch 2', 'size': 30})
            InstructionGroup.objects.update_or_create(cohort=cohort_sem5, code='ALL', defaults={'name': 'Whole Class', 'size': 60})
            self.stdout.write(self.style.SUCCESS("  [OK] Seeded Cohorts & Lab Groups (3A-L1, 3A-L2, etc.)"))

            # 8. Course Offerings for Sem 3
            prof_user = User.objects.filter(role_assignments__role__code='PROFESSOR').first()
            if not prof_user:
                prof_user = User.objects.create_user(
                    email='prof.sharma@university.edu',
                    password='ProfPassword123!',
                    full_name='Dr. Rajesh Sharma',
                    employee_code='PRF001'
                )
                prof_role, _ = Role.objects.get_or_create(code=Role.Code.PROFESSOR)
                UserRoleAssignment.objects.create(user=prof_user, role=prof_role)
                ProfessorProfile.objects.create(user=prof_user, department=cse_dept, designation='Professor', max_hours_per_day=6)

            for item in curriculum_sem3:
                offering, _ = CourseOffering.objects.update_or_create(
                    term=odd_term,
                    cohort=cohort_sem3,
                    curriculum_item=item,
                    defaults={'is_active': True}
                )
                # Assign professor
                if item.course.course_type == Course.CourseType.LAB:
                    g1 = InstructionGroup.objects.get(cohort=cohort_sem3, code='3A-L1')
                    TeachingAssignment.objects.update_or_create(
                        course_offering=offering,
                        professor=prof_user,
                        instruction_group=g1,
                        defaults={'is_primary': True, 'is_active': True}
                    )
                else:
                    TeachingAssignment.objects.update_or_create(
                        course_offering=offering,
                        professor=prof_user,
                        instruction_group=None,
                        defaults={'is_primary': True, 'is_active': True}
                    )
            self.stdout.write(self.style.SUCCESS("  [OK] Seeded Course Offerings & Fixed Teaching Assignments"))

        self.stdout.write(self.style.SUCCESS("Phase 2 Academic Data setup completed successfully!"))
