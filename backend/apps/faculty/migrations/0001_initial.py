import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ProfessorUnavailability',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weekday', models.PositiveSmallIntegerField(blank=True, help_text='1=Monday, 2=Tuesday, ..., 5=Friday', null=True)),
                ('specific_date', models.DateField(blank=True, help_text='Optional specific calendar date', null=True)),
                ('start_slot', models.PositiveSmallIntegerField(default=1, help_text='Start slot (1..8)')),
                ('end_slot', models.PositiveSmallIntegerField(default=8, help_text='End slot (1..8)')),
                ('reason', models.CharField(default='Personal / Committee Meeting', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('professor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unavailabilities', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'professor_unavailability',
                'ordering': ['professor', 'specific_date', 'weekday', 'start_slot'],
            },
        ),
    ]
