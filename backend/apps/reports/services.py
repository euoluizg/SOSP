import datetime
from typing import Any, Dict, List, Optional
from apps.scheduling.selectors import get_all_appointments
from common.feature_flags import FEATURE_REPORTS_EXPORT
from common.exceptions import ProblemDetailsException
from .exporters import get_report_exporter
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

        # Filtragem por período (quando informado)
        if start_date:
            appts = [a for a in appts if str(a.get("scheduledDate") or "") >= start_date]
        if end_date:
            appts = [a for a in appts if str(a.get("scheduledDate") or "") <= end_date]

        total = len(appts)
        scheduled = sum(1 for a in appts if a.get("status") == "scheduled")
        in_progress = sum(1 for a in appts if a.get("status") in ("confirmed", "in_progress"))
        completed = sum(1 for a in appts if a.get("status") == "completed")
        cancelled = sum(1 for a in appts if a.get("status") == "cancelled")
        no_show = sum(1 for a in appts if a.get("status") in ("no_show", "noShow"))

        by_service: Dict[str, Dict[str, Any]] = {}
        for a in appts:
            svc_name = a.get("serviceName") or "Serviço Público"
            entry = by_service.setdefault(svc_name, {"serviceName": svc_name, "total": 0, "completed": 0, "noShow": 0})
            entry["total"] += 1
            if a.get("status") == "completed":
                entry["completed"] += 1
            elif a.get("status") in ("no_show", "noShow"):
                entry["noShow"] += 1

        return {
            "period": {"start": start_date or "2026-11-01", "end": end_date or "2026-11-30"},
            "scope": {
                "agencyId": agency_id,
                "unitId": unit_id,
            },
            "metrics": {
                "totalAppointments": total,
                "scheduled": scheduled,
                "inProgress": in_progress,
                "completed": completed,
                "cancelled": cancelled,
                "noShow": no_show,
                "attendanceRate": round((completed / total) * 100, 1) if total > 0 else 0,
            },
            "byService": sorted(by_service.values(), key=lambda x: x["total"], reverse=True),
            "recentQueue": appts[:25],
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

        exporter = get_report_exporter(export_type)
        summary = ReportsService.get_appointments_summary(
            start_date=effective_filters.get("startDate"),
            end_date=effective_filters.get("endDate"),
            agency_id=effective_filters.get("agencyId"),
            unit_id=effective_filters.get("unitId"),
        )
        exported_bytes = exporter.export(summary)

        record = reports_repository.create_export(
            export_type=exporter.format_name,
            filters=effective_filters,
            requested_by=requested_by,
        )
        enriched = dict(record)
        enriched["contentType"] = exporter.content_type
        enriched["fileName"] = exporter.build_filename()
        enriched["byteSize"] = len(exported_bytes)
        return enriched

    @staticmethod
    def get_export(export_id: str) -> Optional[Dict[str, Any]]:
        return reports_repository.get_export(export_id)

    @staticmethod
    def list_exports() -> List[Dict[str, Any]]:
        return reports_repository.list_exports()
