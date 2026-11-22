from typing import Any, Dict, List, Optional
from common.exceptions import ProblemDetailsException
from .repositories import catalog_repository


def _record_audit(action: str, target_table: str, target_id: str, user: Any = None, before_state: Any = None, after_state: Any = None, detail: str = "") -> None:
    try:
        from apps.audit.services import AuditService
        actor_id = getattr(user, "id", None) or getattr(user, "user_id", None) or "system"
        AuditService.record_event(
            action=action,
            actor_user_id=str(actor_id),
            target_table=target_table,
            target_id=str(target_id),
            before_state=before_state,
            after_state=after_state,
            detail=detail,
        )
    except Exception:
        pass


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
    def create_agency(data: Dict[str, Any], user: Any = None) -> Dict[str, Any]:
        created = catalog_repository.create_agency(data)
        _record_audit(
            action="CREATE",
            target_table="catalogAgency",
            target_id=created["id"],
            user=user,
            after_state=created,
            detail=f"Órgão {created['acronym']} ({created['name']}) criado.",
        )
        return created

    @staticmethod
    def update_agency(agency_id: str, data: Dict[str, Any], user: Any = None) -> Dict[str, Any]:
        agency = CatalogService.get_agency_or_404(agency_id)
        before_state = dict(agency)

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

        action_name = "DEACTIVATE" if data.get("isActive") is False else "UPDATE"
        _record_audit(
            action=action_name,
            target_table="catalogAgency",
            target_id=agency_id,
            user=user,
            before_state=before_state,
            after_state=updated,
            detail=f"Órgão {updated['acronym']} {'desativado logicamente' if action_name == 'DEACTIVATE' else 'atualizado'}.",
        )
        return updated

    @staticmethod
    def deactivate_agency(agency_id: str, user: Any = None) -> Dict[str, Any]:
        return CatalogService.update_agency(agency_id, {"isActive": False}, user=user)

    @staticmethod
    def list_units(agency_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return catalog_repository.get_units(agency_id=agency_id)

    @staticmethod
    def get_unit_or_404(unit_id: str) -> Dict[str, Any]:
        unit = catalog_repository.get_unit_by_id(unit_id)
        if not unit:
            raise ProblemDetailsException(
                detail=f"Unidade com ID '{unit_id}' não encontrada.",
                title="Unidade não encontrada",
                status_code=404,
            )
        return unit

    @staticmethod
    def create_unit(data: Dict[str, Any], user: Any = None) -> Dict[str, Any]:
        created = catalog_repository.create_unit(data)
        _record_audit(
            action="CREATE",
            target_table="catalogUnit",
            target_id=created["id"],
            user=user,
            after_state=created,
            detail=f"Unidade '{created['name']}' criada.",
        )
        return created

    @staticmethod
    def update_unit(unit_id: str, data: Dict[str, Any], user: Any = None) -> Dict[str, Any]:
        unit = CatalogService.get_unit_or_404(unit_id)
        updated = catalog_repository.update_unit(unit_id, data)
        if not updated:
            raise ProblemDetailsException(detail="Falha ao atualizar unidade.", status_code=500)
        action_name = "DEACTIVATE" if data.get("isActive") is False else "UPDATE"
        _record_audit(
            action=action_name,
            target_table="catalogUnit",
            target_id=unit_id,
            user=user,
            before_state=unit,
            after_state=updated,
            detail=f"Unidade '{updated['name']}' {'desativada logicamente' if action_name == 'DEACTIVATE' else 'atualizada'}.",
        )
        return updated

    @staticmethod
    def deactivate_unit(unit_id: str, user: Any = None) -> Dict[str, Any]:
        return CatalogService.update_unit(unit_id, {"isActive": False}, user=user)

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
    def create_service(data: Dict[str, Any], user: Any = None) -> Dict[str, Any]:
        actor_id = getattr(user, "id", None)
        created = catalog_repository.create_service(data, created_by_id=str(actor_id) if actor_id else None)
        _record_audit(
            action="CREATE",
            target_table="catalogService",
            target_id=created["id"],
            user=user,
            after_state=created,
            detail=f"Serviço '{created['name']}' publicado no catálogo.",
        )
        return created

    @staticmethod
    def update_service(service_id: str, data: Dict[str, Any], user: Any = None) -> Dict[str, Any]:
        svc = CatalogService.get_service_or_404(service_id)
        updated = catalog_repository.update_service(service_id, data)
        if not updated:
            raise ProblemDetailsException(detail="Falha ao atualizar serviço.", status_code=500)
        action_name = "DEACTIVATE" if data.get("isActive") is False else "UPDATE"
        _record_audit(
            action=action_name,
            target_table="catalogService",
            target_id=service_id,
            user=user,
            before_state=svc,
            after_state=updated,
            detail=f"Serviço '{updated['name']}' {'desativado logicamente' if action_name == 'DEACTIVATE' else 'atualizado'}.",
        )
        return updated

    @staticmethod
    def deactivate_service(service_id: str, user: Any = None) -> Dict[str, Any]:
        return CatalogService.update_service(service_id, {"isActive": False}, user=user)

    @staticmethod
    def list_categories() -> List[str]:
        return catalog_repository.get_categories()
