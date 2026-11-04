from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ScheduleVersionViewSet,
    ScheduledMeetingViewSet,
    ValidatePlacementView,
    TimetableGridView,
    AvailableRoomsView,
    BatchUpdateMeetingsView,
    ScheduleChangeAuditViewSet,
    MyTimetableAPIView,
    ProfessorTimetableAPIView,
    BranchTimetableAPIView,
    HolidayCalendarViewSet,
    DateOverrideViewSet,
)

router = DefaultRouter()
router.register(r'timetable/versions', ScheduleVersionViewSet, basename='schedule-version')
router.register(r'timetable/meetings', ScheduledMeetingViewSet, basename='scheduled-meeting')
router.register(r'timetable/audits', ScheduleChangeAuditViewSet, basename='timetable-audit')
router.register(r'audit-logs', ScheduleChangeAuditViewSet, basename='audit-logs')
router.register(r'holidays', HolidayCalendarViewSet, basename='holiday')
router.register(r'date-overrides', DateOverrideViewSet, basename='date-override')

urlpatterns = [
    path('timetable/validate', ValidatePlacementView.as_view(), name='timetable-validate'),
    path('timetable/<int:version_id>/grid', TimetableGridView.as_view(), name='timetable-grid'),
    path('timetable/<int:version_id>/available-rooms', AvailableRoomsView.as_view(), name='available-rooms'),
    path('timetable/batch-update', BatchUpdateMeetingsView.as_view(), name='timetable-batch-update'),

    # Phase 4 Read-only views
    path('my-timetable/', MyTimetableAPIView.as_view(), name='my-timetable'),
    path('professors/<int:professor_id>/timetable/', ProfessorTimetableAPIView.as_view(), name='professor-timetable'),
    path('branches/<int:branch_id>/timetable/', BranchTimetableAPIView.as_view(), name='branch-timetable'),

    path('', include(router.urls)),
]
