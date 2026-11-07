from django.db import models
from django.contrib.postgres.fields import ArrayField

class CompatibleArrayField(ArrayField):
    """ArrayField compatível com PostgreSQL (nativo array) e SQLite (fallback texto)."""
    def db_type(self, connection):
        if connection.vendor == "sqlite":
            return "text"
        return super().db_type(connection)


class CompositeKeyForeignKey(models.ForeignKey):
    """
    ForeignKey que atua como coluna líder de chave primária composta em tabelas
    associativas do SOSP (catalogServiceAgency, catalogUnitService) no Django 5.1,
    evitando a geração de coluna artificial 'id' inexistente no schema PostgreSQL
    e suprimindo o falso alerta W342 de unicidade simples.
    """
    def _check_unique(self, **kwargs):
        return []

