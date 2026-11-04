import csv
import io
from django.db import transaction
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from apps.accounts.models import User, Role, UserRoleAssignment, ProfessorProfile
from apps.academics.models import Department, Branch, Course, CourseDeliveryRule, CurriculumItem

class CSVImportService:
    @staticmethod
    def import_curriculum_csv(file_obj):
        """
        Imports curriculum items and courses from a CSV file.
        Expected headers:
        branch_code,semester_no,course_code,course_name,credit,course_type,weekly_meetings,duration_slots
        """
        decoded_file = file_obj.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(decoded_file))

        required_headers = [
            'branch_code', 'semester_no', 'course_code', 'course_name',
            'credit', 'course_type'
        ]
        if not reader.fieldnames:
            return {'success': False, 'errors': [{'row': 0, 'message': 'Empty CSV file'}]}

        missing_headers = [h for h in required_headers if h not in [fn.strip() for fn in reader.fieldnames]]
        if missing_headers:
            return {
                'success': False,
                'errors': [{'row': 0, 'message': f"Missing required headers: {', '.join(missing_headers)}"}]
            }

        errors = []
        rows_to_process = []
        valid_course_types = [c[0] for c in Course.CourseType.choices]

        for idx, raw_row in enumerate(reader, start=2): # 1-based, row 1 is header
            row = {k.strip(): v.strip() for k, v in raw_row.items() if k}
            row_errors = []

            # 1. Branch
            branch_code = row.get('branch_code', '')
            branch = Branch.objects.filter(code__iexact=branch_code).first()
            if not branch:
                row_errors.append(f"Branch '{branch_code}' does not exist.")

            # 2. Semester
            try:
                semester_no = int(row.get('semester_no', ''))
                if semester_no < 1:
                    row_errors.append("semester_no must be at least 1.")
                elif branch and semester_no > branch.max_semesters:
                    row_errors.append(f"semester_no {semester_no} exceeds branch max semesters ({branch.max_semesters}).")
            except ValueError:
                row_errors.append("semester_no must be an integer.")
                semester_no = None

            # 3. Course Code & Name
            course_code = row.get('course_code', '').upper()
            course_name = row.get('course_name', '')
            if not course_code:
                row_errors.append("course_code is required.")
            if not course_name:
                row_errors.append("course_name is required.")

            # 4. Credit
            try:
                credit = int(row.get('credit', '3'))
                if credit < 1:
                    row_errors.append("credit must be >= 1.")
            except ValueError:
                row_errors.append("credit must be an integer.")
                credit = 3

            # 5. Course Type
            course_type = row.get('course_type', 'THEORY').upper()
            if course_type not in valid_course_types:
                row_errors.append(f"Invalid course_type '{course_type}'. Allowed: {', '.join(valid_course_types)}")

            # 6. Delivery Rule (Optional in CSV, defaults applied if blank)
            try:
                weekly_meetings = int(row.get('weekly_meetings')) if row.get('weekly_meetings') else None
            except ValueError:
                row_errors.append("weekly_meetings must be an integer.")
                weekly_meetings = None

            try:
                duration_slots = int(row.get('duration_slots')) if row.get('duration_slots') else None
            except ValueError:
                row_errors.append("duration_slots must be an integer.")
                duration_slots = None

            if row_errors:
                errors.append({'row': idx, 'message': "; ".join(row_errors)})
            else:
                rows_to_process.append({
                    'branch': branch,
                    'semester_no': semester_no,
                    'course_code': course_code,
                    'course_name': course_name,
                    'credit': credit,
                    'course_type': course_type,
                    'weekly_meetings': weekly_meetings,
                    'duration_slots': duration_slots,
                })

        if errors:
            return {'success': False, 'errors': errors, 'imported_count': 0}

        # Atomic commit
        imported_count = 0
        with transaction.atomic():
            for item in rows_to_process:
                # Get or create Course
                course, _ = Course.objects.update_or_create(
                    code=item['course_code'],
                    defaults={
                        'name': item['course_name'],
                        'credit': item['credit'],
                        'course_type': item['course_type'],
                        'department': item['branch'].department,
                    }
                )

                # Set Delivery Rule
                meetings = item['weekly_meetings']
                slots = item['duration_slots']
                room_type = 'COMPUTER_LAB' if item['course_type'] == 'LAB' else 'CLASSROOM'

                if meetings is None or slots is None:
                    if item['course_type'] == 'LAB':
                        meetings, slots = 2, 3
                    else:
                        meetings, slots = item['credit'], 1

                CourseDeliveryRule.objects.update_or_create(
                    course=course,
                    defaults={
                        'weekly_meetings': meetings,
                        'duration_slots': slots,
                        'preferred_room_type': room_type,
                    }
                )

                # Link to CurriculumItem
                CurriculumItem.objects.update_or_create(
                    branch=item['branch'],
                    semester_no=item['semester_no'],
                    course=course,
                    defaults={'is_active': True}
                )
                imported_count += 1

        return {'success': True, 'imported_count': imported_count, 'errors': []}

    @staticmethod
    def import_professors_csv(file_obj):
        """
        Imports professors from a CSV file.
        Expected headers:
        email,full_name,employee_code,department_code,designation,max_hours_per_day
        """
        decoded_file = file_obj.read().decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(decoded_file))

        required_headers = ['email', 'full_name', 'department_code']
        if not reader.fieldnames:
            return {'success': False, 'errors': [{'row': 0, 'message': 'Empty CSV file'}]}

        missing_headers = [h for h in required_headers if h not in [fn.strip() for fn in reader.fieldnames]]
        if missing_headers:
            return {
                'success': False,
                'errors': [{'row': 0, 'message': f"Missing required headers: {', '.join(missing_headers)}"}]
            }

        errors = []
        rows_to_process = []
        seen_emails = set()

        for idx, raw_row in enumerate(reader, start=2):
            row = {k.strip(): v.strip() for k, v in raw_row.items() if k}
            row_errors = []

            # Email
            email = row.get('email', '').lower()
            if not email:
                row_errors.append("email is required.")
            else:
                try:
                    validate_email(email)
                except ValidationError:
                    row_errors.append(f"Invalid email format: '{email}'.")

                if email in seen_emails:
                    row_errors.append(f"Duplicate email in CSV: '{email}'.")
                seen_emails.add(email)

            # Name
            full_name = row.get('full_name', '')
            if not full_name:
                row_errors.append("full_name is required.")

            # Department
            dept_code = row.get('department_code', '')
            dept = Department.objects.filter(code__iexact=dept_code).first()
            if not dept:
                row_errors.append(f"Department code '{dept_code}' not found.")

            # Max hours
            try:
                max_hours = int(row.get('max_hours_per_day', '6'))
                if max_hours < 1 or max_hours > 12:
                    row_errors.append("max_hours_per_day must be between 1 and 12.")
            except ValueError:
                row_errors.append("max_hours_per_day must be an integer.")
                max_hours = 6

            designation = row.get('designation', 'Assistant Professor') or 'Assistant Professor'
            emp_code = row.get('employee_code') or None

            if row_errors:
                errors.append({'row': idx, 'message': "; ".join(row_errors)})
            else:
                rows_to_process.append({
                    'email': email,
                    'full_name': full_name,
                    'employee_code': emp_code,
                    'department': dept,
                    'designation': designation,
                    'max_hours_per_day': max_hours,
                })

        if errors:
            return {'success': False, 'errors': errors, 'imported_count': 0}

        imported_count = 0
        prof_role, _ = Role.objects.get_or_create(
            code=Role.Code.PROFESSOR,
            defaults={'name': 'Professor', 'description': 'Faculty member'}
        )

        with transaction.atomic():
            for item in rows_to_process:
                user, created = User.objects.get_or_create(
                    email=item['email'],
                    defaults={
                        'full_name': item['full_name'],
                        'employee_code': item['employee_code'],
                        'is_active': True,
                    }
                )
                if created:
                    user.set_password('ProfessorPassword123!')
                    user.save()
                else:
                    user.full_name = item['full_name']
                    if item['employee_code']:
                        user.employee_code = item['employee_code']
                    user.save()

                UserRoleAssignment.objects.get_or_create(user=user, role=prof_role)

                ProfessorProfile.objects.update_or_create(
                    user=user,
                    defaults={
                        'department': item['department'],
                        'designation': item['designation'],
                        'max_hours_per_day': item['max_hours_per_day'],
                    }
                )
                imported_count += 1

        return {'success': True, 'imported_count': imported_count, 'errors': []}
