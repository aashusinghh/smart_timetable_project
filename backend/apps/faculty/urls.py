from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProfessorViewSet, ProfessorUnavailabilityViewSet

router = DefaultRouter()
router.register(r'professors', ProfessorViewSet, basename='professor')
router.register(r'professor-unavailabilities', ProfessorUnavailabilityViewSet, basename='professor-unavailability')

urlpatterns = [
    path('', include(router.urls)),
]
