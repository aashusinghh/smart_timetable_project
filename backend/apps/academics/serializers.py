from rest_framework import serializers
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
from apps.accounts.models import User

class DepartmentSerializer(serializers.ModelSerializer):
    branches_count = serializers.IntegerField(source='branches.count', read_only=True)

    class Meta:
        model = Department
        fields = ['id', 'code', 'name', 'description', 'is_active', 'branches_count', 'created_at', 'updated_at']


class BranchSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    department_code = serializers.CharField(source='department.code', read_only=True)

    class Meta:
        model = Branch
        fields = [
            'id', 'department', 'department_name', 'department_code',
            'code', 'name', 'degree_name', 'max_semesters', 'is_active',
            'created_at', 'updated_at'
        ]


class AcademicYearSerializer(serializers.ModelSerializer):
    terms_count = serializers.IntegerField(source='terms.count', read_only=True)

    class Meta:
        model = AcademicYear
        fields = ['id', 'name', 'start_date', 'end_date', 'is_current', 'is_active', 'terms_count', 'created_at', 'updated_at']


class AcademicTermSerializer(serializers.ModelSerializer):
    year_name = serializers.CharField(source='academic_year.name', read_only=True)
    term_type_display = serializers.CharField(source='get_term_type_display', read_only=True)

    class Meta:
        model = AcademicTerm
        fields = [
            'id', 'academic_year', 'year_name', 'name', 'term_type',
            'term_type_display', 'start_date', 'end_date', 'is_active',
            'created_at', 'updated_at'
        ]


class TimeSlotSerializer(serializers.ModelSerializer):
    session_display = serializers.CharField(source='get_session_display', read_only=True)

    class Meta:
        model = TimeSlot
        fields = [
            'id', 'slot_no', 'start_time', 'end_time', 'session',
            'session_display', 'is_active', 'created_at', 'updated_at'
        ]


class InstructionGroupSerializer(serializers.ModelSerializer):
    cohort_str = serializers.CharField(source='cohort.__str__', read_only=True)

    class Meta:
        model = InstructionGroup
        fields = ['id', 'cohort', 'cohort_str', 'code', 'name', 'size', 'is_active', 'created_at', 'updated_at']


class CohortSerializer(serializers.ModelSerializer):
    branch_code = serializers.CharField(source='branch.code', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    term_name = serializers.CharField(source='term.name', read_only=True)
    instruction_groups = InstructionGroupSerializer(many=True, read_only=True)

    class Meta:
        model = Cohort
        fields = [
            'id', 'branch', 'branch_code', 'branch_name', 'term', 'term_name',
            'semester_no', 'section_code', 'student_count', 'is_active',
            'instruction_groups', 'created_at', 'updated_at'
        ]

    def validate(self, data):
        branch = data.get('branch') or getattr(self.instance, 'branch', None)
        sem_no = data.get('semester_no', getattr(self.instance, 'semester_no', None))
        if branch and sem_no and sem_no > branch.max_semesters:
            raise serializers.ValidationError({
                'semester_no': f"Semester {sem_no} exceeds maximum allowed ({branch.max_semesters}) for branch {branch.code}."
            })
        return data


class CourseDeliveryRuleSerializer(serializers.ModelSerializer):
    total_contact_hours = serializers.IntegerField(read_only=True)

    class Meta:
        model = CourseDeliveryRule
        fields = [
            'id', 'course', 'weekly_meetings', 'duration_slots',
            'preferred_room_type', 'total_contact_hours', 'created_at', 'updated_at'
        ]
        extra_kwargs = {'course': {'required': False}}


class CourseSerializer(serializers.ModelSerializer):
    department_code = serializers.CharField(source='department.code', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    branch_code = serializers.CharField(source='branch.code', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    professor_name = serializers.CharField(source='professor.full_name', read_only=True)
    professor_email = serializers.CharField(source='professor.email', read_only=True)
    course_type_display = serializers.CharField(source='get_course_type_display', read_only=True)
    delivery_rule = CourseDeliveryRuleSerializer(required=False)

    class Meta:
        model = Course
        fields = [
            'id', 'department', 'department_code', 'department_name',
            'branch', 'branch_code', 'branch_name', 'semester',
            'professor', 'professor_name', 'professor_email',
            'code', 'name', 'credit', 'course_type', 'course_type_display',
            'description', 'is_active', 'delivery_rule', 'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        rule_data = validated_data.pop('delivery_rule', None)
        branch = validated_data.get('branch')
        if branch and not validated_data.get('department'):
            validated_data['department'] = branch.department

        course = Course.objects.create(**validated_data)

        if rule_data:
            CourseDeliveryRule.objects.create(course=course, **rule_data)
        else:
            # Default rule based on course type & credit
            if course.course_type == Course.CourseType.LAB:
                CourseDeliveryRule.objects.create(
                    course=course,
                    weekly_meetings=2,
                    duration_slots=3,
                    preferred_room_type='COMPUTER_LAB'
                )
            else:
                CourseDeliveryRule.objects.create(
                    course=course,
                    weekly_meetings=course.credit,
                    duration_slots=1,
                    preferred_room_type='CLASSROOM'
                )

        # Auto-link to CurriculumItem for the branch and semester if branch provided
        if course.branch and course.semester:
            CurriculumItem.objects.get_or_create(
                branch=course.branch,
                semester_no=course.semester,
                course=course,
                defaults={'is_elective': False}
            )

        # If professor specified, sync teaching assignment to any existing offerings
        if course.professor:
            for off in CourseOffering.objects.filter(curriculum_item__course=course):
                TeachingAssignment.objects.update_or_create(
                    course_offering=off,
                    defaults={'professor': course.professor, 'is_primary': True}
                )

        return course

    def update(self, instance, validated_data):
        rule_data = validated_data.pop('delivery_rule', None)
        branch = validated_data.get('branch', instance.branch)
        if branch and not validated_data.get('department') and not instance.department:
            validated_data['department'] = branch.department

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if rule_data:
            CourseDeliveryRule.objects.update_or_create(
                course=instance,
                defaults=rule_data
            )

        if instance.branch and instance.semester:
            CurriculumItem.objects.get_or_create(
                branch=instance.branch,
                semester_no=instance.semester,
                course=instance,
                defaults={'is_elective': False}
            )

        if instance.professor:
            for off in CourseOffering.objects.filter(curriculum_item__course=instance):
                TeachingAssignment.objects.update_or_create(
                    course_offering=off,
                    defaults={'professor': instance.professor, 'is_primary': True}
                )

        return instance


class CurriculumItemSerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source='course.code', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    course_type = serializers.CharField(source='course.course_type', read_only=True)
    course_credit = serializers.IntegerField(source='course.credit', read_only=True)
    branch_code = serializers.CharField(source='branch.code', read_only=True)

    class Meta:
        model = CurriculumItem
        fields = [
            'id', 'branch', 'branch_code', 'semester_no', 'course',
            'course_code', 'course_name', 'course_type', 'course_credit',
            'is_elective', 'is_active', 'created_at', 'updated_at'
        ]

    def validate(self, data):
        branch = data.get('branch') or getattr(self.instance, 'branch', None)
        sem_no = data.get('semester_no', getattr(self.instance, 'semester_no', None))
        if branch and sem_no and sem_no > branch.max_semesters:
            raise serializers.ValidationError({
                'semester_no': f"Semester {sem_no} exceeds maximum allowed ({branch.max_semesters}) for branch {branch.code}."
            })
        return data


class CourseOfferingSerializer(serializers.ModelSerializer):
    term_name = serializers.CharField(source='term.name', read_only=True)
    cohort_str = serializers.CharField(source='cohort.__str__', read_only=True)
    course_code = serializers.CharField(source='curriculum_item.course.code', read_only=True)
    course_name = serializers.CharField(source='curriculum_item.course.name', read_only=True)
    course_type = serializers.CharField(source='curriculum_item.course.course_type', read_only=True)
    course_credit = serializers.IntegerField(source='curriculum_item.course.credit', read_only=True)
    semester_no = serializers.IntegerField(source='curriculum_item.semester_no', read_only=True)
    branch_id = serializers.IntegerField(source='cohort.branch_id', read_only=True)
    assignments_count = serializers.IntegerField(source='teaching_assignments.count', read_only=True)
    professor_id = serializers.SerializerMethodField()
    professor_name = serializers.SerializerMethodField()
    teaching_assignment_id = serializers.SerializerMethodField()

    class Meta:
        model = CourseOffering
        fields = [
            'id', 'term', 'term_name', 'cohort', 'cohort_str',
            'curriculum_item', 'course_code', 'course_name', 'course_type', 'course_credit',
            'semester_no', 'branch_id',
            'professor_id', 'professor_name', 'teaching_assignment_id',
            'assignments_count', 'is_active', 'created_at', 'updated_at'
        ]

    def get_teaching_assignment_id(self, obj):
        ta = obj.teaching_assignments.filter(is_active=True).first()
        return ta.id if ta else None

    def get_professor_id(self, obj):
        ta = obj.teaching_assignments.filter(is_active=True).first()
        if ta and ta.professor_id:
            return ta.professor_id
        if obj.curriculum_item and obj.curriculum_item.course and obj.curriculum_item.course.professor_id:
            return obj.curriculum_item.course.professor_id
        return None

    def get_professor_name(self, obj):
        ta = obj.teaching_assignments.filter(is_active=True).first()
        if ta and ta.professor:
            return ta.professor.full_name
        if obj.curriculum_item and obj.curriculum_item.course and obj.curriculum_item.course.professor:
            return obj.curriculum_item.course.professor.full_name
        return None

    def validate(self, data):
        term = data.get('term') or getattr(self.instance, 'term', None)
        cohort = data.get('cohort') or getattr(self.instance, 'cohort', None)
        curriculum_item = data.get('curriculum_item') or getattr(self.instance, 'curriculum_item', None)

        if cohort and term and cohort.term_id != term.id:
            raise serializers.ValidationError("Cohort's term must match offering term.")
        if cohort and curriculum_item:
            if cohort.branch_id != curriculum_item.branch_id:
                raise serializers.ValidationError("Cohort branch must match curriculum item branch.")
            if cohort.semester_no != curriculum_item.semester_no:
                raise serializers.ValidationError("Cohort semester must match curriculum item semester.")
        return data


class TeachingAssignmentSerializer(serializers.ModelSerializer):
    professor_name = serializers.CharField(source='professor.full_name', read_only=True)
    professor_email = serializers.CharField(source='professor.email', read_only=True)
    course_code = serializers.CharField(source='course_offering.curriculum_item.course.code', read_only=True)
    course_name = serializers.CharField(source='course_offering.curriculum_item.course.name', read_only=True)
    group_code = serializers.CharField(source='instruction_group.code', read_only=True)
    cohort_str = serializers.CharField(source='course_offering.cohort.__str__', read_only=True)

    class Meta:
        model = TeachingAssignment
        fields = [
            'id', 'course_offering', 'cohort_str', 'course_code', 'course_name',
            'professor', 'professor_name', 'professor_email',
            'instruction_group', 'group_code', 'is_primary', 'is_active',
            'created_at', 'updated_at'
        ]
