from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class ScheduleVersion(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
        PUBLISHED = 'PUBLISHED', 'Published'
        ARCHIVED = 'ARCHIVED', 'Archived'

    term = models.ForeignKey(
        'academics.AcademicTerm',
        on_delete=models.CASCADE,
        related_name='schedule_versions'
    )
    version_no = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True
    )
    revision = models.PositiveIntegerField(default=1, help_text="Monotonically increasing version counter for WS cache sync")
    name = models.CharField(max_length=150, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_schedules'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'schedule_versions'
        unique_together = ('term', 'version_no')
        ordering = ['term', '-version_no']

    def __str__(self):
        title = self.name or f"Version {self.version_no}"
        return f"{self.term.name} - {title} [{self.get_status_display()}] (Rev {self.revision})"


class ScheduledMeeting(models.Model):
    class Weekday(models.IntegerChoices):
        MONDAY = 1, 'Monday'
        TUESDAY = 2, 'Tuesday'
        WEDNESDAY = 3, 'Wednesday'
        THURSDAY = 4, 'Thursday'
        FRIDAY = 5, 'Friday'

    schedule_version = models.ForeignKey(
        ScheduleVersion,
        on_delete=models.CASCADE,
        related_name='meetings'
    )
    teaching_assignment = models.ForeignKey(
        'academics.TeachingAssignment',
        on_delete=models.CASCADE,
        related_name='scheduled_meetings'
    )
    weekday = models.PositiveSmallIntegerField(
        choices=Weekday.choices,
        db_index=True
    )
    start_slot = models.PositiveSmallIntegerField(
        help_text="Starting time slot (1..8)",
        db_index=True
    )
    duration_slots = models.PositiveSmallIntegerField(
        default=1,
        help_text="Duration in 1-hour slots (1 for theory, 3 for lab)"
    )
    room = models.ForeignKey(
        'facilities.Room',
        on_delete=models.CASCADE,
        related_name='scheduled_meetings'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'scheduled_meetings'
        ordering = ['weekday', 'start_slot']

    def __str__(self):
        course = self.teaching_assignment.course_offering.curriculum_item.course.code
        prof = self.teaching_assignment.professor.full_name
        day = self.get_weekday_display()
        end = self.start_slot + self.duration_slots - 1
        return f"{course} with {prof} on {day} (Slots {self.start_slot}-{end}) @ Room {self.room.room_no}"

    @property
    def end_slot(self):
        return self.start_slot + self.duration_slots - 1

    @property
    def occupied_slots(self):
        return list(range(self.start_slot, self.start_slot + self.duration_slots))


class MeetingInstructionGroup(models.Model):
    scheduled_meeting = models.ForeignKey(
        ScheduledMeeting,
        on_delete=models.CASCADE,
        related_name='meeting_instruction_groups'
    )
    instruction_group = models.ForeignKey(
        'academics.InstructionGroup',
        on_delete=models.CASCADE,
        related_name='scheduled_meetings'
    )

    class Meta:
        db_table = 'meeting_instruction_groups'
        unique_together = ('scheduled_meeting', 'instruction_group')

    def __str__(self):
        return f"Meeting {self.scheduled_meeting_id} -> Group {self.instruction_group.code}"


class ProfessorSlotReservation(models.Model):
    schedule_version = models.ForeignKey(
        ScheduleVersion,
        on_delete=models.CASCADE,
        related_name='professor_slot_reservations'
    )
    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='professor_slot_reservations'
    )
    weekday = models.PositiveSmallIntegerField(db_index=True)
    slot_no = models.PositiveSmallIntegerField(db_index=True)
    scheduled_meeting = models.ForeignKey(
        ScheduledMeeting,
        on_delete=models.CASCADE,
        related_name='professor_reservations'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'professor_slot_reservations'
        unique_together = ('schedule_version', 'professor', 'weekday', 'slot_no')
        indexes = [
            models.Index(fields=['schedule_version', 'professor', 'weekday', 'slot_no']),
        ]

    def __str__(self):
        return f"Prof {self.professor_id} busy Day {self.weekday} Slot {self.slot_no} (Version {self.schedule_version_id})"


class RoomSlotReservation(models.Model):
    schedule_version = models.ForeignKey(
        ScheduleVersion,
        on_delete=models.CASCADE,
        related_name='room_slot_reservations'
    )
    room = models.ForeignKey(
        'facilities.Room',
        on_delete=models.CASCADE,
        related_name='room_slot_reservations'
    )
    weekday = models.PositiveSmallIntegerField(db_index=True)
    slot_no = models.PositiveSmallIntegerField(db_index=True)
    scheduled_meeting = models.ForeignKey(
        ScheduledMeeting,
        on_delete=models.CASCADE,
        related_name='room_reservations'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'room_slot_reservations'
        unique_together = ('schedule_version', 'room', 'weekday', 'slot_no')
        indexes = [
            models.Index(fields=['schedule_version', 'room', 'weekday', 'slot_no']),
        ]

    def __str__(self):
        return f"Room {self.room_id} busy Day {self.weekday} Slot {self.slot_no} (Version {self.schedule_version_id})"


class GroupSlotReservation(models.Model):
    schedule_version = models.ForeignKey(
        ScheduleVersion,
        on_delete=models.CASCADE,
        related_name='group_slot_reservations'
    )
    instruction_group = models.ForeignKey(
        'academics.InstructionGroup',
        on_delete=models.CASCADE,
        related_name='group_slot_reservations'
    )
    weekday = models.PositiveSmallIntegerField(db_index=True)
    slot_no = models.PositiveSmallIntegerField(db_index=True)
    scheduled_meeting = models.ForeignKey(
        ScheduledMeeting,
        on_delete=models.CASCADE,
        related_name='group_reservations'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'group_slot_reservations'
        unique_together = ('schedule_version', 'instruction_group', 'weekday', 'slot_no')
        indexes = [
            models.Index(fields=['schedule_version', 'instruction_group', 'weekday', 'slot_no']),
        ]

    def __str__(self):
        return f"Group {self.instruction_group_id} busy Day {self.weekday} Slot {self.slot_no} (Version {self.schedule_version_id})"


class ScheduleChangeAudit(models.Model):
    schedule_version = models.ForeignKey(
        ScheduleVersion,
        on_delete=models.CASCADE,
        related_name='change_audits'
    )
    meeting_id = models.PositiveBigIntegerField(null=True, blank=True)
    action = models.CharField(max_length=50) # 'CREATE', 'UPDATE', 'DELETE', 'BATCH_UPDATE'
    before_json = models.JSONField(default=dict, blank=True)
    after_json = models.JSONField(default=dict, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'schedule_change_audits'
        ordering = ['-created_at']

    def __str__(self):
        user_str = self.user.email if self.user else "System"
        return f"Audit {self.action} on meeting {self.meeting_id} by {user_str} at {self.created_at}"


class HolidayCalendar(models.Model):
    term = models.ForeignKey(
        'academics.AcademicTerm',
        on_delete=models.CASCADE,
        related_name='holidays'
    )
    date = models.DateField(db_index=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, default='')
    is_academic_holiday = models.BooleanField(default=True, help_text="True if classes are suspended on this day")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'holiday_calendar'
        unique_together = ('term', 'date')
        ordering = ['date']

    def __str__(self):
        return f"{self.date}: {self.name} ({self.term.name})"


class DateOverride(models.Model):
    class Status(models.TextChoices):
        CANCELLED = 'CANCELLED', 'Cancelled'
        RESCHEDULED = 'RESCHEDULED', 'Rescheduled'

    scheduled_meeting = models.ForeignKey(
        ScheduledMeeting,
        on_delete=models.CASCADE,
        related_name='date_overrides'
    )
    original_date = models.DateField(db_index=True)
    new_date = models.DateField(null=True, blank=True)
    new_start_slot = models.PositiveSmallIntegerField(null=True, blank=True)
    new_room = models.ForeignKey(
        'facilities.Room',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='date_overrides'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CANCELLED
    )
    reason = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'date_overrides'
        unique_together = ('scheduled_meeting', 'original_date')
        ordering = ['-original_date']

    def __str__(self):
        return f"Override for Meeting {self.scheduled_meeting_id} on {self.original_date}: {self.get_status_display()}"

