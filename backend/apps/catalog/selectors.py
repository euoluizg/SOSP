from typing import Any, Dict, List
from .repositories import catalog_repository

def get_all_active_services() -> List[Dict[str, Any]]:
    """Função pública de seleção de serviços para outros módulos (ADR-001)."""
    return catalog_repository.get_services()

