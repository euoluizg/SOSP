import uuid
from django.db import models

class Review(models.Model):
    """Avaliação de atendimento pelo cidadão (feedbackReview - v2.0)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    protocol = models.OneToOneField("scheduling.Protocol", db_column="protocolid", on_delete=models.CASCADE)
    citizen = models.ForeignKey("accounts.Citizen", db_column="citizenid", on_delete=models.CASCADE)
    service = models.ForeignKey("catalog.Service", db_column="serviceid", on_delete=models.CASCADE)
    unit = models.ForeignKey("catalog.Unit", db_column="unitid", on_delete=models.CASCADE)
    rating = models.SmallIntegerField()
    review_comment = models.CharField(db_column="reviewcomment", max_length=500, null=True, blank=True)
    moderation_status = models.CharField(db_column="moderationstatus", max_length=20, default="pending")
    created_at = models.DateTimeField(db_column="createdat", auto_now_add=True)
    updated_at = models.DateTimeField(db_column="updatedat", auto_now=True)

    class Meta:
        db_table = "feedbackreview"
        verbose_name = "Avaliação"
        verbose_name_plural = "Avaliações"

class ReviewReport(models.Model):
    """Denúncia de avaliação abusiva para moderação (feedbackReviewReport)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review = models.ForeignKey("feedback.Review", db_column="reviewid", on_delete=models.CASCADE)
    reported_by = models.UUIDField(db_column="reportedby")
    reason = models.CharField(max_length=500)
    status = models.CharField(max_length=20, default="pending")
    created_at = models.DateTimeField(db_column="createdat", auto_now_add=True)
    resolved_at = models.DateTimeField(db_column="resolvedat", null=True, blank=True)

    class Meta:
        db_table = "feedbackreviewreport"
        verbose_name = "Denúncia de Avaliação"
        verbose_name_plural = "Denúncias de Avaliações"

class Question(models.Model):
    """Canal de dúvidas diretas do cidadão sobre o protocolo (feedbackQuestion)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    protocol = models.ForeignKey("scheduling.Protocol", db_column="protocolid", on_delete=models.CASCADE)
    citizen = models.ForeignKey("accounts.Citizen", db_column="citizenid", on_delete=models.CASCADE)
    service = models.ForeignKey("catalog.Service", db_column="serviceid", on_delete=models.SET_NULL, null=True, blank=True)
    subject = models.CharField(max_length=200)
    message = models.CharField(max_length=2000)
    attachment_url = models.CharField(db_column="attachmenturl", max_length=500, null=True, blank=True)
    answer = models.CharField(max_length=2000, null=True, blank=True)
    answered_by = models.UUIDField(db_column="answeredby", null=True, blank=True)
    answered_at = models.DateTimeField(db_column="answeredat", null=True, blank=True)
    created_at = models.DateTimeField(db_column="createdat", auto_now_add=True)

    class Meta:
        db_table = "feedbackquestion"
        verbose_name = "Dúvida do Cidadão"
        verbose_name_plural = "Dúvidas dos Cidadãos"
