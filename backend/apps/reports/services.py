import datetime
from typing import Any, Dict, List, Optional
from apps.scheduling.selectors import get_all_appointments
from common.feature_flags import FEATURE_REPORTS_EXPORT
from common.exceptions import ProblemDetailsException

class ReportsService:
    @staticmethod
    def get_appointments_summary(start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        appts = get_all_appointments()
        total = len(appts)
        scheduled = sum(1 for a in appts if a.get("status") == "scheduled")
        completed = sum(1 for a in appts if a.get("status") == "completed")
        cancelled = sum(1 for a in appts if a.get("status") == "cancelled")
        no_show = sum(1 for a in appts if a.get("status") == "no_show")

        return {
            "period": {"start": start_date or "2026-11-01", "end": end_date or "2026-11-30"},
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
    def create_export(export_type: str = "csv", filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not FEATURE_REPORTS_EXPORT:
            raise ProblemDetailsException(detail="Exportação de relatórios desativada.", status_code=403)

        return {
            "exportId": f"exp-{int(datetime.datetime.now().timestamp())}",
            "type": export_type,
            "status": "ready",
            "downloadUrl": f"/mock-storage/relatorio-agendamentos.{export_type}",
            "generatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

