import abc
from typing import Any, Dict, List, Optional, Protocol

class BaseRepository(Protocol):
    """Interface base de repositório para desacoplamento de banco de dados (Duck Typing)."""
    def get_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        ...

    def list_all(self, **filters: Any) -> List[Dict[str, Any]]:
        ...

    def save(self, data: Dict[str, Any]) -> Dict[str, Any]:
        ...


class AbstractRepository(abc.ABC):
    """
    Classe Abstrata Base para Repositórios (Pilar de Abstração e Herança - POO).
    Fornece o contrato formal com @abstractmethod para todas as implementações
    em memória e em ORM do SOSP.
    """

    @abc.abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Recupera entidade pelo identificador primário."""
        raise NotImplementedError

    @abc.abstractmethod
    def list_all(self, **filters: Any) -> List[Dict[str, Any]]:
        """Lista entidades aplicando filtros opcionais."""
        raise NotImplementedError

    @abc.abstractmethod
    def save(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Persiste ou atualiza uma entidade."""
        raise NotImplementedError
