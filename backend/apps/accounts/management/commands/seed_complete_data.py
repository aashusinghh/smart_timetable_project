"""
Builds one complete, internally consistent demo dataset for every screen.

    python manage.py seed_complete_data

It wipes ALL existing data first (users included), then creates:
  * roles, 8 daily time slots, an academic year with an Odd and an Even term
  * a campus with lecture halls, computer labs, electronics labs and a seminar hall
  * 4 departments, 4 programmes (MCA, B.Tech CSE, B.Tech ECE, M.Tech CSE)
  * a full course catalogue (every semester of every programme) with delivery rules
  * cohorts for every running semester, lab batches, course offerings
  * professors with profiles, teaching assignments and a few unavailability blocks
  * a clash-free timetable for both terms (generated with the CP-SAT scheduler)
    - Odd term: a PUBLISHED version plus an editable DRAFT copy
    - Even term: an editable DRAFT
  * holidays and a couple of date overrides
  * the quick-login accounts shown on the login page
"""
from datetime import date, time

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import ProfessorProfile, Role, User, UserRoleAssignment
from apps.academics.models import (
    AcademicTerm,
    AcademicYear,
    Branch,
    Cohort,
    Course,
    CourseDeliveryRule,
    CourseOffering,
    CurriculumItem,
    Department,
    InstructionGroup,
    TeachingAssignment,
    TimeSlot,
)
from apps.facilities.models import Building, Campus, Room, RoomUnavailability
from apps.faculty.models import ProfessorUnavailability
from apps.scheduler.services.generator import TimetableGenerator
from apps.timetable.models import DateOverride, HolidayCalendar, ScheduledMeeting, ScheduleVersion
from apps.timetable.services.reservation_service import TimetableReservationService

FACULTY_PASSWORD = 'Password@123'

# ---------------------------------------------------------------------------
# Course catalogue: programme -> semester -> [(code, name, type)]
# T = theory (3 credits, 3 x 1h per week), L = lab (2 credits, 2 x 3h per week)
# ---------------------------------------------------------------------------
T, L = 'THEORY', 'LAB'
CATALOGUE = {
    'MCA': {
        1: [('MCA101', 'Programming in C', T), ('MCA102', 'Discrete Mathematics', T),
            ('MCA103', 'Computer Organization and Architecture', T), ('MCA104', 'Accounting and Financial Management', T),
            ('MCA105', 'C Programming Lab', L)],
        2: [('MCA201', 'Data Structures', T), ('MCA202', 'Object Oriented Programming with Java', T),
            ('MCA203', 'Operating Systems', T), ('MCA204', 'Probability and Statistics', T),
            ('MCA205', 'Data Structures and Java Lab', L)],
        3: [('MCA301', 'Database Management Systems', T), ('MCA302', 'Computer Networks', T),
            ('MCA303', 'Design and Analysis of Algorithms', T), ('MCA304', 'Software Engineering', T),
            ('MCA305', 'DBMS and Networks Lab', L)],
        4: [('MCA401', 'Machine Learning', T), ('MCA402', 'Web Technologies', T),
            ('MCA403', 'Cloud Computing', T), ('MCA404', 'Information Security', T),
            ('MCA405', 'Web and ML Lab', L)],
    },
    'MTECH_CSE': {
        1: [('MCS101', 'Advanced Data Structures', T), ('MCS102', 'Advanced Computer Architecture', T),
            ('MCS103', 'Mathematical Foundations of Computing', T), ('MCS104', 'Research Methodology', T),
            ('MCS105', 'Advanced Programming Lab', L)],
        2: [('MCS201', 'Advanced Algorithms', T), ('MCS202', 'Distributed Systems', T),
            ('MCS203', 'Deep Learning', T), ('MCS204', 'Big Data Analytics', T),
            ('MCS205', 'Deep Learning Lab', L)],
        3: [('MCS301', 'Natural Language Processing', T), ('MCS302', 'Blockchain Technologies', T),
            ('MCS303', 'Cyber Security', T), ('MCS304', 'Internet of Things', T),
            ('MCS305', 'Research Lab', L)],
        4: [('MCS401', 'Advanced Topics in AI', T), ('MCS402', 'Quantum Computing', T),
            ('MCS403', 'High Performance Computing', T), ('MCS404', 'Technical Writing', T),
            ('MCS405', 'Dissertation Lab', L)],
    },
    'BTECH_CSE': {
        1: [('CS101', 'Engineering Mathematics I', T), ('CS102', 'Engineering Physics', T),
            ('CS103', 'Programming for Problem Solving', T), ('CS104', 'Basic Electrical Engineering', T),
            ('CS105', 'Programming Lab', L)],
        2: [('CS201', 'Engineering Mathematics II', T), ('CS202', 'Engineering Chemistry', T),
            ('CS203', 'Digital Logic Design', T), ('CS204', 'English Communication', T),
            ('CS205', 'Digital Logic Lab', L)],
        3: [('CS301', 'Data Structures and Algorithms', T), ('CS302', 'Discrete Structures', T),
            ('CS303', 'Object Oriented Programming', T), ('CS304', 'Computer Organization', T),
            ('CS305', 'Data Structures Lab', L)],
        4: [('CS401', 'Design and Analysis of Algorithms', T), ('CS402', 'Operating Systems', T),
            ('CS403', 'Database Systems', T), ('CS404', 'Theory of Computation', T),
            ('CS405', 'Operating Systems and DBMS Lab', L)],
        5: [('CS501', 'Computer Networks', T), ('CS502', 'Compiler Design', T),
            ('CS503', 'Software Engineering', T), ('CS504', 'Artificial Intelligence', T),
            ('CS505', 'Networks and Compiler Lab', L)],
        6: [('CS601', 'Machine Learning', T), ('CS602', 'Computer Graphics', T),
            ('CS603', 'Distributed Computing', T), ('CS604', 'Information Security', T),
            ('CS605', 'Machine Learning Lab', L)],
        7: [('CS701', 'Cloud Computing', T), ('CS702', 'Data Mining', T),
            ('CS703', 'Natural Language Processing', T), ('CS704', 'Management for Engineers', T),
            ('CS705', 'Project Lab I', L)],
        8: [('CS801', 'Big Data Systems', T), ('CS802', 'Mobile Computing', T),
            ('CS803', 'Human Computer Interaction', T), ('CS804', 'Professional Ethics', T),
            ('CS805', 'Project Lab II', L)],
    },
    'BTECH_ECE': {
        1: [('EC101', 'Engineering Mathematics I', T), ('EC102', 'Engineering Physics', T),
            ('EC103', 'Basic Electronics', T), ('EC104', 'Engineering Graphics', T),
            ('EC105', 'Basic Electronics Lab', L)],
        2: [('EC201', 'Engineering Mathematics II', T), ('EC202', 'Network Theory', T),
            ('EC203', 'Programming in C', T), ('EC204', 'Environmental Science', T),
            ('EC205', 'Circuits Lab', L)],
        3: [('EC301', 'Analog Electronic Circuits', T), ('EC302', 'Signals and Systems', T),
            ('EC303', 'Digital Electronics', T), ('EC304', 'Electromagnetic Theory', T),
            ('EC305', 'Analog and Digital Lab', L)],
        4: [('EC401', 'Analog Communication', T), ('EC402', 'Microprocessors and Microcontrollers', T),
            ('EC403', 'Control Systems', T), ('EC404', 'Linear Integrated Circuits', T),
            ('EC405', 'Microprocessor Lab', L)],
        5: [('EC501', 'Digital Communication', T), ('EC502', 'Digital Signal Processing', T),
            ('EC503', 'VLSI Design', T), ('EC504', 'Antennas and Wave Propagation', T),
            ('EC505', 'DSP and VLSI Lab', L)],
        6: [('EC601', 'Microwave Engineering', T), ('EC602', 'Embedded Systems', T),
            ('EC603', 'Information Theory and Coding', T), ('EC604', 'Computer Networks', T),
            ('EC605', 'Embedded Systems Lab', L)],
        7: [('EC701', 'Wireless Communication', T), ('EC702', 'Optical Communication', T),
            ('EC703', 'Radar Engineering', T), ('EC704', 'Management for Engineers', T),
            ('EC705', 'Communication Lab', L)],
        8: [('EC801', 'Satellite Communication', T), ('EC802', 'Machine Learning for Signals', T),
            ('EC803', 'MEMS and Sensors', T), ('EC804', 'Professional Ethics', T),
            ('EC805', 'Project Lab', L)],
    },
}

PROGRAMMES = [
    # (dept_code, dept_name, branch_code, branch_name, degree, max_semesters, sections, students)
    ('CA', 'Computer Applications', 'MCA', 'Master of Computer Applications', 'MCA', 4, ['A'], 60),
    ('CSE', 'Computer Science and Engineering', 'BTECH_CSE', 'B.Tech Computer Science and Engineering', 'B.Tech', 8, ['A', 'B'], 60),
    ('CSE', 'Computer Science and Engineering', 'MTECH_CSE', 'M.Tech Computer Science and Engineering', 'M.Tech', 4, ['A'], 30),
    ('ECE', 'Electronics and Communication Engineering', 'BTECH_ECE', 'B.Tech Electronics and Communication Engineering', 'B.Tech', 8, ['A'], 60),
]
EXTRA_DEPARTMENTS = [('MATH', 'Mathematics')]

# (email, full name, employee code, dept, designation)
FACULTY = [
    ('professor@university.edu', 'Dr. Sunita Sharma', 'CA-001', 'CA', 'Professor'),
    ('dkyadav.ca@university.edu', 'Dr. D. K. Yadav', 'CA-002', 'CA', 'Associate Professor'),
    ('pmishra.ca@university.edu', 'Dr. Pooja Mishra', 'CA-003', 'CA', 'Assistant Professor'),
    ('rverma.ca@university.edu', 'Dr. Rahul Verma', 'CA-004', 'CA', 'Assistant Professor'),
    ('dkumar.cse@university.edu', 'Dr. Dilip Kumar', 'CSE-001', 'CSE', 'Professor'),
    ('vkumar.cse@university.edu', 'Dr. Vinay Kumar', 'CSE-002', 'CSE', 'Associate Professor'),
    ('skumar.cse@university.edu', 'Dr. Sanjay Kumar', 'CSE-003', 'CSE', 'Assistant Professor'),
    ('bksingh.cse@university.edu', 'Dr. B. K. Singh', 'CSE-004', 'CSE', 'Professor'),
    ('sdutta.cse@university.edu', 'Dr. Subrata Dutta', 'CSE-005', 'CSE', 'Assistant Professor'),
    ('rkagrawal.cse@university.edu', 'Dr. R. K. Agrawal', 'CSE-006', 'CSE', 'Associate Professor'),
    ('kpatel.cse@university.edu', 'Dr. Kavita Patel', 'CSE-007', 'CSE', 'Assistant Professor'),
    ('aroy.cse@university.edu', 'Dr. Anirban Roy', 'CSE-008', 'CSE', 'Assistant Professor'),
    ('mjain.cse@university.edu', 'Dr. Meera Jain', 'CSE-009', 'CSE', 'Associate Professor'),
    ('sghosh.cse@university.edu', 'Dr. Sourav Ghosh', 'CSE-010', 'CSE', 'Assistant Professor'),
    ('nrao.cse@university.edu', 'Dr. Nandini Rao', 'CSE-011', 'CSE', 'Assistant Professor'),
    ('tsen.cse@university.edu', 'Dr. Tapas Sen', 'CSE-012', 'CSE', 'Professor'),
    ('kksingh.ece@university.edu', 'Dr. K. K. Singh', 'ECE-001', 'ECE', 'Professor'),
    ('rsinha.ece@university.edu', 'Dr. Rashmi Sinha', 'ECE-002', 'ECE', 'Associate Professor'),
    ('akumar.ece@university.edu', 'Dr. Amit Kumar', 'ECE-003', 'ECE', 'Assistant Professor'),
    ('bbhowmik.ece@university.edu', 'Dr. Basanta Bhowmik', 'ECE-004', 'ECE', 'Assistant Professor'),
    ('ppandey.ece@university.edu', 'Dr. Priya Pandey', 'ECE-005', 'ECE', 'Assistant Professor'),
    ('mdas.ece@university.edu', 'Dr. Manoj Das', 'ECE-006', 'ECE', 'Associate Professor'),
]
# Which faculty pool teaches each programme's courses.
TEACHING_DEPT = {'MCA': 'CA', 'BTECH_CSE': 'CSE', 'MTECH_CSE': 'CSE', 'BTECH_ECE': 'ECE'}

ROOMS = [
    # (building, room_no, name, type, capacity, floor)
    ('LHC', 'LH-101', 'Lecture Hall 101', 'CLASSROOM', 70, 1),
    ('LHC', 'LH-102', 'Lecture Hall 102', 'CLASSROOM', 70, 1),
    ('LHC', 'LH-103', 'Lecture Hall 103', 'CLASSROOM', 70, 1),
    ('LHC', 'LH-201', 'Lecture Hall 201', 'CLASSROOM', 70, 2),
    ('LHC', 'LH-202', 'Lecture Hall 202', 'CLASSROOM', 70, 2),
    ('LHC', 'LH-203', 'Lecture Hall 203', 'CLASSROOM', 70, 2),
    ('LHC', 'LH-301', 'Lecture Hall 301', 'CLASSROOM', 70, 3),
    ('LHC', 'LH-302', 'Lecture Hall 302', 'CLASSROOM', 70, 3),
    ('CA', 'CA-101', 'MCA Classroom 1', 'CLASSROOM', 65, 1),
    ('CA', 'CA-102', 'MCA Classroom 2', 'CLASSROOM', 65, 1),
    ('CA', 'CA-LAB1', 'MCA Programming Lab', 'COMPUTER_LAB', 64, 2),
    ('CC', 'CC-LAB1', 'Computer Centre Lab 1', 'COMPUTER_LAB', 64, 1),
    ('CC', 'CC-LAB2', 'Computer Centre Lab 2', 'COMPUTER_LAB', 64, 1),
    ('CC', 'CC-LAB3', 'Computer Centre Lab 3', 'COMPUTER_LAB', 64, 2),
    ('CC', 'CC-LAB4', 'AI and Data Lab', 'COMPUTER_LAB', 64, 2),
    ('CC', 'CC-LAB5', 'Networks and Systems Lab', 'COMPUTER_LAB', 64, 3),
    ('CA', 'CA-LAB2', 'MCA Project Lab', 'COMPUTER_LAB', 64, 2),
    ('ECE', 'EC-LAB1', 'Electronics Circuits Lab', 'ELECTRONICS_LAB', 64, 1),
    ('ECE', 'EC-LAB2', 'Communication and DSP Lab', 'ELECTRONICS_LAB', 64, 2),
    ('ECE', 'EC-LAB3', 'Embedded Systems Lab', 'ELECTRONICS_LAB', 64, 2),
    ('AUD', 'SH-1', 'Main Seminar Hall', 'SEMINAR_HALL', 200, 1),
]
BUILDINGS = [
    ('LHC', 'Lecture Hall Complex', 3),
    ('CA', 'Department of Computer Applications', 2),
    ('CC', 'Computer Centre', 2),
    ('ECE', 'Department of Electronics and Communication', 2),
    ('AUD', 'Auditorium Block', 1),
]


class Command(BaseCommand):
    help = 'Wipes the database and seeds one complete, consistent demo dataset for every screen.'

    def add_arguments(self, parser):
        parser.add_argument('--time-limit', type=int, default=60,
                            help='Seconds the timetable solver may spend per term (default 60).')
        parser.add_argument('--no-reset', action='store_true',
                            help='Do not wipe existing data first (not recommended).')

    def log(self, msg):
        self.stdout.write(self.style.SUCCESS(f'[OK] {msg}'))

    def handle(self, *args, **opts):
        if not opts['no_reset']:
            call_command('flush', interactive=False, verbosity=0)
            self.log('Old data removed')

        with transaction.atomic():
            ctx = self.seed_structure()
        for term in ctx['terms']:
            self.build_timetable(ctx, term, opts['time_limit'])
        with transaction.atomic():
            self.seed_calendar(ctx)
        self.print_summary()

    # ------------------------------------------------------------------
    def seed_structure(self):
        roles = {
            code: Role.objects.create(code=code, name=name, description=desc)
            for code, name, desc in [
                (Role.Code.SUPER_ADMIN, 'Super Administrator', 'Full university system access'),
                (Role.Code.BRANCH_COORDINATOR, 'Branch Coordinator', 'Plans the timetable for a branch'),
                (Role.Code.PROFESSOR, 'Professor', 'Faculty member'),
            ]
        }

        for no, (s, e, sess) in enumerate([
            (time(8, 30), time(9, 30), 'MORNING'), (time(9, 30), time(10, 30), 'MORNING'),
            (time(10, 30), time(11, 30), 'MORNING'), (time(11, 30), time(12, 30), 'MORNING'),
            (time(14, 0), time(15, 0), 'AFTERNOON'), (time(15, 0), time(16, 0), 'AFTERNOON'),
            (time(16, 0), time(17, 0), 'AFTERNOON'), (time(17, 0), time(18, 0), 'AFTERNOON'),
        ], start=1):
            TimeSlot.objects.create(slot_no=no, start_time=s, end_time=e, session=sess)
        self.log('Roles and 8 time slots')

        year = AcademicYear.objects.create(name='2026-27', start_date=date(2026, 7, 20),
                                           end_date=date(2027, 5, 31), is_current=True)
        odd = AcademicTerm.objects.create(academic_year=year, name='Odd Semester 2026-27', term_type='ODD',
                                          start_date=date(2026, 7, 20), end_date=date(2026, 12, 15))
        even = AcademicTerm.objects.create(academic_year=year, name='Even Semester 2026-27', term_type='EVEN',
                                           start_date=date(2027, 1, 4), end_date=date(2027, 5, 31))
        self.log('Academic year 2026-27 with Odd and Even terms')

        campus = Campus.objects.create(name='Main Campus', code='MAIN', address='University Road')
        bld = {c: Building.objects.create(campus=campus, code=c, name=n, floors_count=f) for c, n, f in BUILDINGS}
        rooms = {}
        for b, no, name, rtype, cap, floor in ROOMS:
            rooms[no] = Room.objects.create(building=bld[b], room_no=no, name=name, room_type=rtype,
                                            capacity=cap, floor=floor, has_projector=True)
        RoomUnavailability.objects.create(room=rooms['LH-302'], weekday=5, start_slot=5, end_slot=8,
                                          reason='Reserved for university seminars')
        self.log(f'{len(BUILDINGS)} buildings and {len(ROOMS)} rooms')

        depts = {}
        for dcode, dname, *_ in PROGRAMMES:
            if dcode not in depts:
                depts[dcode] = Department.objects.create(code=dcode, name=dname,
                                                         description=f'Department of {dname}')
        for dcode, dname in EXTRA_DEPARTMENTS:
            depts[dcode] = Department.objects.create(code=dcode, name=dname, description=f'Department of {dname}')
        branches = {}
        for dcode, _, bcode, bname, degree, max_sem, sections, students in PROGRAMMES:
            branches[bcode] = Branch.objects.create(department=depts[dcode], code=bcode, name=bname,
                                                    degree_name=degree, max_semesters=max_sem)
        self.log(f'{len(depts)} departments and {len(branches)} programmes')

        # Users -----------------------------------------------------------
        admin = User.objects.create_user('admin@university.edu', 'Admin@12345', 'System Administrator',
                                         employee_code='ADMIN-001', is_staff=True, is_superuser=True)
        UserRoleAssignment.objects.create(user=admin, role=roles[Role.Code.SUPER_ADMIN])
        coord = User.objects.create_user('coordinator@university.edu', 'Coord@12345', 'Prof. Anil Mehta',
                                         employee_code='COORD-001')
        for b in ('BTECH_CSE', 'MCA'):
            UserRoleAssignment.objects.create(user=coord, role=roles[Role.Code.BRANCH_COORDINATOR],
                                              branch=branches[b])
        ProfessorProfile.objects.create(user=coord, department=depts['CSE'], designation='Associate Professor',
                                        max_hours_per_day=4)
        UserRoleAssignment.objects.create(user=coord, role=roles[Role.Code.PROFESSOR])

        profs = {}
        for email, name, emp, dcode, desig in FACULTY:
            pw = 'Prof@12345' if email == 'professor@university.edu' else FACULTY_PASSWORD
            u = User.objects.create_user(email, pw, name, employee_code=emp)
            ProfessorProfile.objects.create(user=u, department=depts[dcode], designation=desig,
                                            max_hours_per_day=6)
            UserRoleAssignment.objects.create(user=u, role=roles[Role.Code.PROFESSOR])
            profs.setdefault(dcode, []).append(u)
        profs['CSE'].append(coord)
        ProfessorUnavailability.objects.create(professor=profs['CSE'][0], weekday=3, start_slot=5, end_slot=8,
                                               reason='Board of Studies meeting')
        ProfessorUnavailability.objects.create(professor=profs['ECE'][0], weekday=5, start_slot=1, end_slot=2,
                                               reason='Research committee')
        ProfessorUnavailability.objects.create(professor=profs['CA'][0], weekday=1, start_slot=7, end_slot=8,
                                               reason='Department administration')
        self.log(f'{User.objects.count()} users (1 admin, 1 coordinator, {len(FACULTY)} faculty)')

        # Courses and curriculum ------------------------------------------
        rr = {d: 0 for d in profs}
        for bcode, sems in CATALOGUE.items():
            branch = branches[bcode]
            pool_dept = TEACHING_DEPT[bcode]
            for sem, courses in sems.items():
                for code, name, ctype in courses:
                    pool = profs[pool_dept]
                    prof = pool[rr[pool_dept] % len(pool)]
                    rr[pool_dept] += 1
                    is_lab = ctype == L
                    course = Course.objects.create(
                        code=code, name=name, course_type=ctype, credit=2 if is_lab else 3,
                        department=branch.department, branch=branch, semester=sem, professor=prof,
                        description=f'{name} for {branch.degree_name} semester {sem}.')
                    CourseDeliveryRule.objects.create(
                        course=course, weekly_meetings=2 if is_lab else 3, duration_slots=3 if is_lab else 1,
                        preferred_room_type=('ELECTRONICS_LAB' if bcode == 'BTECH_ECE' else 'COMPUTER_LAB')
                        if is_lab else 'CLASSROOM')
                    CurriculumItem.objects.create(branch=branch, semester_no=sem, course=course)
        self.log(f'{Course.objects.count()} courses with delivery rules and curriculum')

        # Cohorts, groups, offerings, assignments --------------------------
        for term in (odd, even):
            parity = 1 if term.term_type == 'ODD' else 0
            for dcode, _, bcode, _, _, max_sem, sections, students in PROGRAMMES:
                branch = branches[bcode]
                for sem in range(1, max_sem + 1):
                    if sem % 2 != parity:
                        continue
                    for sec in sections:
                        cohort = Cohort.objects.create(branch=branch, term=term, semester_no=sem,
                                                       section_code=sec, student_count=students)
                        half = students // 2
                        InstructionGroup.objects.create(cohort=cohort, code='ALL', name='Entire Section',
                                                        size=students)
                        InstructionGroup.objects.create(cohort=cohort, code=f'{sem}{sec}-L1', name='Lab Batch 1',
                                                        size=half)
                        InstructionGroup.objects.create(cohort=cohort, code=f'{sem}{sec}-L2', name='Lab Batch 2',
                                                        size=students - half)
                        for item in CurriculumItem.objects.filter(branch=branch, semester_no=sem):
                            off = CourseOffering.objects.create(term=term, cohort=cohort, curriculum_item=item)
                            teacher = item.course.professor
                            if sec != 'A':
                                # Other sections get the next colleague, so no one teaches
                                # the same 6-hour lab twice a week.
                                pool = profs[TEACHING_DEPT[bcode]]
                                teacher = pool[(pool.index(teacher) + 5) % len(pool)]
                            TeachingAssignment.objects.create(course_offering=off, professor=teacher)
        self.log(f'{Cohort.objects.count()} cohorts, {CourseOffering.objects.count()} offerings, '
                 f'{TeachingAssignment.objects.count()} teaching assignments')
        return {'admin': admin, 'terms': [odd, even], 'odd': odd, 'even': even, 'rooms': rooms}

    # ------------------------------------------------------------------
    def build_timetable(self, ctx, term, time_limit):
        admin = ctx['admin']
        version = ScheduleVersion.objects.create(term=term, version_no=1, status='DRAFT',
                                                 name=f'Master Timetable - {term.name}', created_by=admin)
        result = TimetableGenerator(version, time_limit=time_limit, replace_existing=True).generate()
        proposed = result.get('proposed_meetings') or []
        if not proposed:
            raise CommandError(f'Scheduler found no timetable for {term.name}: {result.get("solver_status")} '
                               f'{result.get("unscheduled_offerings")}')
        all_proposed = list(proposed)

        def place(target, meetings=None):
            meetings = all_proposed if meetings is None else meetings
            placed = 0
            for m in meetings:
                asg = TeachingAssignment.objects.get(id=m['teaching_assignment_id'])
                try:
                    TimetableReservationService.save_meeting(
                        schedule_version=target, teaching_assignment=asg, weekday=m['weekday'],
                        start_slot=m['start_slot'], duration_slots=m['duration_slots'],
                        room=Room.objects.get(id=m['room_id']),
                        instruction_group_ids=m.get('instruction_group_ids') or None, user=admin)
                    placed += 1
                except Exception as exc:  # keep going; report at the end
                    self.stdout.write(self.style.WARNING(f'  skipped {asg}: {exc}'))
            return placed

        placed = place(version)
        unscheduled = len(result.get('unscheduled_offerings') or [])
        # Top up anything the first solve could not fit, keeping what is already placed.
        for _ in range(3):
            if not unscheduled:
                break
            extra = TimetableGenerator(version, time_limit=time_limit, replace_existing=False).generate()
            new = extra.get('proposed_meetings') or []
            placed += place(version, new)
            all_proposed.extend(new)
            unscheduled = len(extra.get('unscheduled_offerings') or [])
        self.log(f'{term.name}: {placed} meetings placed ({result.get("solver_status")}, '
                 f'{unscheduled} unscheduled)')

        if term.term_type == 'ODD':
            # Publish v1 so faculty and branch views have an official timetable,
            # and give the planner an editable draft copy as v2.
            ScheduleVersion.objects.filter(id=version.id).update(status='PUBLISHED', revision=version.revision + 1)
            draft = ScheduleVersion.objects.create(term=term, version_no=2, status='DRAFT',
                                                   name=f'Working Draft - {term.name}', created_by=admin)
            place(draft)
            self.log(f'{term.name}: version 1 PUBLISHED, version 2 DRAFT copy for editing')

    # ------------------------------------------------------------------
    def seed_calendar(self, ctx):
        odd, even = ctx['odd'], ctx['even']
        holidays = [
            (odd, date(2026, 8, 15), 'Independence Day'),
            (odd, date(2026, 10, 2), 'Gandhi Jayanti'),
            (odd, date(2026, 10, 20), 'Dussehra'),
            (odd, date(2026, 11, 8), 'Diwali'),
            (odd, date(2026, 11, 24), 'Guru Nanak Jayanti'),
            (even, date(2027, 1, 26), 'Republic Day'),
            (even, date(2027, 3, 22), 'Holi'),
            (even, date(2027, 4, 14), 'Ambedkar Jayanti'),
        ]
        for term, d, name in holidays:
            HolidayCalendar.objects.create(term=term, date=d, name=name,
                                           description=f'{name}: no classes', is_academic_holiday=True)
        published = ScheduleVersion.objects.filter(term=odd, status='PUBLISHED').first()
        meetings = list(ScheduledMeeting.objects.filter(schedule_version=published).order_by('id')[:2])
        if meetings:
            DateOverride.objects.create(scheduled_meeting=meetings[0], original_date=date(2026, 11, 23),
                                        status='CANCELLED', reason='Professor on official duty',
                                        created_by=ctx['admin'])
        if len(meetings) > 1:
            DateOverride.objects.create(scheduled_meeting=meetings[1], original_date=date(2026, 11, 25),
                                        new_date=date(2026, 11, 28), new_start_slot=meetings[1].start_slot,
                                        new_room=meetings[1].room, status='RESCHEDULED',
                                        reason='Moved for mid-semester exam', created_by=ctx['admin'])
        self.log(f'{len(holidays)} holidays and {DateOverride.objects.count()} date overrides')

    def print_summary(self):
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Seeding complete. Log in with:'))
        self.stdout.write('  Super Admin   admin@university.edu        / Admin@12345')
        self.stdout.write('  Coordinator   coordinator@university.edu  / Coord@12345   (B.Tech CSE and MCA)')
        self.stdout.write('  Professor     professor@university.edu    / Prof@12345    (MCA faculty)')
        self.stdout.write(f'  Other faculty <name>@university.edu       / {FACULTY_PASSWORD}')
