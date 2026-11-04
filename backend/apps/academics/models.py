from django.db import models
from django.core.exceptions import ValidationError

class Department(models.Model):
    code = models.CharField(max_length=20, unique=True, db_index=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'departments'
        ordering = ['code']

    def __str__(self):
        return f"{self.name} ({self.code})"


class Branch(models.Model):
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='branches'
    )
    code = models.CharField(max_length=30, db_index=True)
    name = models.CharField(max_length=150)
    degree_name = models.CharField(max_length=100, default='B.Tech')
    max_semesters = models.PositiveIntegerField(default=8)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'branches'
        unique_together = ('department', 'code')
        ordering = ['department', 'code']

    def __str__(self):
        return f"{self.name} ({self.code}) - {self.degree_name}"


class AcademicYear(models.Model):
    name = models.CharField(max_length=50, unique=True, db_index=True, help_text="e.g. '2026-27'")
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'academic_years'
        ordering = ['-start_date']

    def __str__(self):
        return self.name

    def clean(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError({'end_date': 'End date must be after start date.'})


class AcademicTerm(models.Model):
    class TermType(models.TextChoices):
        ODD = 'ODD', 'Odd Semester'
        EVEN = 'EVEN', 'Even Semester'
        SUMMER = 'SUMMER', 'Summer Term'

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='terms'
    )
    name = models.CharField(max_length=100, help_text="e.g. 'Odd Semester 2026-27'")
    term_type = models.CharField(
        max_length=20,
        choices=TermType.choices,
        default=TermType.ODD
    )
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'academic_terms'
        unique_together = ('academic_year', 'name')
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.name} ({self.academic_year.name})"

    def clean(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError({'end_date': 'End date must be after start date.'})


class TimeSlot(models.Model):
    class Session(models.TextChoices):
        MORNING = 'MORNING', 'Morning Session'
        AFTERNOON = 'AFTERNOON', 'Afternoon Session'

    slot_no = models.PositiveSmallIntegerField(unique=True, db_index=True, help_text="Slot index 1 through 8")
    start_time = models.TimeField()
    end_time = models.TimeField()
    session = models.CharField(max_length=20, choices=Session.choices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'time_slots'
        ordering = ['slot_no']

    def __str__(self):
        start_str = self.start_time.strftime('%H:%M') if hasattr(self.start_time, 'strftime') else str(self.start_time)
        end_str = self.end_time.strftime('%H:%M') if hasattr(self.end_time, 'strftime') else str(self.end_time)
        return f"Slot {self.slot_no} ({start_str} - {end_str}) [{self.get_session_display()}]"


class Cohort(models.Model):
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='cohorts'
    )
    term = models.ForeignKey(
        AcademicTerm,
        on_delete=models.CASCADE,
        related_name='cohorts'
    )
    semester_no = models.PositiveIntegerField(help_text="Current semester number (1..branch.max_semesters)")
    section_code = models.CharField(max_length=10, default='A', help_text="Section such as A, B, C")
    student_count = models.PositiveIntegerField(default=60)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cohorts'
        unique_together = ('branch', 'term', 'semester_no', 'section_code')
        ordering = ['branch', 'semester_no', 'section_code']

    def __str__(self):
        return f"{self.branch.code} Sem {self.semester_no} Sec {self.section_code} ({self.term.name})"

    def clean(self):
        super().clean()
        if self.branch_id and self.semester_no:
            if self.semester_no > self.branch.max_semesters:
                raise ValidationError({
                    'semester_no': f"Semester {self.semester_no} exceeds maximum allowed ({self.branch.max_semesters}) for branch {self.branch.code}."
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class InstructionGroup(models.Model):
    cohort = models.ForeignKey(
        Cohort,
        on_delete=models.CASCADE,
        related_name='instruction_groups'
    )
    code = models.CharField(max_length=50, help_text="e.g. 'A-L1', 'A-L2', 'ALL'")
    name = models.CharField(max_length=100, blank=True, default='')
    size = models.PositiveIntegerField(default=30)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'instruction_groups'
        unique_together = ('cohort', 'code')
        ordering = ['cohort', 'code']

    def __str__(self):
        return f"{self.cohort} [{self.code}] ({self.size} students)"


class Course(models.Model):
    class CourseType(models.TextChoices):
        THEORY = 'THEORY', 'Theory'
        LAB = 'LAB', 'Practical / Laboratory'
        PROJECT = 'PROJECT', 'Project Work'
        SEMINAR = 'SEMINAR', 'Seminar'

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses'
    )
    code = models.CharField(max_length=30, unique=True, db_index=True)
    name = models.CharField(max_length=150)
    credit = models.PositiveIntegerField(default=3)
    course_type = models.CharField(
        max_length=20,
        choices=CourseType.choices,
        default=CourseType.THEORY,
        db_index=True
    )
    description = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'courses'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name} ({self.get_course_type_display()}, {self.credit}cr)"


class CourseDeliveryRule(models.Model):
    course = models.OneToOneField(
        Course,
        on_delete=models.CASCADE,
        related_name='delivery_rule'
    )
    weekly_meetings = models.PositiveIntegerField(
        default=3,
        help_text="Weekly meeting occurrences (e.g. 3 for 3x1hr theory, 2 for 2x3hr lab)"
    )
    duration_slots = models.PositiveIntegerField(
        default=1,
        help_text="Duration per meeting in 1-hour slots (e.g. 1 for theory, 3 for lab)"
    )
    preferred_room_type = models.CharField(
        max_length=50,
        blank=True,
        default='CLASSROOM'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'course_delivery_rules'

    def __str__(self):
        return f"Rule for {self.course.code}: {self.weekly_meetings} meetings x {self.duration_slots} slot(s) = {self.total_contact_hours} contact hrs/wk"

    @property
    def total_contact_hours(self):
        return self.weekly_meetings * self.duration_slots


class CurriculumItem(models.Model):
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='curriculum_items'
    )
    semester_no = models.PositiveIntegerField()
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='curriculum_inclusions'
    )
    is_elective = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'curriculum_items'
        unique_together = ('branch', 'semester_no', 'course')
        ordering = ['branch', 'semester_no', 'course__code']

    def __str__(self):
        return f"{self.branch.code} Sem {self.semester_no} -> {self.course.code}"

    def clean(self):
        super().clean()
        if self.branch_id and self.semester_no:
            if self.semester_no > self.branch.max_semesters:
                raise ValidationError({
                    'semester_no': f"Semester {self.semester_no} exceeds maximum ({self.branch.max_semesters}) for branch {self.branch.code}."
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class CourseOffering(models.Model):
    term = models.ForeignKey(
        AcademicTerm,
        on_delete=models.CASCADE,
        related_name='course_offerings'
    )
    cohort = models.ForeignKey(
        Cohort,
        on_delete=models.CASCADE,
        related_name='offerings'
    )
    curriculum_item = models.ForeignKey(
        CurriculumItem,
        on_delete=models.CASCADE,
        related_name='offerings'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'course_offerings'
        unique_together = ('term', 'cohort', 'curriculum_item')
        ordering = ['term', 'cohort', 'curriculum_item']

    def __str__(self):
        return f"{self.cohort} :: {self.curriculum_item.course.code} ({self.term.name})"

    def clean(self):
        super().clean()
        if self.cohort_id and self.term_id and self.cohort.term_id != self.term_id:
            raise ValidationError("Cohort's term must match the offering term.")
        if self.cohort_id and self.curriculum_item_id:
            if self.cohort.branch_id != self.curriculum_item.branch_id:
                raise ValidationError("Cohort branch must match curriculum item branch.")
            if self.cohort.semester_no != self.curriculum_item.semester_no:
                raise ValidationError("Cohort semester must match curriculum item semester.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class TeachingAssignment(models.Model):
    course_offering = models.ForeignKey(
        CourseOffering,
        on_delete=models.CASCADE,
        related_name='teaching_assignments'
    )
    professor = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='teaching_assignments'
    )
    instruction_group = models.ForeignKey(
        InstructionGroup,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='teaching_assignments',
        help_text="Optional: specific lab group. If null, professor teaches the whole cohort."
    )
    is_primary = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'teaching_assignments'
        unique_together = ('course_offering', 'professor', 'instruction_group')
        ordering = ['course_offering', 'professor']

    def __str__(self):
        grp = f" [{self.instruction_group.code}]" if self.instruction_group else " [Entire Cohort]"
        return f"{self.course_offering} -> Prof {self.professor.full_name}{grp}"
