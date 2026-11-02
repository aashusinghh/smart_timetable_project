from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema_field
from .models import User, Role, UserRoleAssignment, ProfessorProfile
from apps.academics.models import Branch, Department

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'code', 'name', 'description']


class RoleAssignmentBranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ['id', 'code', 'name', 'degree_name']


class UserRoleAssignmentSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    branch = RoleAssignmentBranchSerializer(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), source='role', write_only=True
    )
    branch_id = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.all(), source='branch', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = UserRoleAssignment
        fields = ['id', 'role', 'role_id', 'branch', 'branch_id', 'created_at']


class ProfessorProfileDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'code', 'name']


class ProfessorProfileSerializer(serializers.ModelSerializer):
    department = ProfessorProfileDepartmentSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), source='department', write_only=True
    )

    class Meta:
        model = ProfessorProfile
        fields = ['id', 'designation', 'department', 'department_id', 'max_hours_per_day']


class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    role_assignments = UserRoleAssignmentSerializer(many=True, read_only=True)
    professor_profile = ProfessorProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'employee_code',
            'is_active', 'is_staff', 'is_superuser',
            'roles', 'role_assignments', 'professor_profile',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_superuser', 'created_at', 'updated_at']

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_roles(self, obj):
        return obj.get_role_codes()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email', '').strip().lower()
        password = attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError('Email and password are required.')

        user = authenticate(request=self.context.get('request'), email=email, password=password)

        if not user:
            raise serializers.ValidationError('Invalid email or password.')

        if not user.is_active:
            raise serializers.ValidationError('This user account is inactive.')

        attrs['user'] = user
        return attrs


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=False, allow_blank=True)
