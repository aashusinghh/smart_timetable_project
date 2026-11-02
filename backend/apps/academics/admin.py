from django.contrib import admin
from .models import Department, Branch

class BranchInline(admin.TabularInline):
    model = Branch
    extra = 1


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active', 'created_at')
    search_fields = ('code', 'name')
    list_filter = ('is_active',)
    inlines = [BranchInline]


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'department', 'degree_name', 'max_semesters', 'is_active')
    list_filter = ('department', 'degree_name', 'is_active')
    search_fields = ('code', 'name', 'department__name')

