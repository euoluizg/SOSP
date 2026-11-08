from django.urls import path, re_path, include
from common.health import HealthCheckView

urlpatterns = [
    # Health checks
    re_path(r"^api/v1/health/?$", HealthCheckView.as_view(), name="health-check-v1"),
    re_path(r"^health/?$", HealthCheckView.as_view(), name="health-check-root"),

    # Módulos SOSP — /api/v1/ (Aceita com ou sem barra final)
    re_path(r"^api/v1/auth/", include("apps.accounts.urls_auth")),
    re_path(r"^api/v1/citizens", include("apps.accounts.urls_citizens")),
    re_path(r"^api/v1/services", include("apps.catalog.urls_services")),
    re_path(r"^api/v1/agencies", include("apps.catalog.urls_agencies")),
    re_path(r"^api/v1/units", include("apps.catalog.urls_units")),
    re_path(r"^api/v1/categories", include("apps.catalog.urls_categories")),
    re_path(r"^api/v1/guidance", include("apps.guidance.urls")),
    re_path(r"^api/v1/appointments", include("apps.scheduling.urls_appointments")),
    re_path(r"^api/v1/protocols", include("apps.scheduling.urls_protocols")),
    re_path(r"^api/v1/feedback", include("apps.feedback.urls")),
    re_path(r"^api/v1/questions", include("apps.feedback.urls_questions")),
    re_path(r"^api/v1/reports", include("apps.reports.urls")),
    re_path(r"^api/v1/audit", include("apps.audit.urls")),
]

handler404 = "common.exceptions.custom_404_handler"
handler500 = "common.exceptions.custom_500_handler"
