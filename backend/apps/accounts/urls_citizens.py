from django.urls import re_path
from .views import CitizenMeView
from apps.scheduling.views import CitizenAppointmentsView

urlpatterns = [
    re_path(r"^/me/?$", CitizenMeView.as_view(), name="citizen-me"),
    re_path(r"^/(?P<citizen_id>[^/]+)/appointments/?$", CitizenAppointmentsView.as_view(), name="citizen-appointments"),
]
