import uuid
import datetime
from typing import Any, Dict, List, Optional
from django.conf import settings

class GuidanceInMemoryRepository:
    def __init__(self):
        self._checklists: Dict[str, Dict[str, Any]] = {}
        self._pdf_jobs: Dict[str, Dict[str, Any]] = {}

    def get_progress(self, citizen_id: str, service_id: str) -> Optional[Dict[str, Any]]:
        key = f"{citizen_id}:{service_id}"
        return self._checklists.get(key)

    def save_progress(self, citizen_id: str, service_id: str, checked_document_ids: List[str]) -> Dict[str, Any]:
        key = f"{citizen_id}:{service_id}"
        record = {
            "citizenId": citizen_id,
            "serviceId": service_id,
            "checkedDocumentIds": checked_document_ids,
            "updatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        self._checklists[key] = record
        return record

    def save_pdf_job(self, job_id: str, citizen_id: str, service_id: str, file_url: str) -> Dict[str, Any]:
        job = {
            "jobId": job_id,
            "citizenId": citizen_id,
            "serviceId": service_id,
            "status": "completed",
            "fileUrl": file_url,
            "downloadUrl": file_url,
            "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        self._pdf_jobs[job_id] = job
        return job

    def get_pdf_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self._pdf_jobs.get(job_id)


class GuidanceDjangoORMRepository:
    """Implementação real de persistência de guias via Django ORM (ADR-001)."""

    def get_progress(self, citizen_id: str, service_id: str) -> Optional[Dict[str, Any]]:
        from .models import GuidanceProgress
        try:
            p = GuidanceProgress.objects.filter(citizen_id=citizen_id, service_id=service_id).first()
            if not p:
                return None
            return {
                "id": str(p.id),
                "citizenId": str(p.citizen_id),
                "serviceId": str(p.service_id),
                "checkedDocumentIds": [str(d) for d in (p.checked_document_ids or [])],
                "startedAt": p.started_at.isoformat() if p.started_at else None,
                "completedAt": p.completed_at.isoformat() if p.completed_at else None,
                "updatedAt": p.updated_at.isoformat() if p.updated_at else None,
            }
        except Exception:
            return None

    def save_progress(self, citizen_id: str, service_id: str, checked_document_ids: List[str]) -> Dict[str, Any]:
        from .models import GuidanceProgress
        from django.utils import timezone
        p, _ = GuidanceProgress.objects.update_or_create(
            citizen_id=citizen_id,
            service_id=service_id,
            defaults={
                "checked_document_ids": checked_document_ids,
                "updated_at": timezone.now(),
            },
        )
        return {
            "id": str(p.id),
            "citizenId": str(p.citizen_id),
            "serviceId": str(p.service_id),
            "checkedDocumentIds": [str(d) for d in (p.checked_document_ids or [])],
            "updatedAt": p.updated_at.isoformat() if p.updated_at else None,
        }

    def save_pdf_job(self, job_id: str, citizen_id: str, service_id: str, file_url: str) -> Dict[str, Any]:
        from .models import GeneratedPdf
        from django.utils import timezone
        import datetime
        import hashlib

        c_hash = hashlib.sha256(f"{citizen_id}:{service_id}".encode("utf-8")).hexdigest()
        expires = timezone.now() + datetime.timedelta(hours=24)
        pdf_id = uuid.UUID(job_id) if len(job_id) == 36 else uuid.uuid4()

        pdf = GeneratedPdf.objects.create(
            id=pdf_id,
            citizen_id=citizen_id,
            service_id=service_id,
            file_url=file_url,
            checklist_hash=c_hash,
            expires_at=expires,
        )
        return {
            "jobId": str(pdf.id),
            "serviceId": str(pdf.service_id),
            "status": "completed",
            "fileUrl": pdf.file_url,
            "downloadUrl": pdf.file_url,
            "createdAt": pdf.created_at.isoformat(),
        }

    def get_pdf_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        from .models import GeneratedPdf
        try:
            pdf = GeneratedPdf.objects.filter(id=job_id).first()
            if not pdf:
                return None
            return {
                "jobId": str(pdf.id),
                "serviceId": str(pdf.service_id),
                "status": "completed",
                "fileUrl": pdf.file_url,
                "downloadUrl": pdf.file_url,
                "createdAt": pdf.created_at.isoformat(),
            }
        except Exception:
            return None


_guidance_memory_repository = GuidanceInMemoryRepository()

def get_guidance_repository():
    if getattr(settings, "REPOSITORY_BACKEND", "memory") == "orm":
        return GuidanceDjangoORMRepository()
    return _guidance_memory_repository

class GuidanceRepositoryProxy:
    def __getattr__(self, name):
        repo = get_guidance_repository()
        return getattr(repo, name)

guidance_repository = GuidanceRepositoryProxy()
