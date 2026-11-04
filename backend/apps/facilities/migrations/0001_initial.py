import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Campus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
                ('code', models.CharField(db_index=True, max_length=50, unique=True)),
                ('address', models.TextField(blank=True, default='')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name_plural': 'Campuses',
                'db_table': 'campuses',
                'ordering': ['code'],
            },
        ),
        migrations.CreateModel(
            name='Building',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
                ('code', models.CharField(db_index=True, max_length=50)),
                ('floors_count', models.PositiveIntegerField(default=1)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('campus', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='buildings', to='facilities.campus')),
            ],
            options={
                'db_table': 'buildings',
                'ordering': ['campus', 'code'],
                'unique_together': {('campus', 'code')},
            },
        ),
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('room_no', models.CharField(db_index=True, max_length=50)),
                ('name', models.CharField(blank=True, default='', max_length=150)),
                ('room_type', models.CharField(choices=[('CLASSROOM', 'Standard Classroom'), ('COMPUTER_LAB', 'Computer Lab'), ('ELECTRONICS_LAB', 'Electronics Lab'), ('CHEMISTRY_LAB', 'Chemistry Lab'), ('SEMINAR_HALL', 'Seminar Hall')], db_index=True, default='CLASSROOM', max_length=50)),
                ('capacity', models.PositiveIntegerField(default=60)),
                ('floor', models.PositiveIntegerField(default=1)),
                ('has_projector', models.BooleanField(default=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('building', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rooms', to='facilities.building')),
            ],
            options={
                'db_table': 'rooms',
                'ordering': ['building', 'room_no'],
                'unique_together': {('building', 'room_no')},
            },
        ),
        migrations.CreateModel(
            name='RoomUnavailability',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weekday', models.PositiveSmallIntegerField(blank=True, help_text='1=Monday, 2=Tuesday, ..., 5=Friday (or recurring weekday)', null=True)),
                ('specific_date', models.DateField(blank=True, help_text='Optional specific calendar date', null=True)),
                ('start_slot', models.PositiveSmallIntegerField(default=1, help_text='Starting time slot (1..8)')),
                ('end_slot', models.PositiveSmallIntegerField(default=8, help_text='Ending time slot (1..8)')),
                ('reason', models.CharField(default='Maintenance / Reserved', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unavailabilities', to='facilities.room')),
            ],
            options={
                'db_table': 'room_unavailability',
                'ordering': ['room', 'specific_date', 'weekday', 'start_slot'],
            },
        ),
    ]
