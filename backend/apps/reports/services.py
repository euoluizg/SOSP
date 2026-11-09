import datetime
from typing import Any, Dict, List, Optional
from apps.scheduling.selectors import get_all_appointments
from common.feature_flags import FEATURE_REPORTS_EXPORT
from common.exceptions import ProblemDetailsException
from .repositories import reports_repository

class ReportsService:
    @staticmethod
    def get_appointments_summary(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        agency_id: Optional[str] = None,
        unit_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        appts = get_all_appointments()

        # Filtragem estrita por escopo organizacional (RN-36, ADR-003)
        if unit_id:
            appts = [a for a in appts if str(a.get("unitId") or "") == str(unit_id)]
        elif agency_id:
            appts = [a for a in appts if str(a.get("agencyId") or "") == str(agency_id)]

        total = len(appts)
        scheduled = sum(1 for a in appts if a.get("status") == "scheduled")
        completed = sum(1 for a in appts if a.get("status") == "completed")
        cancelled = sum(1 for a in appts if a.get("status") == "cancelled")
        no_show = sum(1 for a in appts if a.get("status") == "no_show")

        return {
            "period": {"start": start_date or "2026-11-01", "end": end_date or "2026-11-30"},
            "scope": {
                "agencyId": agency_id,
                "unitId": unit_id,
            },
            "metrics": {
                "totalAppointments": total,
                "scheduled": scheduled,
                "completed": completed,
                "cancelled": cancelled,
                "noShow": no_show,
                "attendanceRate": round((completed / total) * 100, 1) if total > 0 else 0,
            },
            "recentQueue": appts[:10],
        }

    @staticmethod
    def create_export(
        export_type: str = "csv",
        filters: Optional[Dict[str, Any]] = None,
        requested_by: str = "user-admin-01",
        user_scope: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        if not FEATURE_REPORTS_EXPORT:
            raise ProblemDetailsException(detail="Exportação de relatórios desativada.", status_code=403)

        effective_filters = dict(filters or {})

        # Se for usuário com escopo organizacional restrito (servidor/gestor), valida e impõe o escopo (RN-36)
        if user_scope:
            scope_agency = user_scope.get("agency_id")
            scope_unit = user_scope.get("unit_id")

            client_agency = effective_filters.get("agencyId")
            client_unit = effective_filters.get("unitId")

            if client_agency and scope_agency and client_agency != scope_agency:
                raise ProblemDetailsException(
                    detail="Servidor não possui autorização para exportar dados de outro órgão (RN-36).",
                    status_code=403,
                    title="Acesso não autorizado",
                )
            if client_unit and scope_unit and client_unit != scope_unit:
                raise ProblemDetailsException(
                    detail="Servidor não possui autorização para exportar dados de outra unidade (RN-36).",
                    status_code=403,
                    title="Acesso não autorizado",
                )

            if scope_agency:
                effective_filters["agencyId"] = scope_agency
            if scope_unit:
                effective_filters["unitId"] = scope_unit

        return reports_repository.create_export(
            export_type=export_type,
            filters=effective_filters,
            requested_by=requested_by,
        )

    @staticmethod
    def get_export(export_id: str) -> Optional[Dict[str, Any]]:
        return reports_repository.get_export(export_id)

    @staticmethod
    def list_exports() -> List[Dict[str, Any]]:
        return reports_repository.list_exports()
