import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AcademicYear',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, help_text="e.g. '2026-27'", max_length=50, unique=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('is_current', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'academic_years',
                'ordering': ['-start_date'],
            },
        ),
        migrations.CreateModel(
            name='TimeSlot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slot_no', models.PositiveSmallIntegerField(db_index=True, help_text='Slot index 1 through 8', unique=True)),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('session', models.CharField(choices=[('MORNING', 'Morning Session'), ('AFTERNOON', 'Afternoon Session')], max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'time_slots',
                'ordering': ['slot_no'],
            },
        ),
        migrations.CreateModel(
            name='AcademicTerm',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text="e.g. 'Odd Semester 2026-27'", max_length=100)),
                ('term_type', models.CharField(choices=[('ODD', 'Odd Semester'), ('EVEN', 'Even Semester'), ('SUMMER', 'Summer Term')], default='ODD', max_length=20)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('academic_year', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='terms', to='academics.academicyear')),
            ],
            options={
                'db_table': 'academic_terms',
                'ordering': ['-start_date'],
                'unique_together': {('academic_year', 'name')},
            },
        ),
        migrations.CreateModel(
            name='Cohort',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('semester_no', models.PositiveIntegerField(help_text='Current semester number (1..branch.max_semesters)')),
                ('section_code', models.CharField(default='A', help_text='Section such as A, B, C', max_length=10)),
                ('student_count', models.PositiveIntegerField(default=60)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('branch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cohorts', to='academics.branch')),
                ('term', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cohorts', to='academics.academicterm')),
            ],
            options={
                'db_table': 'cohorts',
                'ordering': ['branch', 'semester_no', 'section_code'],
                'unique_together': {('branch', 'term', 'semester_no', 'section_code')},
            },
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(db_index=True, max_length=30, unique=True)),
                ('name', models.CharField(max_length=150)),
                ('credit', models.PositiveIntegerField(default=3)),
                ('course_type', models.CharField(choices=[('THEORY', 'Theory'), ('LAB', 'Practical / Laboratory'), ('PROJECT', 'Project Work'), ('SEMINAR', 'Seminar')], db_index=True, default='THEORY', max_length=20)),
                ('description', models.TextField(blank=True, default='')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('department', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='courses', to='academics.department')),
            ],
            options={
                'db_table': 'courses',
                'ordering': ['code'],
            },
        ),
        migrations.CreateModel(
            name='CourseDeliveryRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weekly_meetings', models.PositiveIntegerField(default=3, help_text='Weekly meeting occurrences (e.g. 3 for 3x1hr theory, 2 for 2x3hr lab)')),
                ('duration_slots', models.PositiveIntegerField(default=1, help_text='Duration per meeting in 1-hour slots (e.g. 1 for theory, 3 for lab)')),
                ('preferred_room_type', models.CharField(blank=True, default='CLASSROOM', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('course', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='delivery_rule', to='academics.course')),
            ],
            options={
                'db_table': 'course_delivery_rules',
            },
        ),
        migrations.CreateModel(
            name='CurriculumItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('semester_no', models.PositiveIntegerField()),
                ('is_elective', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('branch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='curriculum_items', to='academics.branch')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='curriculum_inclusions', to='academics.course')),
            ],
            options={
                'db_table': 'curriculum_items',
                'ordering': ['branch', 'semester_no', 'course__code'],
                'unique_together': {('branch', 'semester_no', 'course')},
            },
        ),
        migrations.CreateModel(
            name='InstructionGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(help_text="e.g. 'A-L1', 'A-L2', 'ALL'", max_length=50)),
                ('name', models.CharField(blank=True, default='', max_length=100)),
                ('size', models.PositiveIntegerField(default=30)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('cohort', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='instruction_groups', to='academics.cohort')),
            ],
            options={
                'db_table': 'instruction_groups',
                'ordering': ['cohort', 'code'],
                'unique_together': {('cohort', 'code')},
            },
        ),
        migrations.CreateModel(
            name='CourseOffering',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('cohort', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='offerings', to='academics.cohort')),
                ('curriculum_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='offerings', to='academics.curriculumitem')),
                ('term', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='course_offerings', to='academics.academicterm')),
            ],
            options={
                'db_table': 'course_offerings',
                'ordering': ['term', 'cohort', 'curriculum_item'],
                'unique_together': {('term', 'cohort', 'curriculum_item')},
            },
        ),
        migrations.CreateModel(
            name='TeachingAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_primary', models.BooleanField(default=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('course_offering', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teaching_assignments', to='academics.courseoffering')),
                ('instruction_group', models.ForeignKey(blank=True, help_text='Optional: specific lab group. If null, professor teaches the whole cohort.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='teaching_assignments', to='academics.instructiongroup')),
                ('professor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teaching_assignments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'teaching_assignments',
                'ordering': ['course_offering', 'professor'],
                'unique_together': {('course_offering', 'professor', 'instruction_group')},
            },
        ),
    ]
