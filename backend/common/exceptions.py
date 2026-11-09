import uuid
from typing import Any, Dict, List, Optional
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError, NotFound, PermissionDenied, AuthenticationFailed

class ProblemDetailsException(APIException):
    """Exceção customizada compatível com RFC 7807 (Problem Details)."""
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(
        self,
        detail: str,
        title: str = "Erro na requisição",
        type_uri: str = "about:blank",
        status_code: int = 400,
        errors: Optional[List[Dict[str, str]]] = None,
    ):
        super().__init__(detail)
        self.detail = detail
        self.title = title
        self.type_uri = type_uri
        self.status_code = status_code
        self.errors = errors or []

def problem_details_exception_handler(exc: Exception, context: Dict[str, Any]) -> Optional[Response]:
    """Handler global que padroniza todas as exceções em RFC 7807 (application/problem+json)."""
    response = exception_handler(exc, context)
    trace_id = str(uuid.uuid4())
    request = context.get("request")
    instance = request.path if request else "/"

    if isinstance(exc, ProblemDetailsException):
        payload = {
            "type": exc.type_uri,
            "title": exc.title,
            "status": exc.status_code,
            "detail": exc.detail,
            "instance": instance,
            "traceId": trace_id,
        }
        if exc.errors:
            payload["errors"] = exc.errors
        return Response(payload, status=exc.status_code, content_type="application/problem+json")

    if response is not None:
        status_code = response.status_code
        errors: List[Dict[str, str]] = []
        detail = "Ocorreu um erro no processamento da solicitação."

        if isinstance(response.data, dict):
            if "detail" in response.data:
                detail = str(response.data["detail"])
            else:
                detail = "Um ou mais campos contêm valores inválidos."
                for field, val in response.data.items():
                    msg = val[0] if isinstance(val, list) and len(val) > 0 else str(val)
                    errors.append({"field": field, "message": str(msg)})
        elif isinstance(response.data, list):
            detail = str(response.data[0]) if len(response.data) > 0 else detail

        title_map = {
            400: "Dados inválidos",
            401: "Não autenticado",
            403: "Acesso não autorizado",
            404: "Recurso não encontrado",
            409: "Conflito de estado",
            422: "Erro de validação",
            429: "Muitas requisições",
            500: "Erro interno do servidor",
        }

        payload = {
            "type": f"https://sosp.al.gov.br/errors/{status_code}",
            "title": title_map.get(status_code, "Erro de processamento"),
            "status": status_code,
            "detail": detail,
            "instance": instance,
            "traceId": trace_id,
        }
        if errors:
            payload["errors"] = errors

        response.data = payload
        # `content_type` (e não o header) precisa ser definido no Response: o DRF
        # sobrescreve o header `Content-Type` a partir de `response.content_type`
        # durante a renderização, descartando qualquer valor setado manualmente.
        response.content_type = "application/problem+json"
        return response

    return None

def custom_404_handler(request, exception=None):
    """Handler global para rotas inexistentes retornando RFC 7807."""
    from django.http import JsonResponse
    payload = {
        "type": "https://sosp.al.gov.br/errors/404",
        "title": "Recurso não encontrado",
        "status": 404,
        "detail": "A rota solicitada não foi encontrada no servidor.",
        "instance": request.path,
        "traceId": str(uuid.uuid4()),
    }
    return JsonResponse(payload, status=404, content_type="application/problem+json")

def custom_500_handler(request):
    """Handler global para erros internos retornando RFC 7807."""
    from django.http import JsonResponse
    payload = {
        "type": "https://sosp.al.gov.br/errors/500",
        "title": "Erro interno do servidor",
        "status": 500,
        "detail": "Ocorreu um erro inesperado no processamento da solicitação.",
        "instance": request.path,
        "traceId": str(uuid.uuid4()),
    }
    return JsonResponse(payload, status=500, content_type="application/problem+json")
