from django.core.management.base import BaseCommand
from apps.accounts.models import User, Role, UserRoleAssignment, ProfessorProfile
from apps.academics.models import Department, Branch

class Command(BaseCommand):
    help = 'Seeds sample departments, branches, and test users for all 3 roles'

    def handle(self, *args, **options):
        # 1. Ensure Roles
        admin_role, _ = Role.objects.get_or_create(
            code=Role.Code.SUPER_ADMIN,
            defaults={'name': 'Super Administrator', 'description': 'Full university system access'}
        )
        coord_role, _ = Role.objects.get_or_create(
            code=Role.Code.BRANCH_COORDINATOR,
            defaults={'name': 'Branch Coordinator', 'description': 'Coordinates branch timetable'}
        )
        prof_role, _ = Role.objects.get_or_create(
            code=Role.Code.PROFESSOR,
            defaults={'name': 'Professor', 'description': 'Faculty member'}
        )

        # 2. Departments
        cse_dept, _ = Department.objects.get_or_create(
            code='CSE',
            defaults={
                'name': 'Computer Science & Engineering',
                'description': 'Department of Computer Science & Engineering'
            }
        )
        ca_dept, _ = Department.objects.get_or_create(
            code='CA',
            defaults={
                'name': 'Computer Applications',
                'description': 'Department of Computer Applications (MCA)'
            }
        )
        ece_dept, _ = Department.objects.get_or_create(
            code='ECE',
            defaults={
                'name': 'Electronics & Communication Engineering',
                'description': 'Department of Electronics & Communication'
            }
        )

        # 3. Branches
        btech_cse, _ = Branch.objects.get_or_create(
            department=cse_dept,
            code='BTECH_CSE',
            defaults={
                'name': 'B.Tech in Computer Science',
                'degree_name': 'B.Tech',
                'max_semesters': 8,
            }
        )
        mca, _ = Branch.objects.get_or_create(
            department=ca_dept,
            code='MCA',
            defaults={
                'name': 'Master of Computer Applications',
                'degree_name': 'MCA',
                'max_semesters': 6,
            }
        )
        mtech_cse, _ = Branch.objects.get_or_create(
            department=cse_dept,
            code='MTECH_CSE',
            defaults={
                'name': 'M.Tech in Computer Science',
                'degree_name': 'M.Tech',
                'max_semesters': 4,
            }
        )

        # 4. Super Admin User
        admin_user, _ = User.objects.get_or_create(
            email='admin@university.edu',
            defaults={
                'full_name': 'Dr. Alistair Vance (Super Admin)',
                'employee_code': 'ADM001',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin_user.set_password('Admin@12345')
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()
        UserRoleAssignment.objects.get_or_create(user=admin_user, role=admin_role, branch=None)

        # 5. Coordinator User
        coord_user, _ = User.objects.get_or_create(
            email='coordinator@university.edu',
            defaults={
                'full_name': 'Prof. Rajesh Kumar (CSE Coordinator)',
                'employee_code': 'CRD001',
                'is_staff': False,
            }
        )
        coord_user.set_password('Coord@12345')
        coord_user.save()
        UserRoleAssignment.objects.get_or_create(user=coord_user, role=coord_role, branch=btech_cse)

        # 6. Professor User
        prof_user, _ = User.objects.get_or_create(
            email='professor@university.edu',
            defaults={
                'full_name': 'Dr. Sunita Sharma (Professor)',
                'employee_code': 'PRF001',
                'is_staff': False,
            }
        )
        prof_user.set_password('Prof@12345')
        prof_user.save()
        UserRoleAssignment.objects.get_or_create(user=prof_user, role=prof_role, branch=None)
        ProfessorProfile.objects.get_or_create(
            user=prof_user,
            defaults={
                'designation': 'Associate Professor',
                'department': cse_dept,
                'max_hours_per_day': 6,
            }
        )

        self.stdout.write(self.style.SUCCESS(
            "Successfully seeded sample data:\n"
            "  Admin:       admin@university.edu       / Admin@12345 (SUPER_ADMIN)\n"
            "  Coordinator: coordinator@university.edu / Coord@12345 (BRANCH_COORDINATOR - BTECH_CSE)\n"
            "  Professor:   professor@university.edu   / Prof@12345  (PROFESSOR - CSE Dept)\n"
            "  Departments: CSE, CA, ECE\n"
            "  Branches:    BTECH_CSE, MCA, MTECH_CSE"
        ))

