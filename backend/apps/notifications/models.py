import uuid
from django.db import models

class Template(models.Model):
    """Modelos de mensagens transacionais (notificationsTemplate)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=60)
    channel = models.CharField(max_length=20)
    subject = models.CharField(max_length=200, null=True, blank=True)
    body = models.TextField()
    is_active = models.BooleanField(db_column="isactive", default=True)
    created_at = models.DateTimeField(db_column="createdat", auto_now_add=True)
    updated_at = models.DateTimeField(db_column="updatedat", auto_now=True)

    class Meta:
        db_table = "notificationstemplate"
        verbose_name = "Template de Notificação"
        verbose_name_plural = "Templates de Notificações"

class Preference(models.Model):
    """Preferências de recebimento de notificações do cidadão (notificationsPreference)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    citizen = models.ForeignKey("accounts.Citizen", db_column="citizenid", on_delete=models.CASCADE)
    notification_type = models.CharField(db_column="notificationtype", max_length=40)
    channel = models.CharField(max_length=20)
    is_opt_in = models.BooleanField(db_column="isoptin", default=True)
    updated_at = models.DateTimeField(db_column="updatedat", auto_now=True)

    class Meta:
        db_table = "notificationspreference"
        unique_together = (("citizen", "notification_type", "channel"),)
        verbose_name = "Preferência de Notificação"
        verbose_name_plural = "Preferências de Notificações"

class Delivery(models.Model):
    """Registro de disparos de notificações (notificationsDelivery)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    citizen = models.ForeignKey("accounts.Citizen", db_column="citizenid", on_delete=models.CASCADE)
    channel = models.CharField(max_length=20)
    template_code = models.CharField(db_column="templatecode", max_length=60)
    status = models.CharField(max_length=20, default="queued")
    payload = models.JSONField(default=dict)
    error_message = models.CharField(db_column="errormessage", max_length=500, null=True, blank=True)
    sent_at = models.DateTimeField(db_column="sentat", null=True, blank=True)
    created_at = models.DateTimeField(db_column="createdat", auto_now_add=True)

    class Meta:
        db_table = "notificationsdelivery"
        verbose_name = "Disparo de Notificação"
        verbose_name_plural = "Disparos de Notificações"

class PushSubscription(models.Model):
    """Subscrições de Web Push do navegador do cidadão (notificationsPushSubscription)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    citizen = models.ForeignKey("accounts.Citizen", db_column="citizenid", on_delete=models.CASCADE)
    endpoint = models.CharField(max_length=500)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    created_at = models.DateTimeField(db_column="createdat", auto_now_add=True)
    revoked_at = models.DateTimeField(db_column="revokedat", null=True, blank=True)

    class Meta:
        db_table = "notificationspushsubscription"
        verbose_name = "Assinatura Push"
        verbose_name_plural = "Assinaturas Push"
