from django.db import models

class ProfessorUnavailability(models.Model):
    professor = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='unavailabilities'
    )
    weekday = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="1=Monday, 2=Tuesday, ..., 5=Friday"
    )
    specific_date = models.DateField(
        null=True,
        blank=True,
        help_text="Optional specific calendar date"
    )
    start_slot = models.PositiveSmallIntegerField(default=1, help_text="Start slot (1..8)")
    end_slot = models.PositiveSmallIntegerField(default=8, help_text="End slot (1..8)")
    reason = models.CharField(max_length=255, default='Personal / Committee Meeting')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'professor_unavailability'
        ordering = ['professor', 'specific_date', 'weekday', 'start_slot']

    def __str__(self):
        target = f"{self.specific_date}" if self.specific_date else f"Weekday {self.weekday}"
        return f"Prof {self.professor.full_name} unavailable on {target} (Slots {self.start_slot}-{self.end_slot}): {self.reason}"
