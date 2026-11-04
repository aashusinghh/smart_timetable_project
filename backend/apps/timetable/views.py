from rest_framework import viewsets, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.shortcuts import get_object_or_404
from django.db.models import Q

from apps.accounts.permissions import IsSuperAdminOrReadOnly, IsSuperAdmin
from apps.accounts.models import User, Role
from apps.academics.models import TeachingAssignment, InstructionGroup, AcademicTerm, Branch, TimeSlot
from apps.facilities.models import Room, RoomUnavailability
from apps.faculty.models import ProfessorUnavailability

from .models import (
    ScheduleVersion,
    ScheduledMeeting,
    ProfessorSlotReservation,
    RoomSlotReservation,
    GroupSlotReservation,
    ScheduleChangeAudit,
    HolidayCalendar,
    DateOverride,
)
from .serializers import (
    ScheduleVersionSerializer,
    ScheduledMeetingSerializer,
    ValidationRequestSerializer,
    SaveMeetingRequestSerializer,
    ScheduleChangeAuditSerializer,
    HolidayCalendarSerializer,
    DateOverrideSerializer,
)
from .services.validator import TimetableValidator
from .services.reservation_service import TimetableReservationService, ConflictException
from .services.publication_service import TimetablePublicationService, PublicationConflictException


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@extend_schema_view(
    list=extend_schema(description="List timetable schedule versions for terms."),
    create=extend_schema(description="Create a new schedule draft version for an academic term."),
)
class ScheduleVersionViewSet(viewsets.ModelViewSet):
    queryset = ScheduleVersion.objects.select_related('term__academic_year', 'created_by').prefetch_related('meetings').all()
    serializer_class = ScheduleVersionSerializer
    permission_classes = [IsSuperAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'term__name']
    ordering_fields = ['term', 'version_no', 'revision', 'created_at']
    ordering = ['term', '-version_no']

    def get_permissions(self):
        if self.action in ['submit_review', 'validate_sweep', 'retrieve', 'list']:
            return [IsAuthenticated()]
        return [IsSuperAdminOrReadOnly()]

    def get_queryset(self):
        qs = super().get_queryset()
        term_id = self.request.query_params.get('term')
        version_status = self.request.query_params.get('status')
        if term_id:
            qs = qs.filter(term_id=term_id)
        if version_status:
            qs = qs.filter(status=version_status)
        return qs

    def perform_create(self, serializer):
        term = serializer.validated_data['term']
        latest = ScheduleVersion.objects.filter(term=term).order_by('-version_no').first()
        v_no = (latest.version_no + 1) if latest else 1
        name = serializer.validated_data.get('name') or f"Draft Version {v_no}"
        serializer.save(
            created_by=self.request.user if self.request.user.is_authenticated else None,
            version_no=v_no,
            name=name
        )

    @action(detail=True, methods=['post'], url_path='submit-review')
    def submit_review(self, request, pk=None):
        """Transition schedule version from DRAFT -> UNDER_REVIEW."""
        version = self.get_object()
        updated = TimetablePublicationService.submit_for_review(version, request.user)
        return Response(ScheduleVersionSerializer(updated).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='send-back')
    def send_back(self, request, pk=None):
        """Admin sends an UNDER_REVIEW version back to DRAFT."""
        version = self.get_object()
        reason = request.data.get('reason', '')
        updated = TimetablePublicationService.send_back_to_draft(version, request.user, reason=reason)
        return Response(ScheduleVersionSerializer(updated).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='validate-sweep')
    def validate_sweep(self, request, pk=None):
        """Perform authoritative pre-publication clash sweep on all meetings."""
        version = self.get_object()
        conflicts = TimetablePublicationService.full_sweep_validation(version)
        return Response({
            'valid': len(conflicts) == 0,
            'total_conflicts': len(conflicts),
            'conflicts': conflicts
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request, pk=None):
        """Admin publishes schedule version if 0 clashes exist."""
        version = self.get_object()
        published = TimetablePublicationService.publish_schedule(version, request.user)
        return Response(ScheduleVersionSerializer(published).data, status=status.HTTP_200_OK)


class ValidatePlacementView(APIView):
    """
    Authoritative Timetable Conflict Validation Endpoint (§8).
    Evaluates placement constraints without modifying database records.
    """
    permission_classes = [IsSuperAdminOrReadOnly]

    @extend_schema(
        request=ValidationRequestSerializer,
        description="Check if placing a lecture or lab violates any timetable constraints (lunch crossing, overlaps, capacities).",
    )
    def post(self, request):
        serializer = ValidationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        version = get_object_or_404(ScheduleVersion, id=data['schedule_version_id'])
        assignment = get_object_or_404(TeachingAssignment, id=data['teaching_assignment_id'])
        room = get_object_or_404(Room, id=data['room_id'])

        result = TimetableValidator.validate_meeting_placement(
            schedule_version=version,
            teaching_assignment=assignment,
            weekday=data['weekday'],
            start_slot=data['start_slot'],
            duration_slots=data.get('duration_slots', 1),
            room=room,
            instruction_group_ids=data.get('instruction_group_ids'),
            exclude_meeting_id=data.get('exclude_meeting_id'),
            user=request.user,
        )

        return Response(result, status=status.HTTP_200_OK)


class ScheduledMeetingViewSet(viewsets.ModelViewSet):
    """
    Transactional Meeting Reservation ViewSet (§8).
    Applies authoritative 10-step atomic save and prevents race conditions with HTTP 409.
    """
    queryset = ScheduledMeeting.objects.select_related(
        'schedule_version',
        'teaching_assignment__course_offering__curriculum_item__course',
        'teaching_assignment__course_offering__cohort__branch',
        'teaching_assignment__professor',
        'room__building__campus'
    ).prefetch_related('meeting_instruction_groups__instruction_group').all()
    serializer_class = ScheduledMeetingSerializer
    permission_classes = [IsSuperAdminOrReadOnly]

    def create(self, request, *args, **kwargs):
        serializer = SaveMeetingRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        version = get_object_or_404(ScheduleVersion, id=data['schedule_version_id'])
        assignment = get_object_or_404(TeachingAssignment, id=data['teaching_assignment_id'])
        room = get_object_or_404(Room, id=data['room_id'])

        meeting = TimetableReservationService.save_meeting(
            schedule_version=version,
            teaching_assignment=assignment,
            weekday=data['weekday'],
            start_slot=data['start_slot'],
            duration_slots=data.get('duration_slots', 1),
            room=room,
            instruction_group_ids=data.get('instruction_group_ids'),
            existing_meeting_id=data.get('existing_meeting_id'),
            user=request.user,
        )

        output_serializer = ScheduledMeetingSerializer(meeting)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        meeting = self.get_object()
        weekday = request.data.get('weekday', meeting.weekday)
        start_slot = request.data.get('start_slot', meeting.start_slot)
        duration_slots = request.data.get('duration_slots', meeting.duration_slots)
        room_id = request.data.get('room_id', meeting.room_id)
        room = get_object_or_404(Room, id=room_id)

        updated_meeting = TimetableReservationService.save_meeting(
            schedule_version=meeting.schedule_version,
            teaching_assignment=meeting.teaching_assignment,
            weekday=weekday,
            start_slot=start_slot,
            duration_slots=duration_slots,
            room=room,
            existing_meeting_id=meeting.id,
            user=request.user,
        )

        output_serializer = ScheduledMeetingSerializer(updated_meeting)
        return Response(output_serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        meeting = self.get_object()
        success = TimetableReservationService.delete_meeting(
            schedule_version=meeting.schedule_version,
            meeting_id=meeting.id,
            user=request.user
        )
        if not success:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TimetableGridView(APIView):
    """
    Returns the timetable grid for a schedule version, filterable by branch, cohort, or professor.
    """
    permission_classes = [IsSuperAdminOrReadOnly]

    @extend_schema(description="Retrieve structured weekly timetable grid for a schedule version.")
    def get(self, request, version_id):
        version = get_object_or_404(ScheduleVersion, id=version_id)
        qs = ScheduledMeeting.objects.filter(schedule_version=version).select_related(
            'teaching_assignment__course_offering__curriculum_item__course',
            'teaching_assignment__course_offering__cohort__branch',
            'teaching_assignment__professor',
            'room__building'
        ).prefetch_related('meeting_instruction_groups__instruction_group')

        cohort_id = request.query_params.get('cohort_id')
        branch_id = request.query_params.get('branch_id')
        professor_id = request.query_params.get('professor_id')
        room_id = request.query_params.get('room_id')

        if cohort_id:
            qs = qs.filter(teaching_assignment__course_offering__cohort_id=cohort_id)
        if branch_id:
            qs = qs.filter(teaching_assignment__course_offering__cohort__branch_id=branch_id)
        if professor_id:
            qs = qs.filter(teaching_assignment__professor_id=professor_id)
        if room_id:
            qs = qs.filter(room_id=room_id)

        serializer = ScheduledMeetingSerializer(qs, many=True)
        return Response({
            'schedule_version_id': version.id,
            'revision': version.revision,
            'status': version.status,
            'meetings': serializer.data,
            'total_count': qs.count(),
        })


class AvailableRoomsView(APIView):
    """
    Returns all free rooms for a specified weekday and time slot range.
    """
    permission_classes = [IsSuperAdminOrReadOnly]

    def get(self, request, version_id):
        version = get_object_or_404(ScheduleVersion, id=version_id)
        weekday = int(request.query_params.get('weekday', 1))
        start_slot = int(request.query_params.get('start_slot', 1))
        duration_slots = int(request.query_params.get('duration_slots', 1))
        room_type = request.query_params.get('room_type')
        min_capacity = request.query_params.get('min_capacity')

        target_slots = list(range(start_slot, start_slot + duration_slots))

        busy_room_ids = RoomSlotReservation.objects.filter(
            schedule_version=version,
            weekday=weekday,
            slot_no__in=target_slots
        ).values_list('room_id', flat=True).distinct()

        end_slot = start_slot + duration_slots - 1
        blocked_rooms = RoomUnavailability.objects.filter(
            weekday=weekday,
            start_slot__lte=end_slot,
            end_slot__gte=start_slot
        ).values_list('room_id', flat=True).distinct()

        all_busy_ids = set(busy_room_ids).union(set(blocked_rooms))
        rooms = Room.objects.filter(is_active=True).exclude(id__in=all_busy_ids).select_related('building')

        if room_type:
            rooms = rooms.filter(room_type=room_type)
        if min_capacity:
            rooms = rooms.filter(capacity__gte=int(min_capacity))

        rooms_data = [
            {
                'id': r.id,
                'room_no': r.room_no,
                'name': r.name,
                'building_code': r.building.code,
                'room_type': r.room_type,
                'room_type_display': r.get_room_type_display(),
                'capacity': r.capacity,
                'has_projector': r.has_projector,
            }
            for r in rooms
        ]

        return Response(rooms_data, status=status.HTTP_200_OK)


class BatchUpdateMeetingsView(APIView):
    """
    Updates or moves multiple meetings in one atomic transaction.
    """
    permission_classes = [IsSuperAdminOrReadOnly]

    def post(self, request):
        version_id = request.data.get('schedule_version_id')
        updates = request.data.get('updates', [])
        if not version_id or not updates:
            return Response({'detail': 'schedule_version_id and updates array required'}, status=status.HTTP_400_BAD_REQUEST)

        version = get_object_or_404(ScheduleVersion, id=version_id)
        saved = TimetableReservationService.batch_update(version, updates, user=request.user)
        serializer = ScheduledMeetingSerializer(saved, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Phase 4: Read-Only & Publication Endpoints

class MyTimetableAPIView(APIView):
    """
    GET /api/my-timetable/
    Returns the authenticated professor's personal weekly teaching schedule from
    published schedule versions, along with personal unavailability blocks.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(description="Retrieve authenticated professor's personal published timetable.")
    def get(self, request):
        user = request.user
        term_id = request.query_params.get('term_id')

        # Find schedule version: prefer PUBLISHED, or term-specific, or latest
        versions = ScheduleVersion.objects.all()
        if term_id:
            versions = versions.filter(term_id=term_id)

        pub_ver = versions.filter(status=ScheduleVersion.Status.PUBLISHED).first()
        active_ver = pub_ver or versions.first()

        meetings = []
        if active_ver:
            qs = ScheduledMeeting.objects.filter(
                schedule_version=active_ver,
                teaching_assignment__professor=user
            ).select_related(
                'teaching_assignment__course_offering__curriculum_item__course',
                'teaching_assignment__course_offering__cohort__branch',
                'teaching_assignment__professor',
                'room__building'
            ).prefetch_related('meeting_instruction_groups__instruction_group')
            meetings = ScheduledMeetingSerializer(qs, many=True).data

        # Also get professor unavailability
        unavail = list(ProfessorUnavailability.objects.filter(professor=user).values(
            'id', 'weekday', 'start_slot', 'end_slot', 'reason'
        ))

        # Holidays for term
        holidays = []
        if active_ver:
            holidays = list(HolidayCalendar.objects.filter(term=active_ver.term).values(
                'id', 'date', 'name', 'is_academic_holiday'
            ))

        return Response({
            'schedule_version_id': active_ver.id if active_ver else None,
            'term_name': active_ver.term.name if active_ver else None,
            'status': active_ver.status if active_ver else None,
            'professor_id': user.id,
            'professor_name': user.full_name,
            'meetings': meetings,
            'unavailability': unavail,
            'holidays': holidays,
        })


class ProfessorTimetableAPIView(APIView):
    """
    GET /api/professors/{id}/timetable/
    Coordinator and Admin view of any professor's scheduled timetable.
    """
    permission_classes = [IsSuperAdminOrReadOnly]

    def get(self, request, professor_id):
        prof = get_object_or_404(User, id=professor_id)
        term_id = request.query_params.get('term_id')

        versions = ScheduleVersion.objects.all()
        if term_id:
            versions = versions.filter(term_id=term_id)

        pub_ver = versions.filter(status=ScheduleVersion.Status.PUBLISHED).first()
        active_ver = pub_ver or versions.first()

        meetings = []
        if active_ver:
            qs = ScheduledMeeting.objects.filter(
                schedule_version=active_ver,
                teaching_assignment__professor=prof
            ).select_related(
                'teaching_assignment__course_offering__curriculum_item__course',
                'teaching_assignment__course_offering__cohort__branch',
                'teaching_assignment__professor',
                'room__building'
            ).prefetch_related('meeting_instruction_groups__instruction_group')
            meetings = ScheduledMeetingSerializer(qs, many=True).data

        return Response({
            'professor_id': prof.id,
            'professor_name': prof.full_name,
            'schedule_version_id': active_ver.id if active_ver else None,
            'meetings': meetings,
        })


class BranchTimetableAPIView(APIView):
    """
    GET /api/branches/{id}/timetable/
    Public and student view of a branch's timetable for a term or published schedule.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, branch_id):
        branch = get_object_or_404(Branch, id=branch_id)
        term_id = request.query_params.get('term_id')
        cohort_id = request.query_params.get('cohort_id')
        semester_no = request.query_params.get('semester_no')

        versions = ScheduleVersion.objects.all()
        if term_id:
            versions = versions.filter(term_id=term_id)

        pub_ver = versions.filter(status=ScheduleVersion.Status.PUBLISHED).first()
        active_ver = pub_ver or versions.first()

        meetings = []
        if active_ver:
            qs = ScheduledMeeting.objects.filter(
                schedule_version=active_ver,
                teaching_assignment__course_offering__cohort__branch=branch
            ).select_related(
                'teaching_assignment__course_offering__curriculum_item__course',
                'teaching_assignment__course_offering__cohort__branch',
                'teaching_assignment__professor',
                'room__building'
            ).prefetch_related('meeting_instruction_groups__instruction_group')

            if cohort_id:
                qs = qs.filter(teaching_assignment__course_offering__cohort_id=cohort_id)
            if semester_no:
                qs = qs.filter(teaching_assignment__course_offering__cohort__semester_no=int(semester_no))

            meetings = ScheduledMeetingSerializer(qs, many=True).data

        return Response({
            'branch_id': branch.id,
            'branch_code': branch.code,
            'branch_name': branch.name,
            'schedule_version_id': active_ver.id if active_ver else None,
            'meetings': meetings,
        })


class HolidayCalendarViewSet(viewsets.ModelViewSet):
    """
    CRUD for academic term holidays.
    """
    queryset = HolidayCalendar.objects.select_related('term').all()
    serializer_class = HolidayCalendarSerializer
    permission_classes = [IsSuperAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['date']
    ordering = ['date']

    def get_queryset(self):
        qs = super().get_queryset()
        term_id = self.request.query_params.get('term')
        if term_id:
            qs = qs.filter(term_id=term_id)
        return qs


class DateOverrideViewSet(viewsets.ModelViewSet):
    """
    CRUD for single-day class cancellations and reschedules.
    """
    queryset = DateOverride.objects.select_related(
        'scheduled_meeting__teaching_assignment__course_offering__curriculum_item__course',
        'scheduled_meeting__teaching_assignment__professor',
        'new_room',
        'created_by'
    ).all()
    serializer_class = DateOverrideSerializer
    permission_classes = [IsSuperAdminOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        meeting_id = self.request.query_params.get('meeting')
        status_param = self.request.query_params.get('status')
        if meeting_id:
            qs = qs.filter(scheduled_meeting_id=meeting_id)
        if status_param:
            qs = qs.filter(status=status_param)
        return qs

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user if self.request.user.is_authenticated else None
        )


class ScheduleChangeAuditViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Super Admin Audit Log endpoint with pagination and filtering.
    """
    queryset = ScheduleChangeAudit.objects.select_related('schedule_version', 'user').all()
    serializer_class = ScheduleChangeAuditSerializer
    permission_classes = [IsSuperAdmin]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['action', 'user__email']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        version_id = self.request.query_params.get('version')
        meeting_id = self.request.query_params.get('meeting_id')
        user_id = self.request.query_params.get('user_id')
        action_name = self.request.query_params.get('action')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')

        if version_id:
            qs = qs.filter(schedule_version_id=version_id)
        if meeting_id:
            qs = qs.filter(meeting_id=meeting_id)
        if user_id:
            qs = qs.filter(user_id=user_id)
        if action_name:
            qs = qs.filter(action=action_name)
        if date_from:
            qs = qs.filter(created_at__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__lte=date_to)

        return qs
