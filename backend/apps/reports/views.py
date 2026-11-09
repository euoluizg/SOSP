from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from common.security.permissions import IsInstitutionalUser
from common.exceptions import ProblemDetailsException
from .services import ReportsService


class AppointmentsReportView(APIView):
    """
    Relatório consolidado de agendamentos.
    Restrito a usuários institucionais (servidores e administradores — ADR-003, RS-01).
    Cidadãos recebem 403 Forbidden.
    Servidores têm dados restritos ao seu escopo organizacional autorizado (RN-36).
    """

    permission_classes = [IsInstitutionalUser]

    def get(self, request):
        start_date = request.query_params.get("startDate")
        end_date = request.query_params.get("endDate")
        user_role = getattr(request.user, "role", "servant")

        effective_agency = None
        effective_unit = None

        if user_role in ("server", "servant", "servidor", "gestor", "manager"):
            server_unit = str(getattr(request.user, "unit_id", "") or "")
            server_agency = str(getattr(request.user, "agency_id", "") or "")

            param_agency = request.query_params.get("agencyId")
            param_unit = request.query_params.get("unitId")

            # Valida que o servidor não tente solicitar outro órgão ou unidade
            if param_agency and server_agency and param_agency != server_agency:
                raise ProblemDetailsException(
                    detail="Servidor não possui autorização para consultar relatórios de outro órgão (RN-36).",
                    status_code=403,
                    title="Acesso não autorizado",
                )
            if param_unit and server_unit and param_unit != server_unit:
                raise ProblemDetailsException(
                    detail="Servidor não possui autorização para consultar relatórios de outra unidade (RN-36).",
                    status_code=403,
                    title="Acesso não autorizado",
                )

            effective_agency = server_agency or param_agency
            effective_unit = server_unit or param_unit
        else:
            # Administrador / Superadministrador: pode filtrar livremente por query params
            effective_agency = request.query_params.get("agencyId")
            effective_unit = request.query_params.get("unitId")

        result = ReportsService.get_appointments_summary(
            start_date=start_date,
            end_date=end_date,
            agency_id=effective_agency,
            unit_id=effective_unit,
        )
        return Response(result, status=status.HTTP_200_OK)


class ReportsExportView(APIView):
    """
    Exportação de relatórios gerenciais em CSV/PDF.
    Restrito a usuários institucionais (servidores e administradores — ADR-003, RS-01).
    Cidadãos recebem 403 Forbidden.
    Preserva a identidade autenticada do solicitante para rastreabilidade de auditoria.
    """

    permission_classes = [IsInstitutionalUser]

    def post(self, request):
        export_type = request.data.get("type", "csv")
        filters = dict(request.data.get("filters", {}) or {})
        user_role = getattr(request.user, "role", "servant")
        requested_by = str(request.user.id)

        user_scope = None
        if user_role in ("server", "servant", "servidor", "gestor", "manager"):
            user_scope = {
                "agency_id": str(getattr(request.user, "agency_id", "") or ""),
                "unit_id": str(getattr(request.user, "unit_id", "") or ""),
            }

        result = ReportsService.create_export(
            export_type=export_type,
            filters=filters,
            requested_by=requested_by,
            user_scope=user_scope,
        )
        return Response(result, status=status.HTTP_201_CREATED)
