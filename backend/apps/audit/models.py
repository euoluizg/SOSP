import uuid
from django.db import models

class AuditEvent(models.Model):
    """Trilha imutável de eventos de auditoria (auditEvent - RN-39)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor_type = models.CharField(db_column="actortype", max_length=20)
    actor_id = models.UUIDField(db_column="actorid", null=True, blank=True)
    action = models.CharField(max_length=80)
    entity_type = models.CharField(db_column="entitytype", max_length=80)
    entity_id = models.UUIDField(db_column="entityid", null=True, blank=True)
    before_data = models.JSONField(db_column="beforedata", null=True, blank=True)
    after_data = models.JSONField(db_column="afterdata", null=True, blank=True)
    ip_address = models.GenericIPAddressField(db_column="ipaddress", null=True, blank=True)
    user_agent = models.CharField(db_column="useragent", max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(db_column="createdat", auto_now_add=True)

    class Meta:
        db_table = "auditevent"
        verbose_name = "Evento de Auditoria"
        verbose_name_plural = "Eventos de Auditoria"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.created_at}] {self.actor_type}:{self.actor_id} -> {self.action} on {self.entity_type}:{self.entity_id}"

class DataSubjectRequest(models.Model):
    """Solicitações de direitos de titular LGPD (auditDataSubjectRequest - RS-05)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    citizen = models.ForeignKey("accounts.Citizen", db_column="citizenid", on_delete=models.CASCADE)
    request_type = models.CharField(db_column="requesttype", max_length=20)
    status = models.CharField(max_length=20, default="open")
    notes = models.TextField(null=True, blank=True)
    requested_at = models.DateTimeField(db_column="requestedat", auto_now_add=True)
    completed_at = models.DateTimeField(db_column="completedat", null=True, blank=True)

    class Meta:
        db_table = "auditdatasubjectrequest"
        verbose_name = "Solicitação LGPD"
        verbose_name_plural = "Solicitações LGPD"
        ordering = ["-requested_at"]
