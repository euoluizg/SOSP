from typing import Any, Dict, List
from .repositories import scheduling_repository

def get_all_appointments() -> List[Dict[str, Any]]:
    """Função pública de seleção de agendamentos para outros módulos (ADR-001)."""
    return scheduling_repository.list_all()

