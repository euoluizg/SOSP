import uuid
from typing import Any, Dict, List, Optional
from common.exceptions import ProblemDetailsException
from apps.catalog.repositories import catalog_repository

class GuidanceService:
    _checklists: Dict[str, Dict[str, Any]] = {}
    _pdf_jobs: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get_guidance(cls, service_id: str, citizen_id: str = "citizen-001") -> Dict[str, Any]:
        service = catalog_repository.get_service_by_id(service_id)
        if not service:
            raise ProblemDetailsException(detail="Serviço não encontrado.", status_code=404)

        key = f"{citizen_id}:{service_id}"
        checked_items = cls._checklists.get(key, {}).get("checkedItems", [])

        return {
            "serviceId": service_id,
            "serviceName": service["name"],
            "steps": service.get("steps", []),
            "documents": service.get("documents", []),
            "checkedItems": checked_items,
        }

    @classmethod
    def update_checklist(cls, service_id: str, checked_items: List[str], citizen_id: str = "citizen-001") -> Dict[str, Any]:
        key = f"{citizen_id}:{service_id}"
        cls._checklists[key] = {"checkedItems": checked_items}
        return {"serviceId": service_id, "checkedItems": checked_items, "updated": True}

    @classmethod
    def request_pdf(cls, service_id: str, citizen_id: str = "citizen-001") -> Dict[str, Any]:
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        cls._pdf_jobs[job_id] = {
            "jobId": job_id,
            "serviceId": service_id,
            "status": "completed",
            "downloadUrl": f"/mock-storage/guia-{service_id}.pdf",
        }
        return cls._pdf_jobs[job_id]

    @classmethod
    def get_pdf_job(cls, job_id: str) -> Dict[str, Any]:
        job = cls._pdf_jobs.get(job_id)
        if not job:
            raise ProblemDetailsException(detail="Job de geração de PDF não encontrado.", status_code=404)
        return job

