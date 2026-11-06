import uuid
from django.db import models

class ReportExport(models.Model):
    """Solicitações de exportação de relatórios gerenciais CSV/PDF (reportsExport)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requested_by = models.UUIDField(db_column="requestedby")
    report_type = models.CharField(db_column="reporttype", max_length=40)
    filters = models.JSONField(default=dict)
    status = models.CharField(max_length=20, default="queued")
    file_url = models.CharField(db_column="fileurl", max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(db_column="createdat", auto_now_add=True)
    completed_at = models.DateTimeField(db_column="completedat", null=True, blank=True)

    class Meta:
        db_table = "reportsexport"
        verbose_name = "Exportação de Relatório"
        verbose_name_plural = "Exportações de Relatórios"
        ordering = ["-created_at"]
