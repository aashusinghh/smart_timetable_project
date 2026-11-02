from django.core.management.base import BaseCommand
from decouple import config
from apps.accounts.models import User, Role, UserRoleAssignment

class Command(BaseCommand):
    help = 'Creates an initial Super Administrator user with role assignment'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, default='admin@university.edu', help='Admin email address')
        parser.add_argument('--password', type=str, default='Admin@12345', help='Admin password')
        parser.add_argument('--name', type=str, default='System Administrator', help='Full name')

    def handle(self, *args, **options):
        email = options['email'].strip().lower()
        password = options['password']
        name = options['name']

        # Ensure roles exist first
        super_admin_role, _ = Role.objects.get_or_create(
            code=Role.Code.SUPER_ADMIN,
            defaults={'name': 'Super Administrator', 'description': 'Full university system access'}
        )
        Role.objects.get_or_create(
            code=Role.Code.BRANCH_COORDINATOR,
            defaults={'name': 'Branch Coordinator', 'description': 'Coordinates branch timetable'}
        )
        Role.objects.get_or_create(
            code=Role.Code.PROFESSOR,
            defaults={'name': 'Professor', 'description': 'Faculty member'}
        )

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'full_name': name,
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
                'employee_code': 'ADMIN001'
            }
        )

        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()

        assignment, _ = UserRoleAssignment.objects.get_or_create(
            user=user,
            role=super_admin_role,
            branch=None
        )

        action_str = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(
            f"Successfully {action_str} Super Administrator:\n"
            f"  Email: {email}\n"
            f"  Password: {password}\n"
            f"  Role: {super_admin_role.code}"
        ))

