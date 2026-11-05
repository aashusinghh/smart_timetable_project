from rest_framework import serializers
from .models import AutoScheduleProposal


class GenerateTimetableInputSerializer(serializers.Serializer):
    branch_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list,
        help_text="Optional list of Branch IDs to schedule. If empty, all branches are scheduled."
    )
    time_limit = serializers.IntegerField(
        required=False,
        default=60,
        min_value=5,
        max_value=300,
        help_text="Solver time limit in seconds (5..300, default 60)."
    )
    replace_existing = serializers.BooleanField(
        required=False,
        default=False,
        help_text="If true, replaces existing scheduled meetings for selected branches."
    )


class TaskStatusResponseSerializer(serializers.Serializer):
    task_id = serializers.CharField()
    status = serializers.CharField()
    percentage = serializers.IntegerField()
    message = serializers.CharField(allow_blank=True, default='')
    proposal_id = serializers.IntegerField(required=False, allow_null=True)
    quality_score = serializers.FloatField(required=False, allow_null=True)
    solver_status = serializers.CharField(required=False, allow_null=True)
    placed_count = serializers.IntegerField(required=False, allow_null=True)
    unscheduled_count = serializers.IntegerField(required=False, allow_null=True)
    error = serializers.CharField(required=False, allow_null=True)
    updated_at = serializers.DateTimeField(required=False, allow_null=True)


class AutoScheduleProposalSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)

    class Meta:
        model = AutoScheduleProposal
        fields = [
            'id',
            'schedule_version',
            'selected_branches',
            'proposed_meetings',
            'solver_status',
            'quality_score',
            'unscheduled_offerings',
            'constraint_score_breakdown',
            'generation_metadata',
            'status',
            'created_by',
            'created_by_name',
            'created_by_email',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CommitProposalInputSerializer(serializers.Serializer):
    proposal_id = serializers.IntegerField(help_text="ID of the AutoScheduleProposal to commit")


class ScheduleScoreResponseSerializer(serializers.Serializer):
    overall_score = serializers.FloatField()
    breakdown = serializers.DictField()
    metrics = serializers.DictField()

