import uuid
import datetime
from typing import Any, Dict, List, Optional
from django.conf import settings

class ReportsInMemoryRepository:
    def __init__(self):
        self._exports: List[Dict[str, Any]] = []

    def create_export(self, export_type: str, filters: Optional[Dict[str, Any]] = None, requested_by: str = "user-admin-01") -> Dict[str, Any]:
        export_id = f"exp-{int(datetime.datetime.now().timestamp())}"
        record = {
            "exportId": export_id,
            "type": export_type,
            "status": "ready",
            "filters": filters or {},
            "requestedBy": requested_by,
            "downloadUrl": f"/mock-storage/relatorio-agendamentos.{export_type}",
            "generatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        self._exports.insert(0, record)
        return record

    def get_export(self, export_id: str) -> Optional[Dict[str, Any]]:
        for e in self._exports:
            if e.get("exportId") == export_id:
                return e
        return None

    def list_exports(self) -> List[Dict[str, Any]]:
        return list(self._exports)


class ReportsDjangoORMRepository:
    """Implementação real de persistência de relatórios via Django ORM (ADR-001)."""

    def create_export(self, export_type: str, filters: Optional[Dict[str, Any]] = None, requested_by: str = "user-admin-01") -> Dict[str, Any]:
        from .models import ReportExport
        from django.utils import timezone

        req_uuid = uuid.UUID(requested_by) if len(requested_by) == 36 else uuid.uuid4()
        download_url = f"/mock-storage/relatorio-agendamentos.{export_type}"

        rep = ReportExport.objects.create(
            requested_by=req_uuid,
            report_type=export_type,
            filters=filters or {},
            status="ready",
            file_url=download_url,
            completed_at=timezone.now(),
        )
        return {
            "exportId": str(rep.id),
            "type": rep.report_type,
            "status": rep.status,
            "filters": rep.filters,
            "requestedBy": str(rep.requested_by),
            "downloadUrl": rep.file_url,
            "generatedAt": rep.created_at.isoformat(),
        }

    def get_export(self, export_id: str) -> Optional[Dict[str, Any]]:
        from .models import ReportExport
        try:
            rep = ReportExport.objects.filter(id=export_id).first()
            if not rep:
                return None
            return {
                "exportId": str(rep.id),
                "type": rep.report_type,
                "status": rep.status,
                "filters": rep.filters,
                "requestedBy": str(rep.requested_by),
                "downloadUrl": rep.file_url,
                "generatedAt": rep.created_at.isoformat(),
            }
        except Exception:
            return None

    def list_exports(self) -> List[Dict[str, Any]]:
        from .models import ReportExport
        return [
            {
                "exportId": str(rep.id),
                "type": rep.report_type,
                "status": rep.status,
                "filters": rep.filters,
                "requestedBy": str(rep.requested_by),
                "downloadUrl": rep.file_url,
                "generatedAt": rep.created_at.isoformat(),
            }
            for rep in ReportExport.objects.all().order_by("-created_at")
        ]


_reports_memory_repository = ReportsInMemoryRepository()

def get_reports_repository():
    if getattr(settings, "REPOSITORY_BACKEND", "memory") == "orm":
        return ReportsDjangoORMRepository()
    return _reports_memory_repository

class ReportsRepositoryProxy:
    def __getattr__(self, name):
        repo = get_reports_repository()
        return getattr(repo, name)

reports_repository = ReportsRepositoryProxy()
