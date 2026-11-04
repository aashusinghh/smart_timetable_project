from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DepartmentViewSet,
    BranchViewSet,
    AcademicYearViewSet,
    AcademicTermViewSet,
    TimeSlotViewSet,
    CohortViewSet,
    InstructionGroupViewSet,
    CourseViewSet,
    CurriculumItemViewSet,
    CourseOfferingViewSet,
    TeachingAssignmentViewSet,
)

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'branches', BranchViewSet, basename='branch')
router.register(r'academic-years', AcademicYearViewSet, basename='academic-year')
router.register(r'academic-terms', AcademicTermViewSet, basename='academic-term')
router.register(r'time-slots', TimeSlotViewSet, basename='time-slot')
router.register(r'cohorts', CohortViewSet, basename='cohort')
router.register(r'instruction-groups', InstructionGroupViewSet, basename='instruction-group')
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'curriculum', CurriculumItemViewSet, basename='curriculum')
router.register(r'course-offerings', CourseOfferingViewSet, basename='course-offering')
router.register(r'teaching-assignments', TeachingAssignmentViewSet, basename='teaching-assignment')

urlpatterns = [
    path('', include(router.urls)),
]
