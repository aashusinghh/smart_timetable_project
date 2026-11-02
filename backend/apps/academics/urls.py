from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DepartmentViewSet, BranchViewSet

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet, basename='departments')
router.register(r'branches', BranchViewSet, basename='branches')

urlpatterns = [
    path('', include(router.urls)),
]

