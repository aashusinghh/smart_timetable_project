from django.contrib import admin
from .models import (
    Department,
    Branch,
    AcademicYear,
    AcademicTerm,
    TimeSlot,
    Cohort,
    InstructionGroup,
    Course,
    CourseDeliveryRule,
    CurriculumItem,
    CourseOffering,
    TeachingAssignment,
)

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


class AcademicTermInline(admin.TabularInline):
    model = AcademicTerm
    extra = 1


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_current', 'is_active')
    list_filter = ('is_current', 'is_active')
    search_fields = ('name',)
    inlines = [AcademicTermInline]


@admin.register(AcademicTerm)
class AcademicTermAdmin(admin.ModelAdmin):
    list_display = ('name', 'academic_year', 'term_type', 'start_date', 'end_date', 'is_active')
    list_filter = ('academic_year', 'term_type', 'is_active')
    search_fields = ('name',)


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('slot_no', 'start_time', 'end_time', 'session', 'is_active')
    list_filter = ('session', 'is_active')
    ordering = ('slot_no',)


class InstructionGroupInline(admin.TabularInline):
    model = InstructionGroup
    extra = 1


@admin.register(Cohort)
class CohortAdmin(admin.ModelAdmin):
    list_display = ('branch', 'term', 'semester_no', 'section_code', 'student_count', 'is_active')
    list_filter = ('term', 'branch', 'semester_no', 'is_active')
    search_fields = ('section_code', 'branch__code', 'branch__name')
    inlines = [InstructionGroupInline]


@admin.register(InstructionGroup)
class InstructionGroupAdmin(admin.ModelAdmin):
    list_display = ('cohort', 'code', 'name', 'size', 'is_active')
    list_filter = ('cohort__branch', 'cohort__term')
    search_fields = ('code', 'name', 'cohort__section_code')


class CourseDeliveryRuleInline(admin.StackedInline):
    model = CourseDeliveryRule
    can_delete = False


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'department', 'credit', 'course_type', 'is_active')
    list_filter = ('course_type', 'department', 'is_active')
    search_fields = ('code', 'name')
    inlines = [CourseDeliveryRuleInline]


@admin.register(CurriculumItem)
class CurriculumItemAdmin(admin.ModelAdmin):
    list_display = ('branch', 'semester_no', 'course', 'is_elective', 'is_active')
    list_filter = ('branch', 'semester_no', 'is_elective', 'is_active')
    search_fields = ('course__code', 'course__name', 'branch__code')


class TeachingAssignmentInline(admin.TabularInline):
    model = TeachingAssignment
    extra = 1


@admin.register(CourseOffering)
class CourseOfferingAdmin(admin.ModelAdmin):
    list_display = ('term', 'cohort', 'curriculum_item', 'is_active')
    list_filter = ('term', 'cohort__branch')
    inlines = [TeachingAssignmentInline]


@admin.register(TeachingAssignment)
class TeachingAssignmentAdmin(admin.ModelAdmin):
    list_display = ('course_offering', 'professor', 'instruction_group', 'is_primary', 'is_active')
    list_filter = ('professor', 'is_primary', 'is_active')
    search_fields = ('professor__full_name', 'course_offering__curriculum_item__course__code')
