from django.db import models
from django.conf import settings

class AutoScheduleProposal(models.Model):
    class ProposalStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending Review'
        COMMITTED = 'COMMITTED', 'Committed'
        DISCARDED = 'DISCARDED', 'Discarded'
        FAILED = 'FAILED', 'Failed'

    class SolverStatus(models.TextChoices):
        OPTIMAL = 'OPTIMAL', 'Optimal'
        FEASIBLE = 'FEASIBLE', 'Feasible'
        INFEASIBLE = 'INFEASIBLE', 'Infeasible'
        UNKNOWN = 'UNKNOWN', 'Unknown'
        MODEL_INVALID = 'MODEL_INVALID', 'Model Invalid'
        TIMEOUT = 'TIMEOUT', 'Timeout'

    schedule_version = models.ForeignKey(
        'timetable.ScheduleVersion',
        on_delete=models.CASCADE,
        related_name='proposals'
    )
    selected_branches = models.JSONField(
        default=list,
        help_text="Branch IDs included in this auto-scheduling run"
    )
    proposed_meetings = models.JSONField(
        default=list,
        help_text="Serialized proposed scheduled meetings"
    )
    solver_status = models.CharField(
        max_length=50,
        choices=SolverStatus.choices,
        default=SolverStatus.UNKNOWN
    )
    quality_score = models.FloatField(
        default=0.0,
        help_text="Overall schedule quality score (0.0 to 100.0)"
    )
    unscheduled_offerings = models.JSONField(
        default=list,
        help_text="List of teaching assignments/offerings that could not be scheduled with reason"
    )
    constraint_score_breakdown = models.JSONField(
        default=dict,
        help_text="Individual scores for soft constraints and penalties"
    )
    generation_metadata = models.JSONField(
        default=dict,
        help_text="Metadata including solve_time_seconds, replace_existing flag, counts, etc."
    )
    status = models.CharField(
        max_length=20,
        choices=ProposalStatus.choices,
        default=ProposalStatus.PENDING,
        db_index=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='schedule_proposals'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'auto_schedule_proposals'
        ordering = ['-created_at']

    def __str__(self):
        return f"Proposal #{self.id} for {self.schedule_version} [{self.get_solver_status_display()}] - Score: {self.quality_score:.1f} ({self.get_status_display()})"

