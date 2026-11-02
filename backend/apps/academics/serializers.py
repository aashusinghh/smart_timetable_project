from rest_framework import serializers
from .models import Department, Branch

class DepartmentSerializer(serializers.ModelSerializer):
    branches_count = serializers.IntegerField(source='branches.count', read_only=True)

    class Meta:
        model = Department
        fields = [
            'id', 'code', 'name', 'description',
            'branches_count', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'branches_count', 'created_at', 'updated_at']

    def validate_code(self, value):
        return value.strip().upper()


class BranchSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    department_code = serializers.CharField(source='department.code', read_only=True)

    class Meta:
        model = Branch
        fields = [
            'id', 'department', 'department_name', 'department_code',
            'code', 'name', 'degree_name', 'max_semesters',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'department_name', 'department_code', 'created_at', 'updated_at']

    def validate_code(self, value):
        return value.strip().upper()

    def validate_max_semesters(self, value):
        if value < 1 or value > 12:
            raise serializers.ValidationError('Max semesters must be between 1 and 12.')
        return value

