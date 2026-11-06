from django.urls import re_path
from .views import AgenciesListView

urlpatterns = [
    re_path(r"^/?$", AgenciesListView.as_view(), name="agencies-list"),
]
