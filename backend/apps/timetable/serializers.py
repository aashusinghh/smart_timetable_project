from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
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
from apps.academics.models import TeachingAssignment, InstructionGroup
from apps.facilities.models import Room

class ScheduleVersionSerializer(serializers.ModelSerializer):
    term_name = serializers.CharField(source='term.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    meetings_count = serializers.IntegerField(source='meetings.count', read_only=True)

    class Meta:
        model = ScheduleVersion
        fields = [
            'id', 'term', 'term_name', 'version_no', 'status',
            'status_display', 'revision', 'name', 'notes',
            'meetings_count', 'created_at', 'updated_at'
        ]


class ScheduledMeetingSerializer(serializers.ModelSerializer):
    weekday_display = serializers.CharField(source='get_weekday_display', read_only=True)
    end_slot = serializers.IntegerField(read_only=True)
    room_no = serializers.CharField(source='room.room_no', read_only=True)
    building_code = serializers.CharField(source='room.building.code', read_only=True)
    building_name = serializers.CharField(source='room.building.name', read_only=True)
    room_type = serializers.CharField(source='room.room_type', read_only=True)

    course_code = serializers.CharField(
        source='teaching_assignment.course_offering.curriculum_item.course.code',
        read_only=True
    )
    course_name = serializers.CharField(
        source='teaching_assignment.course_offering.curriculum_item.course.name',
        read_only=True
    )
    course_type = serializers.CharField(
        source='teaching_assignment.course_offering.curriculum_item.course.course_type',
        read_only=True
    )
    course_credit = serializers.IntegerField(
        source='teaching_assignment.course_offering.curriculum_item.course.credit',
        read_only=True
    )
    professor_id = serializers.IntegerField(source='teaching_assignment.professor.id', read_only=True)
    professor_name = serializers.CharField(source='teaching_assignment.professor.full_name', read_only=True)
    cohort_id = serializers.IntegerField(source='teaching_assignment.course_offering.cohort.id', read_only=True)
    cohort_str = serializers.CharField(source='teaching_assignment.course_offering.cohort.__str__', read_only=True)
    branch_id = serializers.IntegerField(source='teaching_assignment.course_offering.cohort.branch.id', read_only=True)
    branch_code = serializers.CharField(source='teaching_assignment.course_offering.cohort.branch.code', read_only=True)
    group_codes = serializers.SerializerMethodField()

    class Meta:
        model = ScheduledMeeting
        fields = [
            'id', 'schedule_version', 'teaching_assignment',
            'weekday', 'weekday_display', 'start_slot', 'duration_slots', 'end_slot',
            'room', 'room_no', 'building_code', 'building_name', 'room_type',
            'course_code', 'course_name', 'course_type', 'course_credit',
            'professor_id', 'professor_name',
            'cohort_id', 'cohort_str', 'branch_id', 'branch_code',
            'group_codes', 'created_at', 'updated_at'
        ]

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_group_codes(self, obj):
        return list(obj.meeting_instruction_groups.values_list('instruction_group__code', flat=True))


class ValidationRequestSerializer(serializers.Serializer):
    schedule_version_id = serializers.IntegerField()
    teaching_assignment_id = serializers.IntegerField()
    weekday = serializers.IntegerField(min_value=1, max_value=5)
    start_slot = serializers.IntegerField(min_value=1, max_value=8)
    duration_slots = serializers.IntegerField(min_value=1, max_value=4, default=1)
    room_id = serializers.IntegerField()
    instruction_group_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list
    )
    exclude_meeting_id = serializers.IntegerField(required=False, allow_null=True)


class SaveMeetingRequestSerializer(serializers.Serializer):
    schedule_version_id = serializers.IntegerField()
    teaching_assignment_id = serializers.IntegerField()
    weekday = serializers.IntegerField(min_value=1, max_value=5)
    start_slot = serializers.IntegerField(min_value=1, max_value=8)
    duration_slots = serializers.IntegerField(min_value=1, max_value=4, default=1)
    room_id = serializers.IntegerField()
    instruction_group_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list
    )
    existing_meeting_id = serializers.IntegerField(required=False, allow_null=True)


class ScheduleChangeAuditSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = ScheduleChangeAudit
        fields = ['id', 'schedule_version', 'meeting_id', 'action', 'before_json', 'after_json', 'user_email', 'created_at']


class HolidayCalendarSerializer(serializers.ModelSerializer):
    term_name = serializers.CharField(source='term.name', read_only=True)

    class Meta:
        model = HolidayCalendar
        fields = [
            'id', 'term', 'term_name', 'date', 'name', 'description',
            'is_academic_holiday', 'created_at', 'updated_at'
        ]


class DateOverrideSerializer(serializers.ModelSerializer):
    meeting_course = serializers.CharField(
        source='scheduled_meeting.teaching_assignment.course_offering.curriculum_item.course.code',
        read_only=True
    )
    meeting_professor = serializers.CharField(
        source='scheduled_meeting.teaching_assignment.professor.full_name',
        read_only=True
    )
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    new_room_no = serializers.CharField(source='new_room.room_no', read_only=True)

    class Meta:
        model = DateOverride
        fields = [
            'id', 'scheduled_meeting', 'meeting_course', 'meeting_professor',
            'original_date', 'new_date', 'new_start_slot', 'new_room', 'new_room_no',
            'status', 'status_display', 'reason', 'created_by_email', 'created_at', 'updated_at'
        ]
