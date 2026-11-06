import uuid
from django.db import models
from common.fields import CompatibleArrayField

class QueryLog(models.Model):
    """Log anônimo de buscas executadas pelos cidadãos (searchQueryLog)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    term = models.CharField(max_length=200)
    filters = models.JSONField(default=dict)
    result_count = models.IntegerField(db_column="resultcount", default=0)
    created_at = models.DateTimeField(db_column="createdat", auto_now_add=True)

    class Meta:
        db_table = "searchquerylog"
        verbose_name = "Log de Busca"
        verbose_name_plural = "Logs de Buscas"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.term} ({self.result_count} resultados)"

class Synonym(models.Model):
    """Sinônimos de termos de busca (searchSynonym)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    term = models.CharField(max_length=100)
    synonyms = CompatibleArrayField(models.CharField(max_length=100))
    is_active = models.BooleanField(db_column="isactive", default=True)
    created_at = models.DateTimeField(db_column="createdat", auto_now_add=True)
    updated_at = models.DateTimeField(db_column="updatedat", auto_now=True)
    deleted_at = models.DateTimeField(db_column="deletedat", null=True, blank=True)

    class Meta:
        db_table = "searchsynonym"
        verbose_name = "Sinônimo"
        verbose_name_plural = "Sinônimos"

    def __str__(self):
        return f"{self.term} -> {self.synonyms}"
