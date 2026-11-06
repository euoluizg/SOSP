from django.db import models
from django.contrib.postgres.fields import ArrayField

class CompatibleArrayField(ArrayField):
    """ArrayField compatível com PostgreSQL (nativo array) e SQLite (fallback texto)."""
    def db_type(self, connection):
        if connection.vendor == "sqlite":
            return "text"
        return super().db_type(connection)
