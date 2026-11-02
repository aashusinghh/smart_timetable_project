from django.core.management.base import BaseCommand
from apps.accounts.models import Role

class Command(BaseCommand):
    help = 'Seeds initial system roles (SUPER_ADMIN, BRANCH_COORDINATOR, PROFESSOR)'

    def handle(self, *args, **options):
        roles_data = [
            {
                'code': Role.Code.SUPER_ADMIN,
                'name': 'Super Administrator',
                'description': 'Full access to all university departments, branches, schedules, and settings.'
            },
            {
                'code': Role.Code.BRANCH_COORDINATOR,
                'name': 'Branch Coordinator',
                'description': 'Manages cohorts, offerings, and draft timetable for assigned branch(es).'
            },
            {
                'code': Role.Code.PROFESSOR,
                'name': 'Professor / Faculty',
                'description': 'Read-only access to personal timetable, assigned courses, and university notices.'
            },
        ]

        created_count = 0
        for r_info in roles_data:
            role, created = Role.objects.get_or_create(
                code=r_info['code'],
                defaults={
                    'name': r_info['name'],
                    'description': r_info['description'],
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created role: {role.code}"))
            else:
                self.stdout.write(f"Role already exists: {role.code}")

        self.stdout.write(self.style.SUCCESS(f"Successfully processed roles. {created_count} created."))

