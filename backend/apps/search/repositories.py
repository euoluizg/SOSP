import uuid
import datetime
from typing import Any, Dict, List, Optional
from django.conf import settings

class SearchInMemoryRepository:
    def __init__(self):
        self._logs: List[Dict[str, Any]] = []
        self._synonyms: Dict[str, List[str]] = {
            "rg": ["identidade", "cin", "carteira de identidade"],
            "identidade": ["rg", "cin", "carteira de identidade"],
            "cnh": ["carteira de motorista", "habilitação", "renovação de cnh"],
        }

    def log_query(self, term: str, filters: Dict[str, Any], result_count: int, session_hash: Optional[str] = None) -> Dict[str, Any]:
        log = {
            "id": f"log-{len(self._logs) + 1:04d}",
            "term": term,
            "filters": filters,
            "resultCount": result_count,
            "sessionHash": session_hash,
            "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        self._logs.insert(0, log)
        return log

    def get_synonyms(self, term: str) -> List[str]:
        return self._synonyms.get(term.lower().strip(), [])

    def list_logs(self) -> List[Dict[str, Any]]:
        return list(self._logs)


class SearchDjangoORMRepository:
    """Implementação real de busca e log anônimo via Django ORM (ADR-001)."""

    def log_query(self, term: str, filters: Dict[str, Any], result_count: int, session_hash: Optional[str] = None) -> Dict[str, Any]:
        from .models import QueryLog
        try:
            log = QueryLog.objects.create(
                term=term[:200],
                filters=filters or {},
                result_count=result_count,
                session_hash=session_hash[:64] if session_hash else None,
            )
            return {
                "id": str(log.id),
                "term": log.term,
                "resultCount": log.result_count,
                "createdAt": log.created_at.isoformat(),
            }
        except Exception:
            return {"term": term, "resultCount": result_count}

    def get_synonyms(self, term: str) -> List[str]:
        from .models import Synonym
        try:
            syn = Synonym.objects.filter(term__iexact=term.strip(), is_active=True).first()
            return list(syn.synonyms) if syn and syn.synonyms else []
        except Exception:
            return []

    def list_logs(self) -> List[Dict[str, Any]]:
        from .models import QueryLog
        return [
            {
                "id": str(l.id),
                "term": l.term,
                "resultCount": l.result_count,
                "createdAt": l.created_at.isoformat(),
            }
            for l in QueryLog.objects.all().order_by("-created_at")[:50]
        ]


_search_memory_repository = SearchInMemoryRepository()

def get_search_repository():
    if getattr(settings, "REPOSITORY_BACKEND", "memory") == "orm":
        return SearchDjangoORMRepository()
    return _search_memory_repository

class SearchRepositoryProxy:
    def __getattr__(self, name):
        repo = get_search_repository()
        return getattr(repo, name)

search_repository = SearchRepositoryProxy()
