from typing import Any, Dict, List, Optional, Protocol

class BaseRepository(Protocol):
    """Interface base de repositório para desacoplamento de banco de dados."""
    def get_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        ...

    def list_all(self, **filters: Any) -> List[Dict[str, Any]]:
        ...

    def save(self, data: Dict[str, Any]) -> Dict[str, Any]:
        ...

