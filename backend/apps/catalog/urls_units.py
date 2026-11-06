from django.urls import re_path
from .views import UnitsListView
from apps.scheduling.views import UnitSlotsView

urlpatterns = [
    re_path(r"^/?$", UnitsListView.as_view(), name="units-list"),
    re_path(r"^/(?P<unit_id>[^/]+)/slots/?$", UnitSlotsView.as_view(), name="unit-slots"),
]
