from django.contrib import admin
from .models import (
    ScheduleVersion,
    ScheduledMeeting,
    MeetingInstructionGroup,
    ProfessorSlotReservation,
    RoomSlotReservation,
    GroupSlotReservation,
    ScheduleChangeAudit,
    HolidayCalendar,
    DateOverride,
)

class ScheduledMeetingInline(admin.TabularInline):
    model = ScheduledMeeting
    extra = 0
    fields = ('weekday', 'start_slot', 'duration_slots', 'room', 'teaching_assignment')


@admin.register(ScheduleVersion)
class ScheduleVersionAdmin(admin.ModelAdmin):
    list_display = ('name', 'term', 'version_no', 'status', 'revision', 'created_at')
    list_filter = ('status', 'term')
    search_fields = ('name',)
    inlines = [ScheduledMeetingInline]


@admin.register(ScheduledMeeting)
class ScheduledMeetingAdmin(admin.ModelAdmin):
    list_display = ('id', 'schedule_version', 'weekday', 'start_slot', 'duration_slots', 'room', 'teaching_assignment')
    list_filter = ('weekday', 'schedule_version__status', 'room__building')
    search_fields = ('room__room_no', 'teaching_assignment__professor__full_name')


@admin.register(ProfessorSlotReservation)
class ProfessorSlotReservationAdmin(admin.ModelAdmin):
    list_display = ('schedule_version', 'professor', 'weekday', 'slot_no', 'scheduled_meeting')
    list_filter = ('weekday', 'slot_no')
    search_fields = ('professor__full_name', 'professor__email')


@admin.register(RoomSlotReservation)
class RoomSlotReservationAdmin(admin.ModelAdmin):
    list_display = ('schedule_version', 'room', 'weekday', 'slot_no', 'scheduled_meeting')
    list_filter = ('weekday', 'slot_no', 'room__building')
    search_fields = ('room__room_no',)


@admin.register(GroupSlotReservation)
class GroupSlotReservationAdmin(admin.ModelAdmin):
    list_display = ('schedule_version', 'instruction_group', 'weekday', 'slot_no', 'scheduled_meeting')
    list_filter = ('weekday', 'slot_no')


@admin.register(ScheduleChangeAudit)
class ScheduleChangeAuditAdmin(admin.ModelAdmin):
    list_display = ('id', 'schedule_version', 'meeting_id', 'action', 'user', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('user__email', 'action')
    readonly_fields = ('schedule_version', 'meeting_id', 'action', 'before_json', 'after_json', 'user', 'created_at')


@admin.register(HolidayCalendar)
class HolidayCalendarAdmin(admin.ModelAdmin):
    list_display = ('date', 'name', 'term', 'is_academic_holiday')
    list_filter = ('term', 'is_academic_holiday')
    search_fields = ('name', 'description')


@admin.register(DateOverride)
class DateOverrideAdmin(admin.ModelAdmin):
    list_display = ('scheduled_meeting', 'original_date', 'status', 'new_date', 'new_start_slot', 'new_room')
    list_filter = ('status', 'original_date')
    search_fields = ('reason',)
