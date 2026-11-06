import math
from typing import Any, Dict, List, Optional
from apps.catalog.selectors import get_all_active_services

class SearchService:
    @staticmethod
    def search_services(
        query: Optional[str] = None,
        category: Optional[str] = None,
        channel: Optional[str] = None,
        city: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Dict[str, Any]:
        all_services = get_all_active_services()
        filtered = list(all_services)

        if query:
            q = query.lower().strip()
            filtered = [
                s for s in filtered
                if (
                    q in s.get("name", "").lower()
                    or q in s.get("summary", "").lower()
                    or q in s.get("description", "").lower()
                    or q in s.get("agencyAcronym", "").lower()
                    or (q == "tirar rg" and s.get("id") == "servico-emitir-rg")
                )
            ]

        if category and category != "Todos":
            filtered = [s for s in filtered if s.get("category") == category]

        if channel and channel != "Todos":
            filtered = [s for s in filtered if s.get("channel") == channel]

        total = len(filtered)
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        page = max(1, page)
        start = (page - 1) * page_size
        items = filtered[start : start + page_size]

        return {
            "items": items,
            "total": total,
            "page": page,
            "pageSize": page_size,
            "totalPages": total_pages,
        }

