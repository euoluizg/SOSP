import time
import datetime
from django.conf import settings
from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class HealthCheckView(APIView):
    """
    Endpoint de verificação de integridade operacional do SOSP.
    - Público / Probe de Load Balancer: Retorna liveness básico sem vazar topologia interna.
    - Autenticado / Interno / Debug: Retorna diagnóstico detalhado (latência, engine, repositórios).
    """
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        db_status = "operational"
        db_error = None
        db_latency_ms = None
        start = time.time()

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            db_latency_ms = round((time.time() - start) * 1000, 2)
        except Exception as e:
            db_status = "degraded"
            db_error = str(e)

        overall_status = "healthy" if db_status == "operational" else "unhealthy"
        http_status = status.HTTP_200_OK if overall_status == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE

        # Verifica autorização para diagnóstico detalhado
        internal_token = request.headers.get("X-Internal-Token") or request.query_params.get("token")
        expected_token = getattr(settings, "INTERNAL_HEALTHCHECK_TOKEN", None)
        is_internal_auth = expected_token and internal_token == expected_token
        is_admin_user = hasattr(request, "user") and getattr(request.user, "is_staff", False)
        show_detailed = settings.DEBUG or is_internal_auth or is_admin_user

        if not show_detailed:
            # Resposta enxuta para probes públicos (sem exposição de engine interna, latência ou stack traces)
            return Response(
                {
                    "status": overall_status,
                    "version": "1.0.0",
                    "service": "sosp-backend",
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "database": {
                        "status": db_status,
                    },
                },
                status=http_status,
            )

        response_payload = {
            "status": overall_status,
            "version": "1.0.0",
            "service": "sosp-backend",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "environment": "production" if not settings.DEBUG else "development",
            "repositoryBackend": getattr(settings, "REPOSITORY_BACKEND", "memory"),
            "database": {
                "engine": getattr(settings, "DB_ENGINE", "sqlite3"),
                "status": db_status,
                "latencyMs": db_latency_ms,
            },
        }
        if db_error:
            response_payload["database"]["error"] = db_error

        return Response(response_payload, status=http_status)
