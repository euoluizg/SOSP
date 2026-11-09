from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from common.security.permissions import IsInstitutionalUser
from .services import ReportsService


class AppointmentsReportView(APIView):
    """
    Relatório consolidado de agendamentos.
    Restrito a usuários institucionais (servidores e administradores — ADR-003, RS-01).
    Cidadãos recebem 403 Forbidden.
    """

    permission_classes = [IsInstitutionalUser]

    def get(self, request):
        start_date = request.query_params.get("startDate")
        end_date = request.query_params.get("endDate")
        result = ReportsService.get_appointments_summary(start_date, end_date)
        return Response(result, status=status.HTTP_200_OK)


class ReportsExportView(APIView):
    """
    Exportação de relatórios gerenciais em CSV/PDF.
    Restrito a usuários institucionais (servidores e administradores — ADR-003, RS-01).
    Cidadãos recebem 403 Forbidden.
    """

    permission_classes = [IsInstitutionalUser]

    def post(self, request):
        export_type = request.data.get("type", "csv")
        filters = request.data.get("filters", {})
        result = ReportsService.create_export(export_type, filters)
        return Response(result, status=status.HTTP_201_CREATED)
