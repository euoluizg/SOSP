from typing import Any, Dict, List, Optional
from common.exceptions import ProblemDetailsException
from .repositories import catalog_repository

class CatalogService:
    @staticmethod
    def list_agencies() -> List[Dict[str, Any]]:
        return catalog_repository.get_agencies()

    @staticmethod
    def get_agency_or_404(agency_id: str) -> Dict[str, Any]:
        agency = catalog_repository.get_agency_by_id(agency_id)
        if not agency:
            raise ProblemDetailsException(
                detail=f"Órgão com ID '{agency_id}' não encontrado.",
                title="Órgão não encontrado",
                status_code=404,
            )
        return agency

    @staticmethod
    def update_agency(agency_id: str, data: Dict[str, Any], user: Any = None) -> Dict[str, Any]:
        agency = CatalogService.get_agency_or_404(agency_id)
        before_state = dict(agency)

        # Validações de campos obrigatórios se presentes
        if "name" in data and not str(data["name"]).strip():
            raise ProblemDetailsException(
                detail="O nome do órgão não pode ser vazio.",
                title="Erro de validação",
                status_code=400,
                errors=[{"field": "name", "message": "O nome do órgão não pode ser vazio."}],
            )
        if "acronym" in data and not str(data["acronym"]).strip():
            raise ProblemDetailsException(
                detail="A sigla do órgão não pode ser vazia.",
                title="Erro de validação",
                status_code=400,
                errors=[{"field": "acronym", "message": "A sigla do órgão não pode ser vazia."}],
            )

        updated = catalog_repository.update_agency(agency_id, data)
        if not updated:
            raise ProblemDetailsException(
                detail=f"Falha ao atualizar órgão '{agency_id}'.",
                title="Erro de atualização",
                status_code=500,
            )

        # Trilha de auditoria (auditEvent)
        try:
            from apps.audit.services import AuditService
            actor_id = getattr(user, "id", None) or getattr(user, "user_id", None) or "system"
            AuditService.record_event(
                action="UPDATE_AGENCY",
                actor_user_id=str(actor_id),
                target_table="catalogAgency",
                target_id=str(agency_id),
                before_state=before_state,
                after_state=updated,
            )
        except Exception:
            pass

        return updated

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
