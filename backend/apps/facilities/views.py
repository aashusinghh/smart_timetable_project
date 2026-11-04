from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import Campus, Building, Room, RoomUnavailability
from .serializers import (
    CampusSerializer,
    BuildingSerializer,
    RoomSerializer,
    RoomUnavailabilitySerializer,
)
from apps.accounts.permissions import IsSuperAdminOrReadOnly

@extend_schema_view(
    list=extend_schema(description="List university campuses."),
    create=extend_schema(description="Create campus (Super Admin only)."),
    retrieve=extend_schema(description="Retrieve campus details."),
    update=extend_schema(description="Update campus (Super Admin only)."),
    destroy=extend_schema(description="Delete campus (Super Admin only)."),
)
class CampusViewSet(viewsets.ModelViewSet):
    queryset = Campus.objects.prefetch_related('buildings').all()
    serializer_class = CampusSerializer
    permission_classes = [IsSuperAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'name', 'address']
    ordering_fields = ['code', 'name', 'created_at']
    ordering = ['code']


@extend_schema_view(
    list=extend_schema(description="List campus buildings. Filter by ?campus=<id> or ?campus_code=<code>."),
    create=extend_schema(description="Create building (Super Admin only)."),
    retrieve=extend_schema(description="Retrieve building details."),
    update=extend_schema(description="Update building (Super Admin only)."),
    destroy=extend_schema(description="Delete building (Super Admin only)."),
)
class BuildingViewSet(viewsets.ModelViewSet):
    queryset = Building.objects.select_related('campus').prefetch_related('rooms').all()
    serializer_class = BuildingSerializer
    permission_classes = [IsSuperAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'name', 'campus__code', 'campus__name']
    ordering_fields = ['campus__code', 'code', 'name']
    ordering = ['campus__code', 'code']

    def get_queryset(self):
        qs = super().get_queryset()
        campus_id = self.request.query_params.get('campus')
        campus_code = self.request.query_params.get('campus_code')
        if campus_id:
            qs = qs.filter(campus_id=campus_id)
        if campus_code:
            qs = qs.filter(campus__code__iexact=campus_code)
        return qs


@extend_schema_view(
    list=extend_schema(description="List rooms. Filter by ?building=<id>, ?room_type=<type>, ?min_capacity=<cap>."),
    create=extend_schema(description="Create room (Super Admin only)."),
    retrieve=extend_schema(description="Retrieve room details."),
    update=extend_schema(description="Update room (Super Admin only)."),
    destroy=extend_schema(description="Delete room (Super Admin only)."),
)
class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.select_related('building__campus').all()
    serializer_class = RoomSerializer
    permission_classes = [IsSuperAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['room_no', 'name', 'building__code', 'building__name']
    ordering_fields = ['building__code', 'room_no', 'capacity', 'room_type']
    ordering = ['building__code', 'room_no']

    def get_queryset(self):
        qs = super().get_queryset()
        building_id = self.request.query_params.get('building')
        building_code = self.request.query_params.get('building_code')
        room_type = self.request.query_params.get('room_type')
        min_cap = self.request.query_params.get('min_capacity')

        if building_id:
            qs = qs.filter(building_id=building_id)
        if building_code:
            qs = qs.filter(building__code__iexact=building_code)
        if room_type:
            qs = qs.filter(room_type=room_type)
        if min_cap:
            try:
                qs = qs.filter(capacity__gte=int(min_cap))
            except ValueError:
                pass
        return qs

    @extend_schema(
        description="Get or add unavailability blocks for this room.",
        responses={200: RoomUnavailabilitySerializer(many=True)},
    )
    @action(detail=True, methods=['get', 'post'], url_path='unavailability')
    def unavailability(self, request, pk=None):
        room = self.get_object()
        if request.method == 'GET':
            items = room.unavailabilities.all()
            serializer = RoomUnavailabilitySerializer(items, many=True)
            return Response(serializer.data)

        # POST: add unavailability
        if not (request.user.is_superuser or request.user.has_role('SUPER_ADMIN')):
            return Response({'detail': 'Super Admin permission required.'}, status=status.HTTP_403_FORBIDDEN)

        data = request.data.copy()
        data['room'] = room.id
        serializer = RoomUnavailabilitySerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RoomUnavailabilityViewSet(viewsets.ModelViewSet):
    queryset = RoomUnavailability.objects.select_related('room__building').all()
    serializer_class = RoomUnavailabilitySerializer
    permission_classes = [IsSuperAdminOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        room_id = self.request.query_params.get('room')
        if room_id:
            qs = qs.filter(room_id=room_id)
        return qs
