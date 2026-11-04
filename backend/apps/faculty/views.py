from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
from apps.accounts.models import User, Role, ProfessorProfile
from apps.accounts.permissions import IsSuperAdminOrReadOnly
from .models import ProfessorUnavailability
from .serializers import (
    ProfessorListSerializer,
    CreateProfessorSerializer,
    ProfessorUnavailabilitySerializer,
)

@extend_schema_view(
    list=extend_schema(description="List faculty members / professors. Filter by ?department=<id>."),
    retrieve=extend_schema(description="Retrieve professor details and teaching load."),
    create=extend_schema(
        request=CreateProfessorSerializer,
        responses={201: ProfessorListSerializer},
        description="Create a new professor user account with department profile in one atomic operation (Super Admin only)."
    ),
)
class ProfessorViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(
        role_assignments__role__code=Role.Code.PROFESSOR
    ).select_related('professor_profile__department').distinct()
    permission_classes = [IsSuperAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['full_name', 'email', 'employee_code', 'professor_profile__department__code', 'professor_profile__department__name']
    ordering_fields = ['full_name', 'email', 'created_at']
    ordering = ['full_name']

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateProfessorSerializer
        return ProfessorListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        dept_id = self.request.query_params.get('department')
        if dept_id:
            qs = qs.filter(professor_profile__department_id=dept_id)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = CreateProfessorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        output_serializer = ProfessorListSerializer(user)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        user = self.get_object()
        user_fields = ['full_name', 'employee_code', 'is_active']
        for field in user_fields:
            if field in request.data:
                setattr(user, field, request.data[field])
        user.save()

        profile = getattr(user, 'professor_profile', None)
        if profile:
            if 'designation' in request.data:
                profile.designation = request.data['designation']
            if 'max_hours_per_day' in request.data:
                profile.max_hours_per_day = int(request.data['max_hours_per_day'])
            if 'department' in request.data:
                profile.department_id = request.data['department']
            profile.save()

        output_serializer = ProfessorListSerializer(user)
        return Response(output_serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        description="Get or add unavailable time blocks for this professor.",
        responses={200: ProfessorUnavailabilitySerializer(many=True)},
    )
    @action(detail=True, methods=['get', 'post'], url_path='unavailability')
    def unavailability(self, request, pk=None):
        prof = self.get_object()
        if request.method == 'GET':
            items = prof.unavailabilities.all()
            serializer = ProfessorUnavailabilitySerializer(items, many=True)
            return Response(serializer.data)

        # POST: create unavailability
        data = request.data.copy()
        data['professor'] = prof.id
        serializer = ProfessorUnavailabilitySerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(professor=prof)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProfessorUnavailabilityViewSet(viewsets.ModelViewSet):
    queryset = ProfessorUnavailability.objects.select_related('professor').all()
    serializer_class = ProfessorUnavailabilitySerializer
    permission_classes = [IsSuperAdminOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        prof_id = self.request.query_params.get('professor')
        if prof_id:
            qs = qs.filter(professor_id=prof_id)
        return qs
