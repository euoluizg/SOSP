import uuid
from typing import Any, Dict, List, Optional
from common.exceptions import ProblemDetailsException
from apps.catalog.repositories import catalog_repository
from .repositories import guidance_repository

class GuidanceService:
    @classmethod
    def get_guidance(cls, service_id: str, citizen_id: str = "citizen-001") -> Dict[str, Any]:
        service = catalog_repository.get_service_by_id(service_id)
        if not service:
            raise ProblemDetailsException(detail="Serviço não encontrado.", status_code=404)

        progress = guidance_repository.get_progress(citizen_id, service_id)
        checked_items = progress.get("checkedDocumentIds", []) if progress else []

        return {
            "serviceId": service_id,
            "serviceName": service["name"],
            "steps": service.get("steps", []),
            "documents": service.get("documents", []),
            "checkedItems": checked_items,
        }

    @classmethod
    def update_checklist(cls, service_id: str, checked_items: List[str], citizen_id: str = "citizen-001") -> Dict[str, Any]:
        guidance_repository.save_progress(citizen_id, service_id, checked_items)
        return {"serviceId": service_id, "checkedItems": checked_items, "updated": True}

    @classmethod
    def request_pdf(cls, service_id: str, citizen_id: str = "citizen-001") -> Dict[str, Any]:
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        file_url = f"/mock-storage/guia-{service_id}.pdf"
        return guidance_repository.save_pdf_job(job_id, citizen_id, service_id, file_url)

    @classmethod
    def get_pdf_job(cls, job_id: str) -> Dict[str, Any]:
        job = guidance_repository.get_pdf_job(job_id)
        if not job:
            raise ProblemDetailsException(detail="Job de geração de PDF não encontrado.", status_code=404)
        return job
