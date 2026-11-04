from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CampusViewSet,
    BuildingViewSet,
    RoomViewSet,
    RoomUnavailabilityViewSet,
)

router = DefaultRouter()
router.register(r'campuses', CampusViewSet, basename='campus')
router.register(r'buildings', BuildingViewSet, basename='building')
router.register(r'rooms', RoomViewSet, basename='room')
router.register(r'room-unavailabilities', RoomUnavailabilityViewSet, basename='room-unavailability')

urlpatterns = [
    path('', include(router.urls)),
]
