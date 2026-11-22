from django.urls import re_path
from .views import AuditEventsListView

urlpatterns = [
    re_path(r"^/events/?$", AuditEventsListView.as_view(), name="audit-events-list"),
]
