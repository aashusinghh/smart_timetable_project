from rest_framework import viewsets, filters
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import Department, Branch
from .serializers import DepartmentSerializer, BranchSerializer
from apps.accounts.permissions import IsSuperAdminOrReadOnly

@extend_schema_view(
    list=extend_schema(description="List all active academic departments."),
    create=extend_schema(description="Create a new academic department (Super Admin only)."),
    retrieve=extend_schema(description="Retrieve academic department details."),
    update=extend_schema(description="Update academic department (Super Admin only)."),
    partial_update=extend_schema(description="Partially update academic department (Super Admin only)."),
    destroy=extend_schema(description="Delete academic department (Super Admin only)."),
)
class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all().prefetch_related('branches')
    serializer_class = DepartmentSerializer
    permission_classes = [IsSuperAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['code', 'name', 'created_at']
    ordering = ['code']


@extend_schema_view(
    list=extend_schema(description="List academic branches. Can filter by ?department=<id> or ?department_code=<code>."),
    create=extend_schema(description="Create a new academic branch (Super Admin only)."),
    retrieve=extend_schema(description="Retrieve academic branch details."),
    update=extend_schema(description="Update academic branch (Super Admin only)."),
    partial_update=extend_schema(description="Partially update academic branch (Super Admin only)."),
    destroy=extend_schema(description="Delete academic branch (Super Admin only)."),
)
class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.select_related('department').all()
    serializer_class = BranchSerializer
    permission_classes = [IsSuperAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'name', 'degree_name', 'department__code', 'department__name']
    ordering_fields = ['code', 'name', 'department', 'max_semesters', 'created_at']
    ordering = ['department__code', 'code']

    def get_queryset(self):
        qs = super().get_queryset()
        dept_id = self.request.query_params.get('department') or self.request.query_params.get('department_id')
        dept_code = self.request.query_params.get('department_code')
        if dept_id:
            qs = qs.filter(department_id=dept_id)
        if dept_code:
            qs = qs.filter(department__code__iexact=dept_code)
        return qs

