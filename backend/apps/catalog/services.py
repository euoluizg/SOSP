from typing import Any, Dict, List, Optional
from common.exceptions import ProblemDetailsException
from .repositories import catalog_repository

class CatalogService:
    @staticmethod
    def list_agencies() -> List[Dict[str, Any]]:
        return catalog_repository.get_agencies()

    @staticmethod
    def list_units(agency_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return catalog_repository.get_units(agency_id=agency_id)

    @staticmethod
    def get_service_or_404(service_id: str) -> Dict[str, Any]:
        service = catalog_repository.get_service_by_id(service_id)
        if not service:
            raise ProblemDetailsException(
                detail=f"Serviço com ID '{service_id}' não encontrado.",
                title="Serviço não encontrado",
                status_code=404,
            )
        return service

    @staticmethod
    def list_categories() -> List[str]:
        return catalog_repository.get_categories()

