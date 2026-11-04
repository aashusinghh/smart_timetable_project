from django.db import transaction
from rest_framework import serializers
from apps.accounts.models import User, Role, UserRoleAssignment, ProfessorProfile
from apps.academics.models import Department
from .models import ProfessorUnavailability

class ProfessorUnavailabilitySerializer(serializers.ModelSerializer):
    professor_name = serializers.CharField(source='professor.full_name', read_only=True)

    class Meta:
        model = ProfessorUnavailability
        fields = [
            'id', 'professor', 'professor_name', 'weekday', 'specific_date',
            'start_slot', 'end_slot', 'reason', 'created_at', 'updated_at'
        ]
        extra_kwargs = {'professor': {'required': False}}


class ProfessorListSerializer(serializers.ModelSerializer):
    designation = serializers.CharField(source='professor_profile.designation', read_only=True)
    department_id = serializers.IntegerField(source='professor_profile.department_id', read_only=True)
    department_code = serializers.CharField(source='professor_profile.department.code', read_only=True)
    department_name = serializers.CharField(source='professor_profile.department.name', read_only=True)
    max_hours_per_day = serializers.IntegerField(source='professor_profile.max_hours_per_day', read_only=True)
    roles = serializers.SerializerMethodField()
    assignments_count = serializers.IntegerField(source='teaching_assignments.count', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'employee_code', 'is_active',
            'designation', 'department_id', 'department_code', 'department_name',
            'max_hours_per_day', 'roles', 'assignments_count', 'created_at'
        ]

    def get_roles(self, obj):
        return obj.get_role_codes()


class CreateProfessorSerializer(serializers.Serializer):
    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=150)
    employee_code = serializers.CharField(max_length=50, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False, default='ProfessorPassword123!')
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all())
    designation = serializers.CharField(max_length=100, default='Assistant Professor')
    max_hours_per_day = serializers.IntegerField(default=6)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    @transaction.atomic
    def create(self, validated_data):
        email = validated_data['email']
        full_name = validated_data['full_name']
        employee_code = validated_data.get('employee_code') or None
        password = validated_data.get('password', 'ProfessorPassword123!')
        dept = validated_data['department']
        designation = validated_data.get('designation', 'Assistant Professor')
        max_hours = validated_data.get('max_hours_per_day', 6)

        user = User.objects.create_user(
            email=email,
            password=password,
            full_name=full_name,
            employee_code=employee_code
        )

        prof_role, _ = Role.objects.get_or_create(
            code=Role.Code.PROFESSOR,
            defaults={'name': 'Professor', 'description': 'Faculty member'}
        )
        UserRoleAssignment.objects.get_or_create(user=user, role=prof_role)

        ProfessorProfile.objects.create(
            user=user,
            department=dept,
            designation=designation,
            max_hours_per_day=max_hours
        )

        return user
