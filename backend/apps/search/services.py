import math
import unicodedata
from typing import Any, Dict, List, Optional
from apps.catalog.selectors import get_all_active_services
from apps.catalog.repositories import category_slug_to_label, normalize_category_slug
from .repositories import search_repository


def _normalize_text(value: str) -> str:
    raw = (value or "").strip().lower()
    decomposed = unicodedata.normalize("NFKD", raw)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


BUILTIN_SYNONYMS: Dict[str, List[str]] = {
    "tirar rg": ["identidade", "cin", "carteira de identidade", "rg"],
    "rg": ["identidade", "cin", "carteira de identidade"],
    "identidade": ["rg", "cin", "carteira de identidade"],
    "segunda via rg": ["identidade", "cin", "carteira de identidade"],
    "cnh": ["carteira nacional de habilitacao", "habilitacao", "renovacao"],
    "carteira de motorista": ["cnh", "habilitacao", "renovacao"],
    "iptu": ["tributos", "imposto", "certidao", "sefaz"],
    "certidao": ["certidao negativa", "sefaz", "debitos", "identidade"],
    "agua": ["casal", "saneamento", "segunda via"],
    "cadunico": ["cadastro unico", "assistencia social", "bolsa familia"],
    "saude": ["sus", "cartao sus", "sesau"],
}


class SearchService:
    @staticmethod
    def search_services(
        query: Optional[str] = None,
        category: Optional[str] = None,
        channel: Optional[str] = None,
        city: Optional[str] = None,
        agency_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Dict[str, Any]:
        all_services = get_all_active_services()
        filtered = list(all_services)

        if query and query.strip():
            q_norm = _normalize_text(query)
            repo_synonyms = search_repository.get_synonyms(query) or search_repository.get_synonyms(q_norm)
            builtin_syns = BUILTIN_SYNONYMS.get(q_norm, [])
            token_syns: List[str] = []
            for token in q_norm.split():
                token_syns.extend(BUILTIN_SYNONYMS.get(token, []))
                token_syns.extend(search_repository.get_synonyms(token) or [])

            search_terms = list(
                dict.fromkeys(
                    [_normalize_text(t) for t in ([query, q_norm] + list(repo_synonyms) + builtin_syns + token_syns) if t]
                )
            )

            def _matches(svc: Dict[str, Any]) -> bool:
                haystack = _normalize_text(
                    " ".join(
                        [
                            str(svc.get("name", "")),
                            str(svc.get("summary", "")),
                            str(svc.get("description", "")),
                            str(svc.get("agencyAcronym", "")),
                            str(svc.get("agencyName", "")),
                            str(svc.get("category", "")),
                        ]
                    )
                )
                return any(
                    term in haystack
                    or (term == "tirar rg" and svc.get("id") == "servico-emitir-rg")
                    for term in search_terms
                )

            filtered = [s for s in filtered if _matches(s)]

        if category and category != "Todos":
            cat_norm = _normalize_text(category)
            cat_slug = normalize_category_slug(category)
            cat_label = _normalize_text(category_slug_to_label(cat_slug))
            filtered = [
                s for s in filtered
                if _normalize_text(str(s.get("category", ""))) in (cat_norm, cat_label)
                or str(s.get("categorySlug", "")) == cat_slug
            ]

        if agency_id:
            filtered = [s for s in filtered if str(s.get("agencyId", "")) == str(agency_id)]

        if channel and channel != "Todos":
            filtered = [s for s in filtered if s.get("channel") == channel]

        if city and city.strip():
            city_norm = _normalize_text(city)
            def _matches_city(svc: Dict[str, Any]) -> bool:
                if svc.get("channel") == "online":
                    return True
                svc_cities = [_normalize_text(c) for c in (svc.get("cities") or [])]
                if svc_cities:
                    return city_norm in svc_cities
                return city_norm in ("maceio", "arapiraca")

            filtered = [s for s in filtered if _matches_city(s)]

        total = len(filtered)
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        page = max(1, page)
        start = (page - 1) * page_size
        items = filtered[start : start + page_size]

        # Log anônimo de busca (ADR-001)
        if query and query.strip():
            search_repository.log_query(
                term=query,
                filters={"category": category, "channel": channel, "city": city, "agencyId": agency_id},
                result_count=total,
            )

        return {
            "items": items,
            "total": total,
            "page": page,
            "pageSize": page_size,
            "totalPages": total_pages,
        }
