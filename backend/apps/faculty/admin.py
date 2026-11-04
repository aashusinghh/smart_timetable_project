from django.contrib import admin
from .models import ProfessorUnavailability

@admin.register(ProfessorUnavailability)
class ProfessorUnavailabilityAdmin(admin.ModelAdmin):
    list_display = ('professor', 'weekday', 'specific_date', 'start_slot', 'end_slot', 'reason')
    list_filter = ('weekday', 'professor')
    search_fields = ('professor__full_name', 'professor__email', 'reason')
