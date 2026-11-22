import uuid
from django.db import models

class Slot(models.Model):
    """Slots de agendamento de 30 minutos por unidade (schedulingSlot)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    unit = models.ForeignKey("catalog.Unit", db_column="unitid", on_delete=models.CASCADE)
    slot_date = models.DateField(db_column="slotdate")
    starts_at = models.TimeField(db_column="startsat")
    ends_at = models.TimeField(db_column="endsat")
    capacity = models.IntegerField(default=1)
    booked_count = models.IntegerField(db_column="bookedcount", default=0)
    created_at = models.DateTimeField(db_column="createdat", auto_now_add=True)
    updated_at = models.DateTimeField(db_column="updatedat", auto_now=True)

    class Meta:
        db_table = "schedulingslot"
        unique_together = (("unit", "slot_date", "starts_at"),)
        verbose_name = "Vaga de Agendamento"
        verbose_name_plural = "Vagas de Agendamento"

    def __str__(self):
        return f"{self.unit} - {self.slot_date} {self.starts_at} ({self.booked_count}/{self.capacity})"

class Appointment(models.Model):
    """Agendamento presencial com protocolo AAAAMMDD-XXXX (schedulingAppointment)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    protocol_number = models.CharField(db_column="protocolnumber", max_length=13, unique=True)
    citizen = models.ForeignKey("accounts.Citizen", db_column="citizenid", on_delete=models.PROTECT)
    service = models.ForeignKey("catalog.Service", db_column="serviceid", on_delete=models.PROTECT)
    unit = models.ForeignKey("catalog.Unit", db_column="unitid", on_delete=models.PROTECT)
    slot = models.ForeignKey("scheduling.Slot", db_column="slotid", on_delete=models.PROTECT)
    scheduled_date = models.DateField(db_column="scheduleddate")
    scheduled_time = models.TimeField(db_column="scheduledtime")
    status = models.CharField(max_length=20, default="scheduled")
    cancellation_reason = models.CharField(db_column="cancellationreason", max_length=500, null=True, blank=True)
    rescheduled_from = models.ForeignKey("self", db_column="rescheduledfromid", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(db_column="createdat", auto_now_add=True)
    updated_at = models.DateTimeField(db_column="updatedat", auto_now=True)

    class Meta:
        db_table = "schedulingappointment"
        verbose_name = "Agendamento"
        verbose_name_plural = "Agendamentos"

    def __str__(self):
        return f"Protocolo {self.protocol_number} - {self.service}"

class Protocol(models.Model):
    """Protocolo oficial de atendimento do cidadão (schedulingProtocol)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    protocol_number = models.CharField(db_column="protocolnumber", max_length=13, unique=True)
    protocol_type = models.CharField(db_column="protocoltype", max_length=20)
    citizen = models.ForeignKey("accounts.Citizen", db_column="citizenid", on_delete=models.PROTECT)
    appointment = models.OneToOneField("scheduling.Appointment", db_column="appointmentid", on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=30, default="received")
    opened_at = models.DateTimeField(db_column="openedat", auto_now_add=True)
    closed_at = models.DateTimeField(db_column="closedat", null=True, blank=True)
    created_at = models.DateTimeField(db_column="createdat", auto_now_add=True)
    updated_at = models.DateTimeField(db_column="updatedat", auto_now=True)

    class Meta:
        db_table = "schedulingprotocol"
        verbose_name = "Protocolo"
        verbose_name_plural = "Protocolos"

    def __str__(self):
        return f"{self.protocol_number} ({self.status})"

class ProtocolAttachment(models.Model):
    """Anexos enviados pelo cidadão no protocolo (schedulingProtocolAttachment)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    protocol = models.ForeignKey("scheduling.Protocol", db_column="protocolid", on_delete=models.CASCADE)
    citizen = models.ForeignKey("accounts.Citizen", db_column="citizenid", on_delete=models.PROTECT)
    file_name = models.CharField(db_column="filename", max_length=255)
    storage_key = models.CharField(db_column="storagekey", max_length=500)
    mime_type = models.CharField(db_column="mimetype", max_length=100)
    file_size = models.IntegerField(db_column="filesize")
    antivirus_status = models.CharField(db_column="antivirusstatus", max_length=20, default="pending")
    created_at = models.DateTimeField(db_column="createdat", auto_now_add=True)

    class Meta:
        db_table = "schedulingprotocolattachment"
        verbose_name = "Anexo de Protocolo"
        verbose_name_plural = "Anexos de Protocolos"

class ProtocolTransition(models.Model):
    """Linha do tempo de transições de status do protocolo (schedulingProtocolTransition)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    protocol = models.ForeignKey("scheduling.Protocol", db_column="protocolid", on_delete=models.CASCADE)
    from_status = models.CharField(db_column="fromstatus", max_length=30, null=True, blank=True)
    to_status = models.CharField(db_column="tostatus", max_length=30)
    actor_type = models.CharField(db_column="actortype", max_length=20)
    actor_id = models.UUIDField(db_column="actorid", null=True, blank=True)
    note = models.CharField(max_length=1000, null=True, blank=True)
    created_at = models.DateTimeField(db_column="createdat", auto_now_add=True)

    class Meta:
        db_table = "schedulingprotocoltransition"
        verbose_name = "Transição de Protocolo"
        verbose_name_plural = "Transições de Protocolos"
        ordering = ["created_at"]

class SlotAvailabilityView(models.Model):
    """View relacional de disponibilidade de vagas em tempo real (vw_schedulingSlotAvailability)."""
    slot_id = models.UUIDField(primary_key=True, db_column="slotid")
    unit_id = models.UUIDField(db_column="unitid")
    unit_name = models.CharField(db_column="unitname", max_length=120)
    city = models.CharField(max_length=80)
    state = models.CharField(max_length=2)
    slot_date = models.DateField(db_column="slotdate")
    starts_at = models.TimeField(db_column="startsat")
    ends_at = models.TimeField(db_column="endsat")
    capacity = models.IntegerField()
    booked_count = models.IntegerField(db_column="bookedcount")
    available_slots = models.IntegerField(db_column="availableslots")
    is_available = models.BooleanField(db_column="isavailable")

    class Meta:
        managed = False
        db_table = "vw_schedulingslotavailability"
