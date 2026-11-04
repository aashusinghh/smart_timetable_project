from django.urls import path
from .views import CurriculumImportView, ProfessorImportView

urlpatterns = [
    path('curriculum/import', CurriculumImportView.as_view(), name='curriculum-import'),
    path('professors/import', ProfessorImportView.as_view(), name='professors-import'),
]
