import math
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class StandardPagination(PageNumberPagination):
    """Paginação padrão do SOSP: 10 registros por página (RN-05)."""
    page_size = 10
    page_size_query_param = "pageSize"
    max_page_size = 50

    def get_paginated_response(self, data):
        total = self.page.paginator.count
        page_size = self.get_page_size(self.request) or self.page_size
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        return Response({
            "items": data,
            "total": total,
            "page": self.page.number,
            "pageSize": page_size,
            "totalPages": total_pages,
        })

