from django.contrib import admin
from .models import AutoScheduleProposal

@admin.register(AutoScheduleProposal)
class AutoScheduleProposalAdmin(admin.ModelAdmin):
    list_display = ('id', 'schedule_version', 'solver_status', 'quality_score', 'status', 'created_by', 'created_at')
    list_filter = ('status', 'solver_status', 'created_at')
    search_fields = ('schedule_version__name', 'schedule_version__term__name')
    readonly_fields = ('created_at', 'updated_at')

