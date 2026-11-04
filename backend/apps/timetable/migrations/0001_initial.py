import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('academics', '0002_phase2_models'),
        ('facilities', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ScheduleVersion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version_no', models.PositiveIntegerField(default=1)),
                ('status', models.CharField(choices=[('DRAFT', 'Draft'), ('UNDER_REVIEW', 'Under Review'), ('PUBLISHED', 'Published'), ('ARCHIVED', 'Archived')], db_index=True, default='DRAFT', max_length=20)),
                ('revision', models.PositiveIntegerField(default=1, help_text='Monotonically increasing version counter for WS cache sync')),
                ('name', models.CharField(blank=True, default='', max_length=150)),
                ('notes', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_schedules', to=settings.AUTH_USER_MODEL)),
                ('term', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='schedule_versions', to='academics.academicterm')),
            ],
            options={
                'db_table': 'schedule_versions',
                'ordering': ['term', '-version_no'],
                'unique_together': {('term', 'version_no')},
            },
        ),
        migrations.CreateModel(
            name='ScheduledMeeting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weekday', models.PositiveSmallIntegerField(choices=[(1, 'Monday'), (2, 'Tuesday'), (3, 'Wednesday'), (4, 'Thursday'), (5, 'Friday')], db_index=True)),
                ('start_slot', models.PositiveSmallIntegerField(db_index=True, help_text='Starting time slot (1..8)')),
                ('duration_slots', models.PositiveSmallIntegerField(default=1, help_text='Duration in 1-hour slots (1 for theory, 3 for lab)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scheduled_meetings', to='facilities.room')),
                ('schedule_version', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='meetings', to='timetable.scheduleversion')),
                ('teaching_assignment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scheduled_meetings', to='academics.teachingassignment')),
            ],
            options={
                'db_table': 'scheduled_meetings',
                'ordering': ['weekday', 'start_slot'],
            },
        ),
        migrations.CreateModel(
            name='ScheduleChangeAudit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('meeting_id', models.PositiveBigIntegerField(blank=True, null=True)),
                ('action', models.CharField(max_length=50)),
                ('before_json', models.JSONField(blank=True, default=dict)),
                ('after_json', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('schedule_version', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='change_audits', to='timetable.scheduleversion')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'schedule_change_audits',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='MeetingInstructionGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('instruction_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scheduled_meetings', to='academics.instructiongroup')),
                ('scheduled_meeting', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='meeting_instruction_groups', to='timetable.scheduledmeeting')),
            ],
            options={
                'db_table': 'meeting_instruction_groups',
                'unique_together': {('scheduled_meeting', 'instruction_group')},
            },
        ),
        migrations.CreateModel(
            name='ProfessorSlotReservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weekday', models.PositiveSmallIntegerField(db_index=True)),
                ('slot_no', models.PositiveSmallIntegerField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('professor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='professor_slot_reservations', to=settings.AUTH_USER_MODEL)),
                ('schedule_version', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='professor_slot_reservations', to='timetable.scheduleversion')),
                ('scheduled_meeting', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='professor_reservations', to='timetable.scheduledmeeting')),
            ],
            options={
                'db_table': 'professor_slot_reservations',
                'unique_together': {('schedule_version', 'professor', 'weekday', 'slot_no')},
            },
        ),
        migrations.CreateModel(
            name='RoomSlotReservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weekday', models.PositiveSmallIntegerField(db_index=True)),
                ('slot_no', models.PositiveSmallIntegerField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='room_slot_reservations', to='facilities.room')),
                ('schedule_version', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='room_slot_reservations', to='timetable.scheduleversion')),
                ('scheduled_meeting', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='room_reservations', to='timetable.scheduledmeeting')),
            ],
            options={
                'db_table': 'room_slot_reservations',
                'unique_together': {('schedule_version', 'room', 'weekday', 'slot_no')},
            },
        ),
        migrations.CreateModel(
            name='GroupSlotReservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weekday', models.PositiveSmallIntegerField(db_index=True)),
                ('slot_no', models.PositiveSmallIntegerField(db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('instruction_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_slot_reservations', to='academics.instructiongroup')),
                ('schedule_version', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_slot_reservations', to='timetable.scheduleversion')),
                ('scheduled_meeting', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_reservations', to='timetable.scheduledmeeting')),
            ],
            options={
                'db_table': 'group_slot_reservations',
                'unique_together': {('schedule_version', 'instruction_group', 'weekday', 'slot_no')},
            },
        ),
        migrations.AddIndex(
            model_name='professorslotreservation',
            index=models.Index(fields=['schedule_version', 'professor', 'weekday', 'slot_no'], name='prof_slot_res_idx'),
        ),
        migrations.AddIndex(
            model_name='roomslotreservation',
            index=models.Index(fields=['schedule_version', 'room', 'weekday', 'slot_no'], name='room_slot_res_idx'),
        ),
        migrations.AddIndex(
            model_name='groupslotreservation',
            index=models.Index(fields=['schedule_version', 'instruction_group', 'weekday', 'slot_no'], name='group_slot_res_idx'),
        ),
    ]
