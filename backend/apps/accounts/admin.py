from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, UserRoleAssignment, ProfessorProfile

class UserRoleAssignmentInline(admin.TabularInline):
    model = UserRoleAssignment
    extra = 1
    autocomplete_fields = ['branch']


class ProfessorProfileInline(admin.StackedInline):
    model = ProfessorProfile
    extra = 0
    can_delete = True


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'full_name', 'employee_code', 'is_staff', 'is_superuser', 'is_active', 'created_at')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'full_name', 'employee_code')
    ordering = ('email',)
    inlines = [UserRoleAssignmentInline, ProfessorProfileInline]

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'employee_code')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    readonly_fields = ('created_at', 'updated_at')

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'employee_code', 'password1', 'password2', 'is_staff', 'is_superuser'),
        }),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'created_at')
    search_fields = ('code', 'name')
    ordering = ('code',)


@admin.register(UserRoleAssignment)
class UserRoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'branch', 'created_at')
    list_filter = ('role', 'branch')
    search_fields = ('user__email', 'user__full_name')


@admin.register(ProfessorProfile)
class ProfessorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'designation', 'department', 'max_hours_per_day')
    list_filter = ('department', 'designation')
    search_fields = ('user__email', 'user__full_name', 'department__name')

