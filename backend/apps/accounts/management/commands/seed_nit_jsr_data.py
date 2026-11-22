import logging
from datetime import time, date
from django.core.management.base import BaseCommand
from django.db import transaction

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
    MeetingInstructionGroup,
    ProfessorSlotReservation,
    RoomSlotReservation,
    GroupSlotReservation,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Seeds complete, comprehensive NIT Jamshedpur academic catalog, faculty, subjects for all semesters and branches'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("=== Starting Complete NIT JSR Catalog & Data Seeding ==="))

        # -------------------------------------------------------------------------
        # 1. ROLES
        # -------------------------------------------------------------------------
        admin_role, _ = Role.objects.get_or_create(
            code=Role.Code.SUPER_ADMIN,
            defaults={'name': 'Super Administrator', 'description': 'Full university system access'}
        )
        coord_role, _ = Role.objects.get_or_create(
            code=Role.Code.BRANCH_COORDINATOR,
            defaults={'name': 'Branch Coordinator', 'description': 'Coordinates branch timetable and allocations'}
        )
        prof_role, _ = Role.objects.get_or_create(
            code=Role.Code.PROFESSOR,
            defaults={'name': 'Professor', 'description': 'Faculty member and instructor'}
        )
        self.stdout.write(self.style.SUCCESS("[OK] Roles verified"))

        # -------------------------------------------------------------------------
        # 2. TIME SLOTS (8 daily slots, standard university schedule)
        # -------------------------------------------------------------------------
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
        self.stdout.write(self.style.SUCCESS("[OK] 8 daily Time Slots verified"))

        # -------------------------------------------------------------------------
        # 3. CAMPUS, BUILDINGS & ROOMS
        # -------------------------------------------------------------------------
        campus, _ = Campus.objects.update_or_create(
            code='NIT_JSR',
            defaults={
                'name': 'NIT Jamshedpur Main Campus',
                'address': 'Adityapur, Jamshedpur, Jharkhand 831014, India',
                'is_active': True,
            }
        )

        buildings_data = [
            ('DJLHC', 'Diamond Jubilee Lecture Hall Complex', 4),
            ('CC_BLK', 'Computer Centre & IT Services Block', 3),
            ('CSE_DEPT', 'Department of Computer Science & Engineering', 3),
            ('ECE_DEPT', 'Department of Electronics & Communication Engineering', 3),
            ('ELEC_BLK', 'Department of Electrical Engineering', 3),
            ('MECH_BLK', 'Mechanical Engineering Complex', 3),
            ('CIVIL_BLK', 'Civil Engineering Department Block', 3),
            ('CENTRAL_AUD', 'Central Auditorium & Convention Centre', 2),
        ]
        bld_map = {}
        for code, name, floors in buildings_data:
            bld, _ = Building.objects.update_or_create(
                campus=campus,
                code=code,
                defaults={'name': name, 'floors_count': floors, 'is_active': True}
            )
            bld_map[code] = bld

        rooms_data = [
            ('DJLHC', 'LH-101', 'Lecture Hall 101', Room.RoomType.CLASSROOM, 75, 1, True),
            ('DJLHC', 'LH-102', 'Lecture Hall 102', Room.RoomType.CLASSROOM, 75, 1, True),
            ('DJLHC', 'LH-201', 'Lecture Hall 201', Room.RoomType.CLASSROOM, 75, 2, True),
            ('DJLHC', 'LH-202', 'Lecture Hall 202', Room.RoomType.CLASSROOM, 75, 2, True),
            ('DJLHC', 'LH-301', 'Lecture Hall 301', Room.RoomType.CLASSROOM, 65, 3, True),
            ('DJLHC', 'LH-302', 'Lecture Hall 302', Room.RoomType.CLASSROOM, 65, 3, True),
            ('CC_BLK', 'CC-LAB-1', 'Programming Lab 1', Room.RoomType.COMPUTER_LAB, 45, 1, True),
            ('CC_BLK', 'CC-LAB-2', 'Computing Lab 2', Room.RoomType.COMPUTER_LAB, 45, 1, True),
            ('CSE_DEPT', 'CS-LH1', 'CSE Lecture Room 1', Room.RoomType.CLASSROOM, 65, 1, True),
            ('CSE_DEPT', 'CS-LAB1', 'Algorithms & Database Lab', Room.RoomType.COMPUTER_LAB, 40, 2, True),
            ('CSE_DEPT', 'CS-LAB2', 'AI & Machine Learning Lab', Room.RoomType.COMPUTER_LAB, 40, 2, True),
            ('ECE_DEPT', 'EC-LH1', 'ECE Lecture Room 1', Room.RoomType.CLASSROOM, 65, 1, True),
            ('ECE_DEPT', 'EC-LAB1', 'Digital Electronics Lab', Room.RoomType.ELECTRONICS_LAB, 40, 2, True),
            ('ECE_DEPT', 'EC-LAB2', 'VLSI & Communication Lab', Room.RoomType.ELECTRONICS_LAB, 40, 2, True),
            ('ELEC_BLK', 'EE-LH1', 'Electrical Lecture Hall 1', Room.RoomType.CLASSROOM, 65, 1, True),
            ('ELEC_BLK', 'EE-LAB1', 'Electrical Machines Lab', Room.RoomType.ELECTRONICS_LAB, 40, 1, True),
            ('MECH_BLK', 'ME-LH1', 'Mechanical Lecture Hall 1', Room.RoomType.CLASSROOM, 65, 1, True),
            ('MECH_BLK', 'ME-CAD', 'CAD / CAM Simulation Lab', Room.RoomType.COMPUTER_LAB, 40, 2, True),
            ('CIVIL_BLK', 'CE-LH1', 'Civil Lecture Hall 1', Room.RoomType.CLASSROOM, 65, 1, True),
            ('CIVIL_BLK', 'CE-LAB1', 'Material Testing & Survey Lab', Room.RoomType.CLASSROOM, 40, 1, True),
            ('CENTRAL_AUD', 'AUD-MAIN', 'NIT JSR Main Auditorium', Room.RoomType.SEMINAR_HALL, 250, 1, True),
        ]
        for b_code, r_no, r_name, r_type, cap, fl, proj in rooms_data:
            Room.objects.update_or_create(
                building=bld_map[b_code],
                room_no=r_no,
                defaults={
                    'name': r_name,
                    'room_type': r_type,
                    'capacity': cap,
                    'floor': fl,
                    'has_projector': proj,
                    'is_active': True,
                }
            )
        self.stdout.write(self.style.SUCCESS("[OK] Campus Buildings and Rooms seeded"))

        # -------------------------------------------------------------------------
        # 4. DEPARTMENTS & ACADEMIC BRANCHES
        # -------------------------------------------------------------------------
        departments_info = [
            ('CSE', 'Computer Science and Engineering', 'Department of Computer Science & Engineering'),
            ('ECE', 'Electronics and Communication Engineering', 'Department of Electronics & Communication Engineering'),
            ('EE', 'Electrical Engineering', 'Department of Electrical Engineering'),
            ('ME', 'Mechanical Engineering', 'Department of Mechanical Engineering'),
            ('CE', 'Civil Engineering', 'Department of Civil Engineering'),
            ('MME', 'Metallurgical and Materials Engineering', 'Department of Metallurgical & Materials Engineering'),
            ('PIE', 'Production and Industrial Engineering', 'Department of Production & Industrial Engineering'),
            ('CA', 'Computer Applications', 'Department of Computer Applications (MCA)'),
            ('MATH', 'Mathematics & Computing', 'Department of Mathematics & Scientific Computing'),
            ('PHY', 'Physics', 'Department of Physics'),
            ('CHEM', 'Chemistry', 'Department of Chemistry'),
            ('HSS', 'Humanities & Social Sciences', 'Department of Humanities & Management Studies'),
        ]
        dept_map = {}
        for code, name, desc in departments_info:
            dept, _ = Department.objects.update_or_create(
                code=code,
                defaults={'name': name, 'description': desc, 'is_active': True}
            )
            dept_map[code] = dept

        # Clean up legacy duplicate department code 'MCA' if present
        legacy_mca = Department.objects.filter(code='MCA').exclude(id=dept_map['CA'].id).first()
        if legacy_mca:
            for b in legacy_mca.branches.all():
                for c in b.cohorts.all():
                    for off in c.offerings.all():
                        for ta in off.teaching_assignments.all():
                            ta.scheduled_meetings.all().delete()
                            ta.delete()
                        off.delete()
                    c.delete()
                b.curriculum_items.all().delete()
                b.delete()
            legacy_mca.delete()

        branches_info = [
            (dept_map['CSE'], 'BTECH_CSE', 'B.Tech in Computer Science and Engineering', 'B.Tech', 8),
            (dept_map['CSE'], 'MTECH_CSE', 'M.Tech in Computer Science (Information Systems)', 'M.Tech', 4),
            (dept_map['ECE'], 'BTECH_ECE', 'B.Tech in Electronics and Communication Engineering', 'B.Tech', 8),
            (dept_map['EE'], 'BTECH_EE', 'B.Tech in Electrical Engineering', 'B.Tech', 8),
            (dept_map['ME'], 'BTECH_ME', 'B.Tech in Mechanical Engineering', 'B.Tech', 8),
            (dept_map['CE'], 'BTECH_CE', 'B.Tech in Civil Engineering', 'B.Tech', 8),
            (dept_map['MME'], 'BTECH_MME', 'B.Tech in Metallurgical and Materials Engineering', 'B.Tech', 8),
            (dept_map['PIE'], 'BTECH_PIE', 'B.Tech in Production and Industrial Engineering', 'B.Tech', 8),
            (dept_map['CA'], 'MCA', 'Master of Computer Applications', 'MCA', 6),
            (dept_map['PHY'], 'MSC_PHY', 'M.Sc. in Physics', 'M.Sc.', 4),
            (dept_map['CHEM'], 'MSC_CHEM', 'M.Sc. in Chemistry', 'M.Sc.', 4),
            (dept_map['MATH'], 'MSC_MATH', 'M.Sc. in Mathematics', 'M.Sc.', 4),
        ]
        branch_map = {}
        for dept, b_code, b_name, degree, max_sems in branches_info:
            branch, _ = Branch.objects.update_or_create(
                department=dept,
                code=b_code,
                defaults={
                    'name': b_name,
                    'degree_name': degree,
                    'max_semesters': max_sems,
                    'is_active': True,
                }
            )
            branch_map[b_code] = branch
        self.stdout.write(self.style.SUCCESS("[OK] Departments and Branches seeded"))

        # -------------------------------------------------------------------------
        # 5. PROFESSORS & FACULTY ROSTER
        # -------------------------------------------------------------------------
        common_password = 'Password@123'

        admin_user, _ = User.objects.update_or_create(
            email='admin@nitjsr.ac.in',
            defaults={
                'full_name': 'Dr. Gautam Sutradhar (Director)',
                'employee_code': 'NITJSR-ADM-001',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )
        admin_user.set_password(common_password)
        admin_user.save()
        UserRoleAssignment.objects.get_or_create(user=admin_user, role=admin_role, branch=None)

        faculty_roster = [
            # CSE
            ('dkumar.cse@nitjsr.ac.in', 'Dr. Dilip Kumar', 'NITJSR-CSE-001', 'CSE', 'Professor & HOD', 5, 'BTECH_CSE'),
            ('vkumar.cse@nitjsr.ac.in', 'Dr. Vinay Kumar', 'NITJSR-CSE-002', 'CSE', 'Associate Professor', 6, None),
            ('skumar.cse@nitjsr.ac.in', 'Dr. Sanjay Kumar', 'NITJSR-CSE-003', 'CSE', 'Assistant Professor', 6, None),
            ('bksingh.cse@nitjsr.ac.in', 'Dr. B. K. Singh', 'NITJSR-CSE-004', 'CSE', 'Professor', 6, None),
            ('sdutta.cse@nitjsr.ac.in', 'Dr. Subrata Dutta', 'NITJSR-CSE-005', 'CSE', 'Assistant Professor', 6, None),
            ('rkagrawal.cse@nitjsr.ac.in', 'Dr. R. K. Agrawal', 'NITJSR-CSE-006', 'CSE', 'Associate Professor', 6, None),
            ('kpatel.cse@nitjsr.ac.in', 'Dr. K. Patel', 'NITJSR-CSE-007', 'CSE', 'Assistant Professor', 6, None),
            ('asingh.cse@nitjsr.ac.in', 'Dr. Abhimanyu Singh', 'NITJSR-CSE-008', 'CSE', 'Assistant Professor', 6, None),
            ('sroy.cse@nitjsr.ac.in', 'Dr. Sudip Roy', 'NITJSR-CSE-009', 'CSE', 'Associate Professor', 6, None),

            # ECE
            ('kksingh.ece@nitjsr.ac.in', 'Dr. K. K. Singh', 'NITJSR-ECE-001', 'ECE', 'Professor & HOD', 5, 'BTECH_ECE'),
            ('rsinha.ece@nitjsr.ac.in', 'Dr. Rashmi Sinha', 'NITJSR-ECE-002', 'ECE', 'Associate Professor', 6, None),
            ('akumar.ece@nitjsr.ac.in', 'Dr. Amit Kumar', 'NITJSR-ECE-003', 'ECE', 'Assistant Professor', 6, None),
            ('bbhowmik.ece@nitjsr.ac.in', 'Dr. Basanta Bhowmik', 'NITJSR-ECE-004', 'ECE', 'Assistant Professor', 6, None),
            ('jsengupta.ece@nitjsr.ac.in', 'Dr. Joydeep Sengupta', 'NITJSR-ECE-005', 'ECE', 'Associate Professor', 6, None),
            ('nagrawal.ece@nitjsr.ac.in', 'Dr. Neha Agrawal', 'NITJSR-ECE-006', 'ECE', 'Assistant Professor', 6, None),

            # EE
            ('nkumar.ee@nitjsr.ac.in', 'Dr. Niranjan Kumar', 'NITJSR-EE-001', 'EE', 'Professor & HOD', 5, 'BTECH_EE'),
            ('jkumar.ee@nitjsr.ac.in', 'Dr. Jitendra Kumar', 'NITJSR-EE-002', 'EE', 'Associate Professor', 6, None),
            ('ohgupta.ee@nitjsr.ac.in', 'Dr. Om Hari Gupta', 'NITJSR-EE-003', 'EE', 'Assistant Professor', 6, None),
            ('mkumar.ee@nitjsr.ac.in', 'Dr. Madan Kumar', 'NITJSR-EE-004', 'EE', 'Assistant Professor', 6, None),
            ('tkumar.ee@nitjsr.ac.in', 'Dr. Tarun Kumar', 'NITJSR-EE-005', 'EE', 'Associate Professor', 6, None),

            # ME
            ('rvsharma.me@nitjsr.ac.in', 'Dr. R. V. Sharma', 'NITJSR-ME-001', 'ME', 'Professor & HOD', 5, 'BTECH_ME'),
            ('skprasad.me@nitjsr.ac.in', 'Dr. S. K. Prasad', 'NITJSR-ME-002', 'ME', 'Associate Professor', 6, None),
            ('akmech.me@nitjsr.ac.in', 'Dr. Anil Kumar', 'NITJSR-ME-003', 'ME', 'Assistant Professor', 6, None),
            ('pkumar.me@nitjsr.ac.in', 'Dr. Prabhas Kumar', 'NITJSR-ME-004', 'ME', 'Associate Professor', 6, None),
            ('ssen.me@nitjsr.ac.in', 'Dr. Sanjay Sen', 'NITJSR-ME-005', 'ME', 'Assistant Professor', 6, None),

            # CE
            ('akchoudhary.ce@nitjsr.ac.in', 'Dr. A. K. Choudhary', 'NITJSR-CE-001', 'CE', 'Professor & HOD', 6, 'BTECH_CE'),
            ('ssroy.ce@nitjsr.ac.in', 'Dr. S. S. Roy', 'NITJSR-CE-002', 'CE', 'Associate Professor', 6, None),
            ('rrsahu.ce@nitjsr.ac.in', 'Dr. R. R. Sahu', 'NITJSR-CE-003', 'CE', 'Assistant Professor', 6, None),
            ('broy.ce@nitjsr.ac.in', 'Dr. B. Roy', 'NITJSR-CE-004', 'CE', 'Associate Professor', 6, None),

            # MME
            ('ashok.mme@nitjsr.ac.in', 'Dr. Ashok Kumar', 'NITJSR-MME-001', 'MME', 'Professor & HOD', 6, 'BTECH_MME'),
            ('rprasad.mme@nitjsr.ac.in', 'Dr. Ranjit Prasad', 'NITJSR-MME-002', 'MME', 'Associate Professor', 6, None),
            ('rksahoo.mme@nitjsr.ac.in', 'Dr. R. K. Sahoo', 'NITJSR-MME-003', 'MME', 'Assistant Professor', 6, None),

            # PIE
            ('skmukherjee.pie@nitjsr.ac.in', 'Dr. S. K. Mukherjee', 'NITJSR-PIE-001', 'PIE', 'Professor & HOD', 6, 'BTECH_PIE'),
            ('ssmahapatra.pie@nitjsr.ac.in', 'Dr. S. S. Mahapatra', 'NITJSR-PIE-002', 'PIE', 'Associate Professor', 6, None),

            # CA
            ('dkyadav.ca@nitjsr.ac.in', 'Dr. D. K. Yadav', 'NITJSR-CA-001', 'CA', 'Associate Professor & HOD', 6, 'MCA'),
            ('rranjan.ca@nitjsr.ac.in', 'Dr. Rajiv Ranjan', 'NITJSR-CA-002', 'CA', 'Assistant Professor', 6, None),
            ('pkjha.ca@nitjsr.ac.in', 'Dr. P. K. Jha', 'NITJSR-CA-003', 'CA', 'Associate Professor', 6, None),

            # Basic Sciences & Humanities
            ('gsmahapatra.math@nitjsr.ac.in', 'Dr. G. S. Mahapatra', 'NITJSR-MATH-001', 'MATH', 'Professor & HOD', 6, 'MSC_MATH'),
            ('dpdutta.math@nitjsr.ac.in', 'Dr. D. P. Dutta', 'NITJSR-MATH-002', 'MATH', 'Associate Professor', 6, None),
            ('hlyadav.phy@nitjsr.ac.in', 'Dr. H. L. Yadav', 'NITJSR-PHY-001', 'PHY', 'Professor & HOD', 6, 'MSC_PHY'),
            ('dnmahato.phy@nitjsr.ac.in', 'Dr. D. N. Mahato', 'NITJSR-PHY-002', 'PHY', 'Associate Professor', 6, None),
            ('bambade.chem@nitjsr.ac.in', 'Dr. Balram Ambade', 'NITJSR-CHEM-001', 'CHEM', 'Professor & HOD', 6, 'MSC_CHEM'),
            ('rkdey.chem@nitjsr.ac.in', 'Dr. R. K. Dey', 'NITJSR-CHEM-002', 'CHEM', 'Associate Professor', 6, None),
            ('rktiwari.hss@nitjsr.ac.in', 'Dr. R. K. Tiwari', 'NITJSR-HSS-001', 'HSS', 'Associate Professor & HOD', 6, None),
            ('ssharma.hss@nitjsr.ac.in', 'Dr. Shruti Sharma', 'NITJSR-HSS-002', 'HSS', 'Assistant Professor', 6, None),
        ]

        prof_user_map = {}
        for email, full_name, emp_code, dept_code, desig, max_hrs, coord_branch in faculty_roster:
            user, _ = User.objects.update_or_create(
                email=email,
                defaults={
                    'full_name': full_name,
                    'employee_code': emp_code,
                    'is_staff': False,
                    'is_active': True,
                }
            )
            user.set_password(common_password)
            user.save()

            UserRoleAssignment.objects.get_or_create(user=user, role=prof_role, branch=None)
            if coord_branch and coord_branch in branch_map:
                UserRoleAssignment.objects.get_or_create(
                    user=user,
                    role=coord_role,
                    branch=branch_map[coord_branch]
                )

            dept_obj = dept_map[dept_code]
            ProfessorProfile.objects.update_or_create(
                user=user,
                defaults={
                    'department': dept_obj,
                    'designation': desig,
                    'max_hours_per_day': max_hrs,
                }
            )
            prof_user_map[email] = user

        self.stdout.write(self.style.SUCCESS(f"[OK] {len(faculty_roster)} Professors & Faculty Members seeded"))

        # -------------------------------------------------------------------------
        # 6. MULTIPLE ACADEMIC YEARS & TERMS
        # -------------------------------------------------------------------------
        years_data = [
            ('2024-25', date(2024, 8, 1), date(2025, 6, 30), False),
            ('2025-26', date(2025, 8, 1), date(2026, 6, 30), False),
            ('2026-27', date(2026, 8, 1), date(2027, 6, 30), True),
        ]
        year_obj_map = {}
        terms_map = {}

        for y_name, s_date, e_date, is_curr in years_data:
            ay, _ = AcademicYear.objects.update_or_create(
                name=y_name,
                defaults={
                    'start_date': s_date,
                    'end_date': e_date,
                    'is_current': is_curr,
                    'is_active': True,
                }
            )
            year_obj_map[y_name] = ay

            # Odd Semester
            odd_start = s_date
            odd_end = date(s_date.year, 12, 22)
            ot, _ = AcademicTerm.objects.update_or_create(
                academic_year=ay,
                name=f'Odd Semester {y_name} (Autumn)',
                defaults={
                    'term_type': AcademicTerm.TermType.ODD,
                    'start_date': odd_start,
                    'end_date': odd_end,
                    'is_active': True,
                }
            )
            terms_map[(y_name, 'ODD')] = ot

            # Even Semester
            even_start = date(e_date.year, 1, 10)
            even_end = e_date
            et, _ = AcademicTerm.objects.update_or_create(
                academic_year=ay,
                name=f'Even Semester {y_name} (Spring)',
                defaults={
                    'term_type': AcademicTerm.TermType.EVEN,
                    'start_date': even_start,
                    'end_date': even_end,
                    'is_active': True,
                }
            )
            terms_map[(y_name, 'EVEN')] = et

        current_odd_term = terms_map[('2026-27', 'ODD')]
        current_even_term = terms_map[('2026-27', 'EVEN')]
        self.stdout.write(self.style.SUCCESS("[OK] Academic Years (2024-25, 2025-26, 2026-27) and Terms seeded"))

        # -------------------------------------------------------------------------
        # 7. COMPREHENSIVE CURRICULUM SUBJECTS FOR EVERY BRANCH & SEMESTER
        # -------------------------------------------------------------------------
        # Helpers for department faculty assignment
        dept_profs = {}
        for email, full_name, emp_code, dept_code, desig, max_hrs, coord_branch in faculty_roster:
            dept_profs.setdefault(dept_code, []).append(email)

        # Subjects structure:
        # branch_code -> semester_no -> list of (code, name, credit, course_type, dept_code, pref_room_type, weekly_meetings, duration_slots)
        branch_curriculum_catalog = {
            'BTECH_CSE': {
                1: [
                    ('CS101-PH', 'Engineering Physics', 4, 'THEORY', 'PHY', 'CLASSROOM', 3, 1),
                    ('CS101-MA', 'Calculus & Linear Algebra', 4, 'THEORY', 'MATH', 'CLASSROOM', 3, 1),
                    ('CS101-EE', 'Basic Electrical Engineering', 3, 'THEORY', 'EE', 'CLASSROOM', 3, 1),
                    ('CS101-ME', 'Engineering Graphics & Design', 3, 'THEORY', 'ME', 'CLASSROOM', 3, 1),
                    ('CS101-HS', 'Professional Communication Skills', 2, 'THEORY', 'HSS', 'CLASSROOM', 2, 1),
                    ('CS101-PHL', 'Engineering Physics Laboratory', 2, 'LAB', 'PHY', 'CLASSROOM', 1, 3),
                    ('CS101-EEL', 'Basic Electrical Engineering Lab', 2, 'LAB', 'EE', 'ELECTRONICS_LAB', 1, 3),
                ],
                2: [
                    ('CS102-CH', 'Engineering Chemistry', 4, 'THEORY', 'CHEM', 'CLASSROOM', 3, 1),
                    ('CS102-MA', 'Advanced Calculus & Differential Equations', 4, 'THEORY', 'MATH', 'CLASSROOM', 3, 1),
                    ('CS102-CS', 'Programming for Problem Solving (C)', 4, 'THEORY', 'CSE', 'CLASSROOM', 3, 1),
                    ('CS102-CE', 'Engineering Mechanics', 3, 'THEORY', 'CE', 'CLASSROOM', 3, 1),
                    ('CS102-CHL', 'Engineering Chemistry Laboratory', 2, 'LAB', 'CHEM', 'CLASSROOM', 1, 3),
                    ('CS102-CSL', 'Programming in C Laboratory', 2, 'LAB', 'CSE', 'COMPUTER_LAB', 1, 3),
                ],
                3: [
                    ('CS201', 'Data Structures and Algorithms', 4, 'THEORY', 'CSE', 'CLASSROOM', 3, 1),
                    ('CS202', 'Discrete Mathematics & Graph Theory', 4, 'THEORY', 'CSE', 'CLASSROOM', 3, 1),
                    ('CS203', 'Digital Electronics and Logic Design', 3, 'THEORY', 'ECE', 'CLASSROOM', 3, 1),
                    ('CS204', 'Object Oriented Programming with Java', 3, 'THEORY', 'CSE', 'CLASSROOM', 3, 1),
                    ('CS205', 'Data Structures Laboratory', 2, 'LAB', 'CSE', 'COMPUTER_LAB', 1, 3),
                    ('CS206', 'Java Programming Laboratory', 2, 'LAB', 'CSE', 'COMPUTER_LAB', 1, 3),
                ],
                4: [
                    ('CS251', 'Computer Organization & Architecture', 4, 'THEORY', 'CSE', 'CLASSROOM', 3, 1),
                    ('CS252', 'Database Management Systems', 4, 'THEORY', 'CSE', 'CLASSROOM', 3, 1),
                    ('CS253', 'Design and Analysis of Algorithms', 4, 'THEORY', 'CSE', 'CLASSROOM', 3, 1),
                    ('CS254', 'Formal Language & Automata Theory', 3, 'THEORY', 'CSE', 'CLASSROOM', 3, 1),
                    ('CS255', 'Database Systems Laboratory', 2, 'LAB', 'CSE', 'COMPUTER_LAB', 1, 3),
                    ('CS256', 'Algorithms Laboratory', 2, 'LAB', 'CSE', 'COMPUTER_LAB', 1, 3),
                ],
                5: [
                    ('CS301', 'Operating Systems', 4, 'THEORY', 'CSE', 'CLASSROOM', 3, 1),
                    ('CS302', 'Computer Networks & Internet Protocols', 4, 'THEORY', 'CSE', 'CLASSROOM', 3, 1),
                    ('CS303', 'Software Engineering & Agile Methods', 3, 'THEORY', 'CSE', 'CLASSROOM', 3, 1),
                    ('CS304', 'Microprocessors and Interfacing', 3, 'THEORY', 'ECE', 'CLASSROOM', 3, 1),
                    ('CS305', 'Operating Systems & Networks Lab', 2, 'LAB', 'CSE', 'COMPUTER_LAB', 1, 3),
                    ('CS306', 'Software Engineering Laboratory', 2, 'LAB', 'CSE', 'COMPUTER_LAB', 1, 3),
                    ('CS307', 'Technical Seminar & Mini Project', 1, 'SEMINAR', 'CSE', 'SEMINAR_HALL', 1, 1),
                ],
                6: [
                    ('CS351', 'Compiler Design', 4, 'THEORY', 'CSE', 'CLASSROOM', 3, 1),
                    ('CS352', 'Machine Learning & Applications', 4, 'THEORY', 'CSE', 'CLASSROOM', 3, 1),
                    ('CS353', 'Web Technologies and Frameworks', 3, 'THEORY', 'CSE', 'CLASSROOM', 3, 1),
                    ('CS354', 'Cryptography and Network Security', 3, 'THEORY', 'CSE', 'CLASSROOM', 3, 1),
                    ('CS355', 'Compiler Design Laboratory', 2, 'LAB', 'CSE', 'COMPUTER_LAB', 1, 3),
                    ('CS356', 'Web Technologies Laboratory', 2, 'LAB', 'CSE', 'COMPUTER_LAB', 1, 3),
                ],
                7: [
                    ('CS401', 'Artificial Intelligence & Neural Networks', 4, 'THEORY', 'CSE', 'CLASSROOM', 3, 1),
                    ('CS402', 'Cloud Computing & Virtualization', 3, 'THEORY', 'CSE', 'CLASSROOM', 3, 1),
                    ('CS403', 'Distributed Systems & Algorithms', 3, 'THEORY', 'CSE', 'CLASSROOM', 3, 1),
                    ('CS404', 'Big Data Analytics', 3, 'THEORY', 'CSE', 'CLASSROOM', 3, 1),
                    ('CS405', 'AI & Cloud Computing Laboratory', 2, 'LAB', 'CSE', 'COMPUTER_LAB', 1, 3),
                    ('CS406', 'Capstone Project Phase - I', 4, 'PROJECT', 'CSE', 'SEMINAR_HALL', 1, 2),
                ],
                8: [
                    ('CS451', 'Internet of Things & Embedded Systems', 3, 'THEORY', 'CSE', 'CLASSROOM', 3, 1),
                    ('CS452', 'Information & Cyber Security', 3, 'THEORY', 'CSE', 'CLASSROOM', 3, 1),
                    ('CS453', 'Deep Learning & Natural Language Processing', 3, 'THEORY', 'CSE', 'CLASSROOM', 3, 1),
                    ('CS454', 'Capstone Project Phase - II', 8, 'PROJECT', 'CSE', 'SEMINAR_HALL', 1, 2),
                    ('CS455', 'Comprehensive Viva-Voce', 2, 'SEMINAR', 'CSE', 'SEMINAR_HALL', 1, 1),
                ],
            },
            'BTECH_ECE': {
                1: [
                    ('EC101-PH', 'Engineering Physics', 4, 'THEORY', 'PHY', 'CLASSROOM', 3, 1),
                    ('EC101-MA', 'Calculus & Linear Algebra', 4, 'THEORY', 'MATH', 'CLASSROOM', 3, 1),
                    ('EC101-EE', 'Basic Electrical Engineering', 3, 'THEORY', 'EE', 'CLASSROOM', 3, 1),
                    ('EC101-ME', 'Engineering Graphics & Design', 3, 'THEORY', 'ME', 'CLASSROOM', 3, 1),
                    ('EC101-PHL', 'Engineering Physics Laboratory', 2, 'LAB', 'PHY', 'CLASSROOM', 1, 3),
                ],
                2: [
                    ('EC102-CH', 'Engineering Chemistry', 4, 'THEORY', 'CHEM', 'CLASSROOM', 3, 1),
                    ('EC102-MA', 'Differential Equations & Transforms', 4, 'THEORY', 'MATH', 'CLASSROOM', 3, 1),
                    ('EC102-CS', 'Computer Programming for Engineers', 4, 'THEORY', 'CSE', 'CLASSROOM', 3, 1),
                    ('EC102-CSL', 'Programming Laboratory', 2, 'LAB', 'CSE', 'COMPUTER_LAB', 1, 3),
                ],
                3: [
                    ('EC201', 'Electronic Devices and Semiconductor Circuits', 4, 'THEORY', 'ECE', 'CLASSROOM', 3, 1),
                    ('EC202', 'Signals and Continuous Systems', 4, 'THEORY', 'ECE', 'CLASSROOM', 3, 1),
                    ('EC203', 'Network Theory and Circuit Analysis', 3, 'THEORY', 'ECE', 'CLASSROOM', 3, 1),
                    ('EC204', 'Electromagnetic Field Theory', 3, 'THEORY', 'ECE', 'CLASSROOM', 3, 1),
                    ('EC205', 'Electronic Devices Laboratory', 2, 'LAB', 'ECE', 'ELECTRONICS_LAB', 1, 3),
                ],
                4: [
                    ('EC251', 'Analog Integrated Circuits & Op-Amps', 4, 'THEORY', 'ECE', 'CLASSROOM', 3, 1),
                    ('EC252', 'Digital System Design & VHDL', 4, 'THEORY', 'ECE', 'CLASSROOM', 3, 1),
                    ('EC253', 'Analog Communication Systems', 3, 'THEORY', 'ECE', 'CLASSROOM', 3, 1),
                    ('EC254', 'Analog Circuits & IC Lab', 2, 'LAB', 'ECE', 'ELECTRONICS_LAB', 1, 3),
                ],
                5: [
                    ('EC301', 'Digital Communication Systems', 4, 'THEORY', 'ECE', 'CLASSROOM', 3, 1),
                    ('EC302', 'Microprocessors & Microcontrollers', 4, 'THEORY', 'ECE', 'CLASSROOM', 3, 1),
                    ('EC303', 'Control Systems Engineering', 3, 'THEORY', 'EE', 'CLASSROOM', 3, 1),
                    ('EC304', 'Digital Communication Lab', 2, 'LAB', 'ECE', 'ELECTRONICS_LAB', 1, 3),
                ],
                6: [
                    ('EC351', 'VLSI Design and CMOS Technology', 4, 'THEORY', 'ECE', 'CLASSROOM', 3, 1),
                    ('EC352', 'Digital Signal Processing', 4, 'THEORY', 'ECE', 'CLASSROOM', 3, 1),
                    ('EC353', 'Microwave & Radar Engineering', 3, 'THEORY', 'ECE', 'CLASSROOM', 3, 1),
                    ('EC354', 'VLSI CAD & DSP Laboratory', 2, 'LAB', 'ECE', 'ELECTRONICS_LAB', 1, 3),
                ],
                7: [
                    ('EC401', 'Wireless and Mobile Communications', 4, 'THEORY', 'ECE', 'CLASSROOM', 3, 1),
                    ('EC402', 'Embedded Systems & RTOS', 3, 'THEORY', 'ECE', 'CLASSROOM', 3, 1),
                    ('EC403', 'Optical Fiber Communication', 3, 'THEORY', 'ECE', 'CLASSROOM', 3, 1),
                    ('EC404', 'Major Project Phase - I', 4, 'PROJECT', 'ECE', 'SEMINAR_HALL', 1, 2),
                ],
                8: [
                    ('EC451', 'Satellite & Radar Systems', 3, 'THEORY', 'ECE', 'CLASSROOM', 3, 1),
                    ('EC452', 'Biomedical Instrumentation', 3, 'THEORY', 'ECE', 'CLASSROOM', 3, 1),
                    ('EC453', 'Major Project Phase - II', 8, 'PROJECT', 'ECE', 'SEMINAR_HALL', 1, 2),
                ],
            },
            'BTECH_EE': {
                1: [
                    ('EE101-PH', 'Engineering Physics', 4, 'THEORY', 'PHY', 'CLASSROOM', 3, 1),
                    ('EE101-MA', 'Mathematics - I', 4, 'THEORY', 'MATH', 'CLASSROOM', 3, 1),
                    ('EE101-EE', 'Introduction to Electrical Engineering', 3, 'THEORY', 'EE', 'CLASSROOM', 3, 1),
                    ('EE101-EEL', 'Electrical Engineering Lab', 2, 'LAB', 'EE', 'ELECTRONICS_LAB', 1, 3),
                ],
                2: [
                    ('EE102-CH', 'Engineering Chemistry', 4, 'THEORY', 'CHEM', 'CLASSROOM', 3, 1),
                    ('EE102-MA', 'Mathematics - II', 4, 'THEORY', 'MATH', 'CLASSROOM', 3, 1),
                    ('EE102-CS', 'Programming in C', 4, 'THEORY', 'CSE', 'CLASSROOM', 3, 1),
                    ('EE102-CSL', 'Programming Lab', 2, 'LAB', 'CSE', 'COMPUTER_LAB', 1, 3),
                ],
                3: [
                    ('EE201', 'Electrical Circuit Analysis & Synthesis', 4, 'THEORY', 'EE', 'CLASSROOM', 3, 1),
                    ('EE202', 'Electrical Machines - I', 4, 'THEORY', 'EE', 'CLASSROOM', 3, 1),
                    ('EE203', 'Electromagnetic Field Theory', 3, 'THEORY', 'EE', 'CLASSROOM', 3, 1),
                    ('EE204', 'Electrical Machines Lab - I', 2, 'LAB', 'EE', 'ELECTRONICS_LAB', 1, 3),
                ],
                4: [
                    ('EE251', 'Electrical Machines - II', 4, 'THEORY', 'EE', 'CLASSROOM', 3, 1),
                    ('EE252', 'Power Generation and Transmission', 4, 'THEORY', 'EE', 'CLASSROOM', 3, 1),
                    ('EE253', 'Electrical Measurement & Instrumentation', 3, 'THEORY', 'EE', 'CLASSROOM', 3, 1),
                    ('EE254', 'Electrical Machines Lab - II', 2, 'LAB', 'EE', 'ELECTRONICS_LAB', 1, 3),
                ],
                5: [
                    ('EE301', 'Control Systems Engineering', 4, 'THEORY', 'EE', 'CLASSROOM', 3, 1),
                    ('EE302', 'Power Electronics and Converters', 4, 'THEORY', 'EE', 'CLASSROOM', 3, 1),
                    ('EE303', 'Microprocessors & Microcontrollers', 3, 'THEORY', 'ECE', 'CLASSROOM', 3, 1),
                    ('EE304', 'Control Systems & Power Electronics Lab', 2, 'LAB', 'EE', 'ELECTRONICS_LAB', 1, 3),
                ],
                6: [
                    ('EE351', 'Switchgear and Power System Protection', 4, 'THEORY', 'EE', 'CLASSROOM', 3, 1),
                    ('EE352', 'Electric Drives and Control', 4, 'THEORY', 'EE', 'CLASSROOM', 3, 1),
                    ('EE353', 'Renewable Energy Technologies', 3, 'THEORY', 'EE', 'CLASSROOM', 3, 1),
                    ('EE354', 'Electric Drives Laboratory', 2, 'LAB', 'EE', 'ELECTRONICS_LAB', 1, 3),
                ],
                7: [
                    ('EE401', 'High Voltage Engineering', 4, 'THEORY', 'EE', 'CLASSROOM', 3, 1),
                    ('EE402', 'Smart Grid Operations', 3, 'THEORY', 'EE', 'CLASSROOM', 3, 1),
                    ('EE403', 'Industrial Automation & PLC', 3, 'THEORY', 'EE', 'CLASSROOM', 3, 1),
                    ('EE404', 'Major Project Phase - I', 4, 'PROJECT', 'EE', 'SEMINAR_HALL', 1, 2),
                ],
                8: [
                    ('EE451', 'Power Quality and FACTS Devices', 3, 'THEORY', 'EE', 'CLASSROOM', 3, 1),
                    ('EE452', 'Electric Vehicle Powertrain Architecture', 3, 'THEORY', 'EE', 'CLASSROOM', 3, 1),
                    ('EE453', 'Major Project Phase - II', 8, 'PROJECT', 'EE', 'SEMINAR_HALL', 1, 2),
                ],
            },
            'BTECH_ME': {
                1: [
                    ('ME101-PH', 'Engineering Physics', 4, 'THEORY', 'PHY', 'CLASSROOM', 3, 1),
                    ('ME101-MA', 'Mathematics - I', 4, 'THEORY', 'MATH', 'CLASSROOM', 3, 1),
                    ('ME101-ME', 'Engineering Graphics & CAD', 3, 'THEORY', 'ME', 'CLASSROOM', 3, 1),
                    ('ME101-MEL', 'Workshop Practices', 2, 'LAB', 'ME', 'CLASSROOM', 1, 3),
                ],
                2: [
                    ('ME102-CH', 'Engineering Chemistry', 4, 'THEORY', 'CHEM', 'CLASSROOM', 3, 1),
                    ('ME102-MA', 'Mathematics - II', 4, 'THEORY', 'MATH', 'CLASSROOM', 3, 1),
                    ('ME102-CE', 'Engineering Mechanics & Statics', 3, 'THEORY', 'CE', 'CLASSROOM', 3, 1),
                    ('ME102-CHL', 'Chemistry Lab', 2, 'LAB', 'CHEM', 'CLASSROOM', 1, 3),
                ],
                3: [
                    ('ME201', 'Engineering Thermodynamics', 4, 'THEORY', 'ME', 'CLASSROOM', 3, 1),
                    ('ME202', 'Mechanics of Solids', 4, 'THEORY', 'ME', 'CLASSROOM', 3, 1),
                    ('ME203', 'Materials Science & Metallurgy', 3, 'THEORY', 'ME', 'CLASSROOM', 3, 1),
                    ('ME204', 'Solid Mechanics Laboratory', 2, 'LAB', 'ME', 'CLASSROOM', 1, 3),
                ],
                4: [
                    ('ME251', 'Applied Thermodynamics & Boilers', 4, 'THEORY', 'ME', 'CLASSROOM', 3, 1),
                    ('ME252', 'Theory of Machines - I', 4, 'THEORY', 'ME', 'CLASSROOM', 3, 1),
                    ('ME253', 'Manufacturing Technology - I', 3, 'THEORY', 'ME', 'CLASSROOM', 3, 1),
                    ('ME254', 'Thermal Engineering Lab', 2, 'LAB', 'ME', 'CLASSROOM', 1, 3),
                ],
                5: [
                    ('ME301', 'Heat and Mass Transfer', 4, 'THEORY', 'ME', 'CLASSROOM', 3, 1),
                    ('ME302', 'Design of Machine Elements - I', 4, 'THEORY', 'ME', 'CLASSROOM', 3, 1),
                    ('ME303', 'Dynamics of Machinery', 3, 'THEORY', 'ME', 'CLASSROOM', 3, 1),
                    ('ME304', 'Heat Transfer Laboratory', 2, 'LAB', 'ME', 'CLASSROOM', 1, 3),
                ],
                6: [
                    ('ME351', 'Internal Combustion Engines & Turbines', 4, 'THEORY', 'ME', 'CLASSROOM', 3, 1),
                    ('ME352', 'Manufacturing Technology - II', 4, 'THEORY', 'ME', 'CLASSROOM', 3, 1),
                    ('ME353', 'Refrigeration and Air Conditioning', 3, 'THEORY', 'ME', 'CLASSROOM', 3, 1),
                    ('ME354', 'IC Engines & RAC Laboratory', 2, 'LAB', 'ME', 'CLASSROOM', 1, 3),
                ],
                7: [
                    ('ME401', 'Automobile Engineering', 4, 'THEORY', 'ME', 'CLASSROOM', 3, 1),
                    ('ME402', 'Power Plant Engineering', 3, 'THEORY', 'ME', 'CLASSROOM', 3, 1),
                    ('ME403', 'Finite Element Analysis', 3, 'THEORY', 'ME', 'CLASSROOM', 3, 1),
                    ('ME404', 'Major Project Phase - I', 4, 'PROJECT', 'ME', 'SEMINAR_HALL', 1, 2),
                ],
                8: [
                    ('ME451', 'Robotics and Industrial Automation', 3, 'THEORY', 'ME', 'CLASSROOM', 3, 1),
                    ('ME452', 'Computational Fluid Dynamics', 3, 'THEORY', 'ME', 'CLASSROOM', 3, 1),
                    ('ME453', 'Major Project Phase - II', 8, 'PROJECT', 'ME', 'SEMINAR_HALL', 1, 2),
                ],
            },
            'BTECH_CE': {
                1: [
                    ('CE101-PH', 'Engineering Physics', 4, 'THEORY', 'PHY', 'CLASSROOM', 3, 1),
                    ('CE101-MA', 'Mathematics - I', 4, 'THEORY', 'MATH', 'CLASSROOM', 3, 1),
                    ('CE101-CE', 'Civil Engineering Drawing', 3, 'THEORY', 'CE', 'CLASSROOM', 3, 1),
                ],
                2: [
                    ('CE102-CH', 'Engineering Chemistry', 4, 'THEORY', 'CHEM', 'CLASSROOM', 3, 1),
                    ('CE102-MA', 'Mathematics - II', 4, 'THEORY', 'MATH', 'CLASSROOM', 3, 1),
                    ('CE102-CE', 'Basic Engineering Mechanics', 3, 'THEORY', 'CE', 'CLASSROOM', 3, 1),
                ],
                3: [
                    ('CE201', 'Solid Mechanics for Structures', 4, 'THEORY', 'CE', 'CLASSROOM', 3, 1),
                    ('CE202', 'Fluid Mechanics and Hydraulics', 4, 'THEORY', 'CE', 'CLASSROOM', 3, 1),
                    ('CE203', 'Surveying Techniques - I', 3, 'THEORY', 'CE', 'CLASSROOM', 3, 1),
                    ('CE204', 'Surveying Laboratory - I', 2, 'LAB', 'CE', 'CLASSROOM', 1, 3),
                ],
                4: [
                    ('CE251', 'Structural Analysis - I', 4, 'THEORY', 'CE', 'CLASSROOM', 3, 1),
                    ('CE252', 'Building Materials & Concrete Technology', 4, 'THEORY', 'CE', 'CLASSROOM', 3, 1),
                    ('CE253', 'Engineering Geology & Seismology', 3, 'THEORY', 'CE', 'CLASSROOM', 3, 1),
                    ('CE254', 'Material Testing Laboratory', 2, 'LAB', 'CE', 'CLASSROOM', 1, 3),
                ],
                5: [
                    ('CE301', 'Design of Concrete Structures - I', 4, 'THEORY', 'CE', 'CLASSROOM', 3, 1),
                    ('CE302', 'Geotechnical Engineering - I', 4, 'THEORY', 'CE', 'CLASSROOM', 3, 1),
                    ('CE303', 'Environmental Engineering - I', 3, 'THEORY', 'CE', 'CLASSROOM', 3, 1),
                    ('CE304', 'Geotechnical Engineering Lab', 2, 'LAB', 'CE', 'CLASSROOM', 1, 3),
                ],
                6: [
                    ('CE351', 'Design of Steel Structures', 4, 'THEORY', 'CE', 'CLASSROOM', 3, 1),
                    ('CE352', 'Transportation Engineering - I', 4, 'THEORY', 'CE', 'CLASSROOM', 3, 1),
                    ('CE353', 'Hydrology & Water Resources Engineering', 3, 'THEORY', 'CE', 'CLASSROOM', 3, 1),
                    ('CE354', 'Environmental Engineering Lab', 2, 'LAB', 'CE', 'CLASSROOM', 1, 3),
                ],
                7: [
                    ('CE401', 'Earthquake Resistant Structural Design', 4, 'THEORY', 'CE', 'CLASSROOM', 3, 1),
                    ('CE402', 'Construction Planning and Management', 3, 'THEORY', 'CE', 'CLASSROOM', 3, 1),
                    ('CE403', 'Major Project Phase - I', 4, 'PROJECT', 'CE', 'SEMINAR_HALL', 1, 2),
                ],
                8: [
                    ('CE451', 'Bridge Engineering and Design', 3, 'THEORY', 'CE', 'CLASSROOM', 3, 1),
                    ('CE452', 'Ground Improvement Techniques', 3, 'THEORY', 'CE', 'CLASSROOM', 3, 1),
                    ('CE453', 'Major Project Phase - II', 8, 'PROJECT', 'CE', 'SEMINAR_HALL', 1, 2),
                ],
            },
            'BTECH_MME': {
                1: [('MM101', 'Physics & Chemistry of Metals', 4, 'THEORY', 'PHY', 'CLASSROOM', 3, 1)],
                2: [('MM102', 'Basic Metallurgical Operations', 4, 'THEORY', 'MME', 'CLASSROOM', 3, 1)],
                3: [
                    ('MM201', 'Metallurgical Thermodynamics & Kinetics', 4, 'THEORY', 'MME', 'CLASSROOM', 3, 1),
                    ('MM202', 'Physical Metallurgy & Crystal Structures', 4, 'THEORY', 'MME', 'CLASSROOM', 3, 1),
                    ('MM203', 'Metallography Laboratory', 2, 'LAB', 'MME', 'CLASSROOM', 1, 3),
                ],
                4: [
                    ('MM251', 'Phase Transformations in Materials', 4, 'THEORY', 'MME', 'CLASSROOM', 3, 1),
                    ('MM252', 'Principles of Iron Making', 4, 'THEORY', 'MME', 'CLASSROOM', 3, 1),
                    ('MM253', 'Mechanical Testing of Materials Lab', 2, 'LAB', 'MME', 'CLASSROOM', 1, 3),
                ],
                5: [
                    ('MM301', 'Steel Making Technology', 4, 'THEORY', 'MME', 'CLASSROOM', 3, 1),
                    ('MM302', 'Heat Treatment of Steels & Alloys', 4, 'THEORY', 'MME', 'CLASSROOM', 3, 1),
                    ('MM303', 'Heat Treatment Laboratory', 2, 'LAB', 'MME', 'CLASSROOM', 1, 3),
                ],
                6: [
                    ('MM351', 'Non-Ferrous Extractive Metallurgy', 4, 'THEORY', 'MME', 'CLASSROOM', 3, 1),
                    ('MM352', 'Corrosion Science and Engineering', 4, 'THEORY', 'MME', 'CLASSROOM', 3, 1),
                    ('MM353', 'Corrosion Testing Lab', 2, 'LAB', 'MME', 'CLASSROOM', 1, 3),
                ],
                7: [
                    ('MM401', 'Welding & Casting Metallurgy', 4, 'THEORY', 'MME', 'CLASSROOM', 3, 1),
                    ('MM402', 'Major Project Phase - I', 4, 'PROJECT', 'MME', 'SEMINAR_HALL', 1, 2),
                ],
                8: [
                    ('MM451', 'Characterization of Advanced Materials', 3, 'THEORY', 'MME', 'CLASSROOM', 3, 1),
                    ('MM452', 'Major Project Phase - II', 8, 'PROJECT', 'MME', 'SEMINAR_HALL', 1, 2),
                ],
            },
            'BTECH_PIE': {
                1: [('PI101', 'Fundamentals of Manufacturing', 4, 'THEORY', 'PIE', 'CLASSROOM', 3, 1)],
                2: [('PI102', 'Workshop Technology & Machine Tools', 4, 'THEORY', 'PIE', 'CLASSROOM', 3, 1)],
                3: [
                    ('PI201', 'Manufacturing Processes - I', 4, 'THEORY', 'PIE', 'CLASSROOM', 3, 1),
                    ('PI202', 'Industrial Engineering and Productivity', 4, 'THEORY', 'PIE', 'CLASSROOM', 3, 1),
                    ('PI203', 'Manufacturing Processes Lab', 2, 'LAB', 'PIE', 'CLASSROOM', 1, 3),
                ],
                4: [
                    ('PI251', 'Machine Tool Technology & Metrology', 4, 'THEORY', 'PIE', 'CLASSROOM', 3, 1),
                    ('PI252', 'Work Study & Ergonomics Analysis', 4, 'THEORY', 'PIE', 'CLASSROOM', 3, 1),
                    ('PI253', 'Metrology & Inspection Lab', 2, 'LAB', 'PIE', 'CLASSROOM', 1, 3),
                ],
                5: [
                    ('PI301', 'Tool Engineering and Jig Design', 4, 'THEORY', 'PIE', 'CLASSROOM', 3, 1),
                    ('PI302', 'Supply Chain Management & Logistics', 4, 'THEORY', 'PIE', 'CLASSROOM', 3, 1),
                    ('PI303', 'Tool Design Laboratory', 2, 'LAB', 'PIE', 'CLASSROOM', 1, 3),
                ],
                6: [
                    ('PI351', 'Automation & Robotics in Production', 4, 'THEORY', 'PIE', 'CLASSROOM', 3, 1),
                    ('PI352', 'CNC Machining and Rapid Prototyping', 4, 'THEORY', 'PIE', 'CLASSROOM', 3, 1),
                    ('PI353', 'CNC Machining Lab', 2, 'LAB', 'PIE', 'CLASSROOM', 1, 3),
                ],
                7: [
                    ('PI401', 'Total Quality Management & Six Sigma', 4, 'THEORY', 'PIE', 'CLASSROOM', 3, 1),
                    ('PI402', 'Major Project Phase - I', 4, 'PROJECT', 'PIE', 'SEMINAR_HALL', 1, 2),
                ],
                8: [
                    ('PI451', 'Lean Manufacturing Systems', 3, 'THEORY', 'PIE', 'CLASSROOM', 3, 1),
                    ('PI452', 'Major Project Phase - II', 8, 'PROJECT', 'PIE', 'SEMINAR_HALL', 1, 2),
                ],
            },
            'MCA': {
                1: [
                    ('CA101', 'Mathematical Foundations of Computer Science', 4, 'THEORY', 'CA', 'CLASSROOM', 3, 1),
                    ('CA102', 'Data Structures & Algorithms with C', 4, 'THEORY', 'CA', 'CLASSROOM', 3, 1),
                    ('CA103', 'Computer Organization & Operating Systems', 3, 'THEORY', 'CA', 'CLASSROOM', 3, 1),
                    ('CA104', 'Data Structures Lab', 2, 'LAB', 'CA', 'COMPUTER_LAB', 1, 3),
                ],
                2: [
                    ('CA151', 'Object Oriented Programming with C++', 4, 'THEORY', 'CA', 'CLASSROOM', 3, 1),
                    ('CA152', 'Database Management Systems & SQL', 4, 'THEORY', 'CA', 'CLASSROOM', 3, 1),
                    ('CA153', 'Computer Networks & Internet Technologies', 3, 'THEORY', 'CA', 'CLASSROOM', 3, 1),
                    ('CA154', 'DBMS and C++ Lab', 2, 'LAB', 'CA', 'COMPUTER_LAB', 1, 3),
                ],
                3: [
                    ('CA201', 'Java Enterprise & J2EE Architecture', 4, 'THEORY', 'CA', 'CLASSROOM', 3, 1),
                    ('CA202', 'Software Engineering & Design Patterns', 4, 'THEORY', 'CA', 'CLASSROOM', 3, 1),
                    ('CA203', 'Python Programming for Data Science', 3, 'THEORY', 'CA', 'CLASSROOM', 3, 1),
                    ('CA204', 'Advanced Java Programming Lab', 2, 'LAB', 'CA', 'COMPUTER_LAB', 1, 3),
                ],
                4: [
                    ('CA251', 'Full Stack Web Development (MERN)', 4, 'THEORY', 'CA', 'CLASSROOM', 3, 1),
                    ('CA252', 'Cloud Computing and Microservices', 4, 'THEORY', 'CA', 'CLASSROOM', 3, 1),
                    ('CA253', 'Information Security & Cryptography', 3, 'THEORY', 'CA', 'CLASSROOM', 3, 1),
                    ('CA254', 'Full Stack Development Lab', 2, 'LAB', 'CA', 'COMPUTER_LAB', 1, 3),
                ],
                5: [
                    ('CA301', 'Machine Learning and Deep Learning', 4, 'THEORY', 'CA', 'CLASSROOM', 3, 1),
                    ('CA302', 'Mobile Application Development (Flutter)', 4, 'THEORY', 'CA', 'CLASSROOM', 3, 1),
                    ('CA303', 'Mobile App Development Lab', 2, 'LAB', 'CA', 'COMPUTER_LAB', 1, 3),
                ],
                6: [
                    ('CA351', 'Major Industrial Project & Internship', 16, 'PROJECT', 'CA', 'SEMINAR_HALL', 1, 2),
                ],
            },
            'MTECH_CSE': {
                1: [
                    ('CS501', 'Advanced Data Structures & Algorithms', 4, 'THEORY', 'CSE', 'CLASSROOM', 3, 1),
                    ('CS502', 'Advanced Computer Architecture', 4, 'THEORY', 'CSE', 'CLASSROOM', 3, 1),
                    ('CS503', 'Data Science and Predictive Analytics', 3, 'THEORY', 'CSE', 'CLASSROOM', 3, 1),
                    ('CS504', 'Advanced Computing Laboratory', 2, 'LAB', 'CSE', 'COMPUTER_LAB', 1, 3),
                ],
                2: [
                    ('CS551', 'Distributed Database Systems', 4, 'THEORY', 'CSE', 'CLASSROOM', 3, 1),
                    ('CS552', 'Deep Neural Networks & Representation', 4, 'THEORY', 'CSE', 'CLASSROOM', 3, 1),
                    ('CS553', 'High Performance Computing (GPU/CUDA)', 3, 'THEORY', 'CSE', 'CLASSROOM', 3, 1),
                    ('CS554', 'High Performance Computing Lab', 2, 'LAB', 'CSE', 'COMPUTER_LAB', 1, 3),
                ],
                3: [
                    ('CS601', 'Dissertation Phase - I (Research Thesis)', 10, 'PROJECT', 'CSE', 'SEMINAR_HALL', 1, 2),
                    ('CS602', 'Comprehensive Research Seminar', 2, 'SEMINAR', 'CSE', 'SEMINAR_HALL', 1, 1),
                ],
                4: [
                    ('CS651', 'Dissertation Phase - II & Final Defense', 14, 'PROJECT', 'CSE', 'SEMINAR_HALL', 1, 2),
                ],
            },
            'MSC_PHY': {
                1: [
                    ('PH4101', 'Classical Mechanics', 4, 'THEORY', 'PHY', 'CLASSROOM', 3, 1),
                    ('PH4102', 'Mathematical Physics', 4, 'THEORY', 'PHY', 'CLASSROOM', 3, 1),
                    ('PH4103', 'Quantum Mechanics - I', 4, 'THEORY', 'PHY', 'CLASSROOM', 3, 1),
                    ('PH4104', 'Electronics & Instrumentation', 3, 'THEORY', 'PHY', 'CLASSROOM', 3, 1),
                    ('PH4105', 'General Physics Laboratory - I', 2, 'LAB', 'PHY', 'CLASSROOM', 1, 3),
                ],
                2: [
                    ('PH4201', 'Quantum Mechanics - II', 4, 'THEORY', 'PHY', 'CLASSROOM', 3, 1),
                    ('PH4202', 'Statistical Mechanics', 4, 'THEORY', 'PHY', 'CLASSROOM', 3, 1),
                    ('PH4203', 'Electrodynamics & Plasma Physics', 4, 'THEORY', 'PHY', 'CLASSROOM', 3, 1),
                    ('PH4204', 'Solid State Physics', 3, 'THEORY', 'PHY', 'CLASSROOM', 3, 1),
                    ('PH4205', 'Optics & Modern Physics Laboratory', 2, 'LAB', 'PHY', 'CLASSROOM', 1, 3),
                ],
                3: [
                    ('PH5101', 'Nuclear & Particle Physics', 4, 'THEORY', 'PHY', 'CLASSROOM', 3, 1),
                    ('PH5102', 'Atomic & Molecular Spectroscopy', 4, 'THEORY', 'PHY', 'CLASSROOM', 3, 1),
                    ('PH5103', 'Condensed Matter Physics', 3, 'THEORY', 'PHY', 'CLASSROOM', 3, 1),
                    ('PH5104', 'Computational Physics & Numerical Methods', 3, 'THEORY', 'PHY', 'CLASSROOM', 3, 1),
                    ('PH5105', 'Advanced Physics Lab', 2, 'LAB', 'PHY', 'CLASSROOM', 1, 3),
                ],
                4: [
                    ('PH5201', 'Laser Physics & Nonlinear Optics', 4, 'THEORY', 'PHY', 'CLASSROOM', 3, 1),
                    ('PH5202', 'Nanomaterials & Characterization', 3, 'THEORY', 'PHY', 'CLASSROOM', 3, 1),
                    ('PH5203', 'M.Sc. Dissertation & Project Work', 6, 'PROJECT', 'PHY', 'SEMINAR_HALL', 1, 3),
                    ('PH5204', 'Comprehensive Viva Voce & Seminar', 2, 'SEMINAR', 'PHY', 'SEMINAR_HALL', 1, 1),
                ],
            },
            'MSC_CHEM': {
                1: [
                    ('CH4101', 'Advanced Inorganic Chemistry - I', 4, 'THEORY', 'CHEM', 'CLASSROOM', 3, 1),
                    ('CH4102', 'Organic Reaction Mechanisms', 4, 'THEORY', 'CHEM', 'CLASSROOM', 3, 1),
                    ('CH4103', 'Quantum Chemistry & Thermodynamics', 4, 'THEORY', 'CHEM', 'CLASSROOM', 3, 1),
                    ('CH4104', 'Analytical Chemistry Principles', 3, 'THEORY', 'CHEM', 'CLASSROOM', 3, 1),
                    ('CH4105', 'Inorganic & Analytical Chemistry Lab', 2, 'LAB', 'CHEM', 'CLASSROOM', 1, 3),
                ],
                2: [
                    ('CH4201', 'Coordination & Organometallic Chemistry', 4, 'THEORY', 'CHEM', 'CLASSROOM', 3, 1),
                    ('CH4202', 'Advanced Organic Synthesis & Stereochemistry', 4, 'THEORY', 'CHEM', 'CLASSROOM', 3, 1),
                    ('CH4203', 'Chemical Kinetics & Electrochemistry', 4, 'THEORY', 'CHEM', 'CLASSROOM', 3, 1),
                    ('CH4204', 'Molecular Spectroscopy', 3, 'THEORY', 'CHEM', 'CLASSROOM', 3, 1),
                    ('CH4205', 'Organic Chemistry Laboratory', 2, 'LAB', 'CHEM', 'CLASSROOM', 1, 3),
                ],
                3: [
                    ('CH5101', 'Bio-inorganic & Supramolecular Chemistry', 4, 'THEORY', 'CHEM', 'CLASSROOM', 3, 1),
                    ('CH5102', 'Natural Products & Medicinal Chemistry', 4, 'THEORY', 'CHEM', 'CLASSROOM', 3, 1),
                    ('CH5103', 'Polymer Chemistry & Materials Science', 3, 'THEORY', 'CHEM', 'CLASSROOM', 3, 1),
                    ('CH5104', 'Computational & Green Chemistry', 3, 'THEORY', 'CHEM', 'CLASSROOM', 3, 1),
                    ('CH5105', 'Physical Chemistry Laboratory', 2, 'LAB', 'CHEM', 'CLASSROOM', 1, 3),
                ],
                4: [
                    ('CH5201', 'Environmental Chemistry & Toxicology', 3, 'THEORY', 'CHEM', 'CLASSROOM', 3, 1),
                    ('CH5202', 'Advanced Spectroscopy & Instrumental Analysis', 3, 'THEORY', 'CHEM', 'CLASSROOM', 3, 1),
                    ('CH5203', 'M.Sc. Research Project / Dissertation', 6, 'PROJECT', 'CHEM', 'SEMINAR_HALL', 1, 3),
                    ('CH5204', 'Seminar & Comprehensive Viva', 2, 'SEMINAR', 'CHEM', 'SEMINAR_HALL', 1, 1),
                ],
            },
            'MSC_MATH': {
                1: [
                    ('MA4101', 'Real Analysis & Measure Theory', 4, 'THEORY', 'MATH', 'CLASSROOM', 3, 1),
                    ('MA4102', 'Abstract Algebra & Group Theory', 4, 'THEORY', 'MATH', 'CLASSROOM', 3, 1),
                    ('MA4103', 'Ordinary & Partial Differential Equations', 4, 'THEORY', 'MATH', 'CLASSROOM', 3, 1),
                    ('MA4104', 'Mathematical Statistics & Probability', 3, 'THEORY', 'MATH', 'CLASSROOM', 3, 1),
                    ('MA4105', 'Mathematical Computing Lab (Python/MATLAB)', 2, 'LAB', 'MATH', 'COMPUTER_LAB', 1, 3),
                ],
                2: [
                    ('MA4201', 'Complex Analysis', 4, 'THEORY', 'MATH', 'CLASSROOM', 3, 1),
                    ('MA4202', 'Linear Algebra & Matrix Theory', 4, 'THEORY', 'MATH', 'CLASSROOM', 3, 1),
                    ('MA4203', 'Numerical Analysis & Scientific Computing', 4, 'THEORY', 'MATH', 'CLASSROOM', 3, 1),
                    ('MA4204', 'Topology & Functional Analysis - I', 3, 'THEORY', 'MATH', 'CLASSROOM', 3, 1),
                    ('MA4205', 'Numerical Analysis Lab', 2, 'LAB', 'MATH', 'COMPUTER_LAB', 1, 3),
                ],
                3: [
                    ('MA5101', 'Functional Analysis - II', 4, 'THEORY', 'MATH', 'CLASSROOM', 3, 1),
                    ('MA5102', 'Operations Research & Optimization Techniques', 4, 'THEORY', 'MATH', 'CLASSROOM', 3, 1),
                    ('MA5103', 'Differential Geometry & Tensor Calculus', 3, 'THEORY', 'MATH', 'CLASSROOM', 3, 1),
                    ('MA5104', 'Number Theory & Cryptography', 3, 'THEORY', 'MATH', 'CLASSROOM', 3, 1),
                    ('MA5105', 'Statistical Computing & Optimization Lab', 2, 'LAB', 'MATH', 'COMPUTER_LAB', 1, 3),
                ],
                4: [
                    ('MA5201', 'Fluid Dynamics & Continuum Mechanics', 3, 'THEORY', 'MATH', 'CLASSROOM', 3, 1),
                    ('MA5202', 'Financial Mathematics & Stochastic Processes', 3, 'THEORY', 'MATH', 'CLASSROOM', 3, 1),
                    ('MA5203', 'M.Sc. Project Dissertation', 6, 'PROJECT', 'MATH', 'SEMINAR_HALL', 1, 3),
                    ('MA5204', 'Comprehensive Seminar & Defense', 2, 'SEMINAR', 'MATH', 'SEMINAR_HALL', 1, 1),
                ],
            },
        }

        course_obj_map = {}
        curriculum_map = {}
        total_courses_created = 0
        prof_rotation_idx = {}

        for b_code, sem_dict in branch_curriculum_catalog.items():
            branch_obj = branch_map[b_code]
            for sem_no, subjects in sem_dict.items():
                for (c_code, c_name, cr, c_type, dept_code, pref_room, w_meet, dur) in subjects:
                    dept_obj = dept_map[dept_code]

                    # Assign a professor from the subject department
                    pool = dept_profs.get(dept_code) or dept_profs['CSE']
                    curr_idx = prof_rotation_idx.get(dept_code, 0)
                    assigned_email = pool[curr_idx % len(pool)]
                    prof_rotation_idx[dept_code] = curr_idx + 1
                    assigned_prof_user = prof_user_map[assigned_email]

                    # Create Course
                    course, _ = Course.objects.update_or_create(
                        code=c_code,
                        defaults={
                            'name': c_name,
                            'credit': cr,
                            'course_type': c_type,
                            'department': dept_obj,
                            'branch': branch_obj,
                            'semester': sem_no,
                            'professor': assigned_prof_user,
                            'is_active': True,
                        }
                    )
                    course_obj_map[c_code] = course
                    total_courses_created += 1

                    # CourseDeliveryRule
                    CourseDeliveryRule.objects.update_or_create(
                        course=course,
                        defaults={
                            'weekly_meetings': w_meet,
                            'duration_slots': dur,
                            'preferred_room_type': pref_room,
                        }
                    )

                    # CurriculumItem
                    ci, _ = CurriculumItem.objects.update_or_create(
                        branch=branch_obj,
                        semester_no=sem_no,
                        course=course,
                        defaults={'is_elective': False, 'is_active': True}
                    )
                    curriculum_map[(b_code, sem_no, c_code)] = ci

        self.stdout.write(self.style.SUCCESS(
            f"[OK] {total_courses_created} Courses, Delivery Rules & Curriculum Items created across all semesters"
        ))

        # -------------------------------------------------------------------------
        # 8. COHORTS & INSTRUCTION GROUPS FOR ALL SEMESTERS (ODD & EVEN)
        # -------------------------------------------------------------------------
        cohort_map = {}   # (term_id, branch_code, sem, sec) -> Cohort
        groups_map = {}   # (cohort, group_code) -> InstructionGroup
        cohort_count = 0

        # Create cohorts across both current terms: Odd Term and Even Term
        active_terms = [current_odd_term, current_even_term]

        for term in active_terms:
            cycle = term.term_type  # 'ODD' or 'EVEN'
            for b_code, branch_obj in branch_map.items():
                max_sems = branch_obj.max_semesters
                for sem in range(1, max_sems + 1):
                    # Check cycle match
                    if cycle == 'ODD' and sem % 2 == 0:
                        continue
                    if cycle == 'EVEN' and sem % 2 == 1:
                        continue

                    # Sections: A and B for CSE/ECE/ME; A for others
                    sections = ['A', 'B'] if b_code in ['BTECH_CSE', 'BTECH_ECE', 'BTECH_ME'] else ['A']
                    for sec in sections:
                        cohort, _ = Cohort.objects.update_or_create(
                            branch=branch_obj,
                            term=term,
                            semester_no=sem,
                            section_code=sec,
                            defaults={'student_count': 60, 'is_active': True}
                        )
                        cohort_map[(term.id, b_code, sem, sec)] = cohort
                        cohort_count += 1

                        # Entire Section group
                        all_grp, _ = InstructionGroup.objects.update_or_create(
                            cohort=cohort,
                            code='ALL',
                            defaults={'name': 'Entire Section', 'size': 60, 'is_active': True}
                        )
                        groups_map[(cohort, 'ALL')] = all_grp

                        # Lab Subgroups: L1, L2
                        for l_code, l_name in [('L1', 'Lab Batch 1'), ('L2', 'Lab Batch 2')]:
                            grp_code = f"{sem}{sec}-{l_code}"
                            ig, _ = InstructionGroup.objects.update_or_create(
                                cohort=cohort,
                                code=grp_code,
                                defaults={'name': l_name, 'size': 30, 'is_active': True}
                            )
                            groups_map[(cohort, grp_code)] = ig

        self.stdout.write(self.style.SUCCESS(f"[OK] {cohort_count} Cohorts and Lab Groups seeded for Odd and Even Terms"))

        # -------------------------------------------------------------------------
        # 9. COURSE OFFERINGS & TEACHING ASSIGNMENTS (For All Cohorts & Semesters)
        # -------------------------------------------------------------------------
        offering_count = 0
        assignment_count = 0

        for (term_id, b_code, sem, sec), cohort in cohort_map.items():
            relevant_items = [
                ci for (b, s, c), ci in curriculum_map.items()
                if b == b_code and s == sem
            ]

            for ci in relevant_items:
                offering, _ = CourseOffering.objects.update_or_create(
                    term_id=term_id,
                    cohort=cohort,
                    curriculum_item=ci,
                    defaults={'is_active': True}
                )
                offering_count += 1

                assigned_prof = ci.course.professor or admin_user

                if ci.course.course_type == Course.CourseType.LAB:
                    cohort_subgroups = [
                        g for (coh, code), g in groups_map.items()
                        if coh == cohort and code != 'ALL'
                    ]
                    for grp in cohort_subgroups:
                        TeachingAssignment.objects.update_or_create(
                            course_offering=offering,
                            professor=assigned_prof,
                            instruction_group=grp,
                            defaults={'is_primary': True, 'is_active': True}
                        )
                        assignment_count += 1
                else:
                    TeachingAssignment.objects.update_or_create(
                        course_offering=offering,
                        professor=assigned_prof,
                        instruction_group=None,
                        defaults={'is_primary': True, 'is_active': True}
                    )
                    assignment_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"[OK] {offering_count} Course Offerings & {assignment_count} Teaching Assignments linked"
        ))

        # -------------------------------------------------------------------------
        # 10. PUBLISHED MASTER TIMETABLE VERSIONS & MEETINGS
        # -------------------------------------------------------------------------
        # Create published schedule for 2026-27 Odd Semester
        master_version_2026_odd, _ = ScheduleVersion.objects.update_or_create(
            term=current_odd_term,
            version_no=1,
            defaults={
                'name': 'NIT JSR Academic Master Schedule (2026-27 Autumn)',
                'status': ScheduleVersion.Status.PUBLISHED,
                'notes': 'Official published timetable for Autumn Semester 2026-27 approved by Academic Administration.',
                'created_by': admin_user,
            }
        )

        # Create published schedule for previous year 2025-26 Odd Semester
        term_2025_odd = terms_map[('2025-26', 'ODD')]
        master_version_2025_odd, _ = ScheduleVersion.objects.update_or_create(
            term=term_2025_odd,
            version_no=1,
            defaults={
                'name': 'NIT JSR Academic Master Schedule (2025-26 Autumn)',
                'status': ScheduleVersion.Status.PUBLISHED,
                'notes': 'Historical archived published timetable for Autumn Semester 2025-26.',
                'created_by': admin_user,
            }
        )

        # Create Draft schedule for 2026-27 Even Semester
        draft_version_2026_even, _ = ScheduleVersion.objects.update_or_create(
            term=current_even_term,
            version_no=1,
            defaults={
                'name': 'NIT JSR Spring 2026-27 Planning Draft',
                'status': ScheduleVersion.Status.DRAFT,
                'notes': 'Working draft schedule for Spring Semester 2026-27.',
                'created_by': admin_user,
            }
        )

        # Place realistic scheduled meetings for 2026-27 Odd Master Version
        scheduled_items = [
            ('CS301', 'BTECH_CSE', 5, 'A', None, 2, 3, 1, 'LH-101'),
            ('CS301', 'BTECH_CSE', 5, 'A', None, 4, 3, 1, 'LH-101'),
            ('CS301', 'BTECH_CSE', 5, 'A', None, 5, 2, 1, 'LH-101'),
            ('CS305', 'BTECH_CSE', 5, 'A', '5A-L1', 2, 5, 3, 'CS-LAB1'),
            ('CS305', 'BTECH_CSE', 5, 'A', '5A-L2', 4, 5, 3, 'CS-LAB1'),
            ('CS201', 'BTECH_CSE', 3, 'A', None, 1, 3, 1, 'LH-101'),
            ('CS201', 'BTECH_CSE', 3, 'A', None, 3, 3, 1, 'LH-101'),
            ('CS201', 'BTECH_CSE', 3, 'A', None, 5, 3, 1, 'LH-101'),
            ('CS205', 'BTECH_CSE', 3, 'A', '3A-L1', 1, 5, 3, 'CC-LAB-1'),
            ('CS205', 'BTECH_CSE', 3, 'A', '3A-L2', 3, 5, 3, 'CC-LAB-1'),
            ('CS202', 'BTECH_CSE', 3, 'A', None, 1, 4, 1, 'LH-101'),
            ('CS202', 'BTECH_CSE', 3, 'A', None, 2, 4, 1, 'LH-101'),
            ('CS202', 'BTECH_CSE', 3, 'A', None, 4, 4, 1, 'LH-101'),
            ('CS302', 'BTECH_CSE', 5, 'A', None, 1, 1, 1, 'LH-101'),
            ('CS302', 'BTECH_CSE', 5, 'A', None, 3, 1, 1, 'LH-101'),
            ('CS302', 'BTECH_CSE', 5, 'A', None, 5, 1, 1, 'LH-101'),
            ('CS203', 'BTECH_CSE', 3, 'A', None, 2, 1, 1, 'LH-101'),
            ('CS203', 'BTECH_CSE', 3, 'A', None, 3, 4, 1, 'LH-101'),
            ('CS204', 'BTECH_CSE', 3, 'A', None, 1, 1, 1, 'LH-102'),
            ('CS204', 'BTECH_CSE', 3, 'A', None, 2, 2, 1, 'LH-102'),
            ('EC201', 'BTECH_ECE', 3, 'A', None, 1, 3, 1, 'EC-LH1'),
            ('EC201', 'BTECH_ECE', 3, 'A', None, 2, 3, 1, 'EC-LH1'),
            ('EC202', 'BTECH_ECE', 3, 'A', None, 1, 4, 1, 'EC-LH1'),
            ('EC202', 'BTECH_ECE', 3, 'A', None, 3, 3, 1, 'EC-LH1'),
            ('EC205', 'BTECH_ECE', 3, 'A', '3A-L1', 2, 5, 3, 'EC-LAB1'),
            ('EE201', 'BTECH_EE', 3, 'A', None, 1, 2, 1, 'EE-LH1'),
            ('EE201', 'BTECH_EE', 3, 'A', None, 3, 2, 1, 'EE-LH1'),
            ('EE202', 'BTECH_EE', 3, 'A', None, 2, 3, 1, 'EE-LH1'),
            ('EE204', 'BTECH_EE', 3, 'A', '3A-L1', 1, 5, 3, 'EE-LAB1'),
            ('ME201', 'BTECH_ME', 3, 'A', None, 1, 1, 1, 'ME-LH1'),
            ('ME201', 'BTECH_ME', 3, 'A', None, 3, 1, 1, 'ME-LH1'),
            ('ME202', 'BTECH_ME', 3, 'A', None, 2, 2, 1, 'ME-LH1'),
            ('ME204', 'BTECH_ME', 3, 'A', '3A-L1', 2, 5, 3, 'ME-CAD'),
            ('CE201', 'BTECH_CE', 3, 'A', None, 1, 2, 1, 'CE-LH1'),
            ('CE202', 'BTECH_CE', 3, 'A', None, 2, 3, 1, 'CE-LH1'),
            ('CE204', 'BTECH_CE', 3, 'A', '3A-L1', 3, 5, 3, 'CE-LAB1'),
            ('CA201', 'MCA', 3, 'A', None, 1, 2, 1, 'CS-LH1'),
            ('CA201', 'MCA', 3, 'A', None, 3, 2, 1, 'CS-LH1'),
            ('CA204', 'MCA', 3, 'A', '3A-L1', 2, 5, 3, 'CC-LAB-2'),
        ]

        ScheduledMeeting.objects.filter(schedule_version=master_version_2026_odd).delete()
        ProfessorSlotReservation.objects.filter(schedule_version=master_version_2026_odd).delete()
        RoomSlotReservation.objects.filter(schedule_version=master_version_2026_odd).delete()
        GroupSlotReservation.objects.filter(schedule_version=master_version_2026_odd).delete()

        created_meetings = 0
        for (c_code, b_code, sem, sec, grp_code, wday, s_slot, dur, r_no) in scheduled_items:
            cohort = cohort_map.get((current_odd_term.id, b_code, sem, sec))
            ci = curriculum_map.get((b_code, sem, c_code))
            if not cohort or not ci:
                continue

            offering = CourseOffering.objects.filter(term=current_odd_term, cohort=cohort, curriculum_item=ci).first()
            if not offering:
                continue

            target_group = None
            if grp_code:
                target_group = groups_map.get((cohort, grp_code))
                ta = TeachingAssignment.objects.filter(course_offering=offering, instruction_group=target_group).first()
            else:
                ta = TeachingAssignment.objects.filter(course_offering=offering, instruction_group__isnull=True).first()

            if not ta:
                ta = TeachingAssignment.objects.filter(course_offering=offering).first()
            if not ta:
                continue

            room_obj = Room.objects.filter(room_no=r_no).first()
            if not room_obj:
                continue

            meeting = ScheduledMeeting.objects.create(
                schedule_version=master_version_2026_odd,
                teaching_assignment=ta,
                weekday=wday,
                start_slot=s_slot,
                duration_slots=dur,
                room=room_obj,
                created_by=admin_user,
            )

            assigned_groups = []
            if target_group:
                assigned_groups.append(target_group)
            elif (cohort, 'ALL') in groups_map:
                assigned_groups.append(groups_map[(cohort, 'ALL')])

            for grp in assigned_groups:
                MeetingInstructionGroup.objects.get_or_create(scheduled_meeting=meeting, instruction_group=grp)

            for slot in range(s_slot, s_slot + dur):
                ProfessorSlotReservation.objects.get_or_create(
                    schedule_version=master_version_2026_odd,
                    professor=ta.professor,
                    weekday=wday,
                    slot_no=slot,
                    defaults={'scheduled_meeting': meeting}
                )
                RoomSlotReservation.objects.get_or_create(
                    schedule_version=master_version_2026_odd,
                    room=room_obj,
                    weekday=wday,
                    slot_no=slot,
                    defaults={'scheduled_meeting': meeting}
                )
                for grp in assigned_groups:
                    GroupSlotReservation.objects.get_or_create(
                        schedule_version=master_version_2026_odd,
                        instruction_group=grp,
                        weekday=wday,
                        slot_no=slot,
                        defaults={'scheduled_meeting': meeting}
                    )

            created_meetings += 1

        self.stdout.write(self.style.SUCCESS(
            f"[OK] {created_meetings} Scheduled Meetings configured for Published Master Version (2026-27 Autumn)"
        ))

        self.stdout.write(self.style.SUCCESS("""
=============================================================================
NIT JSR Academic Catalog & Timetable Data Successfully Populated!
=============================================================================
Highlights:
  - 3 Academic Years (2024-25, 2025-26, 2026-27) with Odd and Even Semesters
  - Complete curriculum subjects across ALL semesters (1 through 8) for:
      * B.Tech CSE (Sem 1 to 8)
      * B.Tech ECE (Sem 1 to 8)
      * B.Tech EE (Sem 1 to 8)
      * B.Tech ME (Sem 1 to 8)
      * B.Tech CE (Sem 1 to 8)
      * B.Tech MME (Sem 1 to 8)
      * B.Tech PIE (Sem 1 to 8)
      * MCA (Sem 1 to 6)
      * M.Tech CSE (Sem 1 to 4)
  - Dedicated Professors mapped for each course
  - Published and Draft Master Schedules available per academic year
=============================================================================
        """))
