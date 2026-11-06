from django.urls import re_path
from .views import AppointmentsReportView, ReportsExportView

urlpatterns = [
    re_path(r"^/appointments/?$", AppointmentsReportView.as_view(), name="reports-appointments"),
    re_path(r"^/exports/?$", ReportsExportView.as_view(), name="reports-exports"),
]
