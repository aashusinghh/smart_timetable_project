from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
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
from .serializers import (
    DepartmentSerializer,
    BranchSerializer,
    AcademicYearSerializer,
    AcademicTermSerializer,
    TimeSlotSerializer,
    CohortSerializer,
    InstructionGroupSerializer,
    CourseSerializer,
    CourseDeliveryRuleSerializer,
    CurriculumItemSerializer,
    CourseOfferingSerializer,
    TeachingAssignmentSerializer,
)
from apps.accounts.permissions import IsSuperAdminOrReadOnly, IsBranchCoordinator

@extend_schema_view(
    list=extend_schema(description="List all active academic departments."),
    create=extend_schema(description="Create a new academic department (Super Admin only)."),
    retrieve=extend_schema(description="Retrieve academic department details."),
    update=extend_schema(description="Update academic department (Super Admin only)."),
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


@extend_schema_view(
    list=extend_schema(description="List academic years."),
    create=extend_schema(description="Create academic year (Super Admin only)."),
)
class AcademicYearViewSet(viewsets.ModelViewSet):
    queryset = AcademicYear.objects.prefetch_related('terms').all()
    serializer_class = AcademicYearSerializer
    permission_classes = [IsSuperAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['start_date', 'name']
    ordering = ['-start_date']


@extend_schema_view(
    list=extend_schema(description="List academic terms. Filter by ?academic_year=<id> or ?is_active=true."),
    create=extend_schema(description="Create academic term (Super Admin only)."),
)
class AcademicTermViewSet(viewsets.ModelViewSet):
    queryset = AcademicTerm.objects.select_related('academic_year').all()
    serializer_class = AcademicTermSerializer
    permission_classes = [IsSuperAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'academic_year__name']
    ordering_fields = ['start_date', 'name']
    ordering = ['-start_date']

    def get_queryset(self):
        qs = super().get_queryset()
        year_id = self.request.query_params.get('academic_year')
        is_active = self.request.query_params.get('is_active')
        if year_id:
            qs = qs.filter(academic_year_id=year_id)
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')
        return qs


@extend_schema_view(
    list=extend_schema(description="List the 8 daily university time slots."),
)
class TimeSlotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TimeSlot.objects.filter(is_active=True).order_by('slot_no')
    serializer_class = TimeSlotSerializer
    permission_classes = [IsSuperAdminOrReadOnly]
    pagination_class = None


@extend_schema_view(
    list=extend_schema(description="List cohorts (branch sections). Filter by ?branch=<id>, ?term=<id>, ?semester=<num>."),
    create=extend_schema(description="Create cohort. Validates semester_no <= branch.max_semesters."),
)
class CohortViewSet(viewsets.ModelViewSet):
    queryset = Cohort.objects.select_related('branch', 'term').prefetch_related('instruction_groups').all()
    serializer_class = CohortSerializer
    permission_classes = [IsSuperAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['section_code', 'branch__code', 'branch__name', 'term__name']
    ordering_fields = ['branch__code', 'semester_no', 'section_code']
    ordering = ['branch__code', 'semester_no', 'section_code']

    def get_queryset(self):
        qs = super().get_queryset()
        branch_id = self.request.query_params.get('branch')
        term_id = self.request.query_params.get('term')
        semester = self.request.query_params.get('semester')

        if branch_id:
            qs = qs.filter(branch_id=branch_id)
        if term_id:
            qs = qs.filter(term_id=term_id)
        if semester:
            qs = qs.filter(semester_no=semester)
        return qs

    @extend_schema(description="Create default instruction groups ('A-L1', 'A-L2' or 'ALL') for this cohort.")
    @action(detail=True, methods=['post'], url_path='generate-groups')
    def generate_groups(self, request, pk=None):
        cohort = self.get_object()
        group_type = request.data.get('type', 'SPLIT')  # 'SPLIT' or 'SINGLE'
        created = []

        if group_type == 'SINGLE':
            grp, _ = InstructionGroup.objects.get_or_create(
                cohort=cohort,
                code='ALL',
                defaults={'name': 'Entire Cohort', 'size': cohort.student_count}
            )
            created.append(grp)
        else:
            half = cohort.student_count // 2
            g1, _ = InstructionGroup.objects.get_or_create(
                cohort=cohort,
                code=f"{cohort.section_code}-L1",
                defaults={'name': f"Section {cohort.section_code} Lab Group 1", 'size': half}
            )
            g2, _ = InstructionGroup.objects.get_or_create(
                cohort=cohort,
                code=f"{cohort.section_code}-L2",
                defaults={'name': f"Section {cohort.section_code} Lab Group 2", 'size': cohort.student_count - half}
            )
            created.extend([g1, g2])

        serializer = InstructionGroupSerializer(created, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class InstructionGroupViewSet(viewsets.ModelViewSet):
    queryset = InstructionGroup.objects.select_related('cohort__branch').all()
    serializer_class = InstructionGroupSerializer
    permission_classes = [IsSuperAdminOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        cohort_id = self.request.query_params.get('cohort')
        if cohort_id:
            qs = qs.filter(cohort_id=cohort_id)
        return qs


@extend_schema_view(
    list=extend_schema(description="List course catalog. Filter by ?course_type=<THEORY|LAB>, ?department=<id>."),
    create=extend_schema(description="Create course with delivery rule."),
)
class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.select_related('department', 'delivery_rule').all()
    serializer_class = CourseSerializer
    permission_classes = [IsSuperAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'name', 'department__code', 'department__name']
    ordering_fields = ['code', 'name', 'credit', 'course_type']
    ordering = ['code']

    def get_queryset(self):
        qs = super().get_queryset()
        course_type = self.request.query_params.get('course_type')
        dept_id = self.request.query_params.get('department')
        if course_type:
            qs = qs.filter(course_type=course_type)
        if dept_id:
            qs = qs.filter(department_id=dept_id)
        return qs


@extend_schema_view(
    list=extend_schema(description="List curriculum items (courses mapped to branch semesters). Filter by ?branch=<id>, ?semester=<num>."),
    create=extend_schema(description="Map course to branch semester. Validates semester <= branch.max_semesters."),
)
class CurriculumItemViewSet(viewsets.ModelViewSet):
    queryset = CurriculumItem.objects.select_related('branch', 'course', 'course__delivery_rule').all()
    serializer_class = CurriculumItemSerializer
    permission_classes = [IsSuperAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['course__code', 'course__name', 'branch__code']
    ordering_fields = ['branch__code', 'semester_no', 'course__code']
    ordering = ['branch__code', 'semester_no', 'course__code']

    def get_queryset(self):
        qs = super().get_queryset()
        branch_id = self.request.query_params.get('branch')
        semester = self.request.query_params.get('semester')
        if branch_id:
            qs = qs.filter(branch_id=branch_id)
        if semester:
            qs = qs.filter(semester_no=semester)
        return qs


@extend_schema_view(
    list=extend_schema(description="List course offerings for cohorts in an academic term. Filter by ?term=<id>, ?cohort=<id>."),
)
class CourseOfferingViewSet(viewsets.ModelViewSet):
    queryset = CourseOffering.objects.select_related(
        'term', 'cohort__branch', 'curriculum_item__course'
    ).prefetch_related('teaching_assignments').all()
    serializer_class = CourseOfferingSerializer
    permission_classes = [IsSuperAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['curriculum_item__course__code', 'curriculum_item__course__name', 'cohort__branch__code']

    def get_queryset(self):
        qs = super().get_queryset()
        term_id = self.request.query_params.get('term')
        cohort_id = self.request.query_params.get('cohort')
        branch_id = self.request.query_params.get('branch')
        if term_id:
            qs = qs.filter(term_id=term_id)
        if cohort_id:
            qs = qs.filter(cohort_id=cohort_id)
        if branch_id:
            qs = qs.filter(cohort__branch_id=branch_id)
        return qs

    @extend_schema(description="Auto-populate course offerings for a cohort based on its branch semester curriculum.")
    @action(detail=False, methods=['post'], url_path='populate-from-curriculum')
    def populate_from_curriculum(self, request):
        cohort_id = request.data.get('cohort_id')
        if not cohort_id:
            return Response({'detail': 'cohort_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cohort = Cohort.objects.select_related('branch', 'term').get(id=cohort_id)
        except Cohort.DoesNotExist:
            return Response({'detail': 'Cohort not found'}, status=status.HTTP_404_NOT_FOUND)

        curriculum_items = CurriculumItem.objects.filter(
            branch=cohort.branch,
            semester_no=cohort.semester_no,
            is_active=True
        )

        created_offerings = []
        for item in curriculum_items:
            offering, _ = CourseOffering.objects.get_or_create(
                term=cohort.term,
                cohort=cohort,
                curriculum_item=item
            )
            created_offerings.append(offering)

        serializer = CourseOfferingSerializer(created_offerings, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    list=extend_schema(description="List teaching assignments (professor fixed allocations to course offerings). Filter by ?offering=<id>, ?professor=<id>."),
)
class TeachingAssignmentViewSet(viewsets.ModelViewSet):
    queryset = TeachingAssignment.objects.select_related(
        'course_offering__cohort__branch',
        'course_offering__curriculum_item__course',
        'professor',
        'instruction_group'
    ).all()
    serializer_class = TeachingAssignmentSerializer
    permission_classes = [IsSuperAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['professor__full_name', 'professor__email', 'course_offering__curriculum_item__course__code']

    def get_queryset(self):
        qs = super().get_queryset()
        offering_id = self.request.query_params.get('offering')
        professor_id = self.request.query_params.get('professor')
        cohort_id = self.request.query_params.get('cohort')
        term_id = self.request.query_params.get('term')

        if offering_id:
            qs = qs.filter(course_offering_id=offering_id)
        if professor_id:
            qs = qs.filter(professor_id=professor_id)
        if cohort_id:
            qs = qs.filter(course_offering__cohort_id=cohort_id)
        if term_id:
            qs = qs.filter(course_offering__term_id=term_id)
        return qs
