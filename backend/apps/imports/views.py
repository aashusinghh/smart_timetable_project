from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, parsers
from drf_spectacular.utils import extend_schema
from apps.accounts.permissions import IsSuperAdmin
from .services import CSVImportService

class CurriculumImportView(APIView):
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    permission_classes = [IsSuperAdmin]

    @extend_schema(
        description="Upload CSV to import curriculum items and course delivery rules (Super Admin only).",
    )
    def post(self, request):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'detail': 'No file uploaded. Please upload a CSV file with key "file".'}, status=status.HTTP_400_BAD_REQUEST)

        if not file_obj.name.endswith('.csv'):
            return Response({'detail': 'Only .csv files are supported.'}, status=status.HTTP_400_BAD_REQUEST)

        result = CSVImportService.import_curriculum_csv(file_obj)
        if not result['success']:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_200_OK)


class ProfessorImportView(APIView):
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    permission_classes = [IsSuperAdmin]

    @extend_schema(
        description="Upload CSV to import professors and profiles (Super Admin only).",
    )
    def post(self, request):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'detail': 'No file uploaded. Please upload a CSV file with key "file".'}, status=status.HTTP_400_BAD_REQUEST)

        if not file_obj.name.endswith('.csv'):
            return Response({'detail': 'Only .csv files are supported.'}, status=status.HTTP_400_BAD_REQUEST)

        result = CSVImportService.import_professors_csv(file_obj)
        if not result['success']:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_200_OK)
