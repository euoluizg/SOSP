from django.urls import re_path
from .views import CategoriesListView

urlpatterns = [
    re_path(r"^/?$", CategoriesListView.as_view(), name="categories-list"),
]
