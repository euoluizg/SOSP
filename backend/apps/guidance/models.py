import uuid
from django.db import models
from common.fields import CompatibleArrayField

class GuidanceProgress(models.Model):
    """Progresso do checklist de documentos pelo cidadão (guidanceProgress)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    citizen = models.ForeignKey("accounts.Citizen", db_column="citizenid", on_delete=models.CASCADE)
    service = models.ForeignKey("catalog.Service", db_column="serviceid", on_delete=models.CASCADE)
    checked_document_ids = CompatibleArrayField(
        models.UUIDField(), db_column="checkeddocumentids", default=list
    )
    created_at = models.DateTimeField(db_column="createdat", auto_now_add=True)
    updated_at = models.DateTimeField(db_column="updatedat", auto_now=True)

    class Meta:
        db_table = "guidanceprogress"
        unique_together = (("citizen", "service"),)
        verbose_name = "Progresso de Guia"
        verbose_name_plural = "Progressos de Guias"

class GeneratedPdf(models.Model):
    """PDFs de guias gerados assincronamente (guidanceGeneratedPdf)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    citizen = models.ForeignKey("accounts.Citizen", db_column="citizenid", on_delete=models.CASCADE)
    service = models.ForeignKey("catalog.Service", db_column="serviceid", on_delete=models.CASCADE)
    file_url = models.CharField(db_column="fileurl", max_length=500)
    expires_at = models.DateTimeField(db_column="expiresat")
    created_at = models.DateTimeField(db_column="createdat", auto_now_add=True)

    class Meta:
        db_table = "guidancegeneratedpdf"
        verbose_name = "PDF Gerado"
        verbose_name_plural = "PDFs Gerados"
