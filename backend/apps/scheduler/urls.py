from django.urls import path
from .views import (
    GenerateTimetableAPIView,
    TaskStatusAPIView,
    ProposalViewSet,
    CommitProposalAPIView,
    DiscardProposalAPIView,
    TimetableScoreAPIView,
)

urlpatterns = [
    # Generation & Task Status
    path('timetable/<int:version_id>/generate', GenerateTimetableAPIView.as_view(), name='timetable-generate'),
    path('tasks/<str:task_id>/status', TaskStatusAPIView.as_view(), name='task-status'),

    # Proposals
    path('timetable/<int:version_id>/proposals', ProposalViewSet.as_view({'get': 'list'}), name='timetable-proposals-list'),
    path('timetable/<int:version_id>/proposals/<int:pk>', ProposalViewSet.as_view({'get': 'retrieve'}), name='timetable-proposals-detail'),
    path('timetable/<int:version_id>/commit-proposal', CommitProposalAPIView.as_view(), name='timetable-commit-proposal'),
    path('timetable/<int:version_id>/discard-proposal', DiscardProposalAPIView.as_view(), name='timetable-discard-proposal'),

    # Quality Scoring Report
    path('timetable/<int:version_id>/score', TimetableScoreAPIView.as_view(), name='timetable-score'),
]

