import uuid
from django.db import models
from common.fields import CompositeKeyForeignKey

class Agency(models.Model):
    """Órgão da administração pública (catalogAgency)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    acronym = models.CharField(max_length=10)
    sphere = models.CharField(max_length=20)
    description = models.CharField(max_length=500, null=True, blank=True)
    is_active = models.BooleanField(db_column="isactive", default=True)
    created_at = models.DateTimeField(db_column="createdat", auto_now_add=True)
    updated_at = models.DateTimeField(db_column="updatedat", auto_now=True)
    deleted_at = models.DateTimeField(db_column="deletedat", null=True, blank=True)

    class Meta:
        db_table = "catalogagency"
        verbose_name = "Órgão"
        verbose_name_plural = "Órgãos"

    def __str__(self):
        return f"{self.acronym} - {self.name}"

class Unit(models.Model):
    """Posto ou unidade de atendimento presencial (catalogUnit)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agency = models.ForeignKey("catalog.Agency", db_column="agencyid", on_delete=models.PROTECT)
    name = models.CharField(max_length=120)
    zip_code = models.CharField(db_column="zipcode", max_length=8)
    street = models.CharField(max_length=120)
    neighborhood = models.CharField(max_length=80)
    city = models.CharField(max_length=80)
    state = models.CharField(max_length=2)
    address_number = models.CharField(db_column="addressnumber", max_length=10)
    phone = models.CharField(max_length=11, null=True, blank=True)
    email = models.CharField(max_length=200, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_accessible = models.BooleanField(db_column="isaccessible", default=False)
    has_priority_service = models.BooleanField(db_column="haspriorityservice", default=False)
    daily_limit = models.IntegerField(db_column="dailylimit", default=40)
    is_active = models.BooleanField(db_column="isactive", default=True)
    created_at = models.DateTimeField(db_column="createdat", auto_now_add=True)
    updated_at = models.DateTimeField(db_column="updatedat", auto_now=True)
    deleted_at = models.DateTimeField(db_column="deletedat", null=True, blank=True)

    class Meta:
        db_table = "catalogunit"
        verbose_name = "Unidade de Atendimento"
        verbose_name_plural = "Unidades de Atendimento"

    def __str__(self):
        return f"{self.name} ({self.city}-{self.state})"

class UnitOpeningHour(models.Model):
    """Horários de funcionamento semanal da unidade (catalogUnitOpeningHour)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    unit = models.ForeignKey("catalog.Unit", db_column="unitid", on_delete=models.CASCADE)
    weekday = models.SmallIntegerField()
    opens_at = models.TimeField(db_column="opensat")
    closes_at = models.TimeField(db_column="closesat")

    class Meta:
        db_table = "catalogunitopeninghour"
        verbose_name = "Horário de Funcionamento"
        verbose_name_plural = "Horários de Funcionamento"

class NonWorkingDay(models.Model):
    """Feriados e dias sem atendimento (catalogNonWorkingDay)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    unit = models.ForeignKey("catalog.Unit", db_column="unitid", on_delete=models.CASCADE, null=True, blank=True)
    day_date = models.DateField(db_column="daydate")
    description = models.CharField(max_length=120)
    scope = models.CharField(max_length=20, default="national")
    created_at = models.DateTimeField(db_column="createdat", auto_now_add=True)

    class Meta:
        db_table = "catalognonworkingday"
        verbose_name = "Dia Não Útil"
        verbose_name_plural = "Dias Não Úteis"

class Service(models.Model):
    """Ficha orientativa de serviço público (catalogService)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=30)
    detailed_description = models.TextField(db_column="detaileddescription")
    eligibility = models.TextField()
    prerequisites = models.TextField(null=True, blank=True)
    is_free = models.BooleanField(db_column="isfree", default=True)
    cost_amount = models.DecimalField(db_column="costamount", max_digits=10, decimal_places=2, null=True, blank=True)
    average_deadline_days = models.IntegerField(db_column="averagedeadlinedays", default=0)
    channel = models.CharField(max_length=20, default="inPerson")
    external_url = models.CharField(db_column="externalurl", max_length=300, null=True, blank=True)
    status = models.CharField(max_length=20, default="draft")
    current_version = models.IntegerField(db_column="currentversion", default=1)
    created_by = models.ForeignKey("accounts.InternalUser", db_column="createdby", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(db_column="createdat", auto_now_add=True)
    updated_at = models.DateTimeField(db_column="updatedat", auto_now=True)
    deleted_at = models.DateTimeField(db_column="deletedat", null=True, blank=True)

    class Meta:
        db_table = "catalogservice"
        verbose_name = "Serviço Público"
        verbose_name_plural = "Serviços Públicos"

    def __str__(self):
        return self.name

class ServiceAgency(models.Model):
    """Associação N:N entre Serviços e Órgãos (catalogServiceAgency)."""
    service = CompositeKeyForeignKey(
        "catalog.Service",
        db_column="serviceid",
        related_name="service_agencies",
        on_delete=models.CASCADE,
        primary_key=True,
    )
    agency = models.ForeignKey(
        "catalog.Agency",
        db_column="agencyid",
        related_name="agency_services",
        on_delete=models.CASCADE,
    )

    class Meta:
        db_table = "catalogserviceagency"
        unique_together = (("service", "agency"),)

    def save(self, *args, **kwargs):
        if not self._state.adding and not kwargs.get("force_insert"):
            return
        kwargs["force_insert"] = True
        return super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        return type(self).objects.using(using).filter(
            service_id=self.service_id, agency_id=self.agency_id
        ).delete()

class UnitService(models.Model):
    """Associação N:N entre Unidades e Serviços (catalogUnitService)."""
    unit = CompositeKeyForeignKey(
        "catalog.Unit",
        db_column="unitid",
        related_name="unit_services",
        on_delete=models.CASCADE,
        primary_key=True,
    )
    service = models.ForeignKey(
        "catalog.Service",
        db_column="serviceid",
        related_name="service_units",
        on_delete=models.CASCADE,
    )
    is_active = models.BooleanField(db_column="isactive", default=True)
    created_at = models.DateTimeField(db_column="createdat", auto_now_add=True)

    class Meta:
        db_table = "catalogunitservice"
        unique_together = (("unit", "service"),)

    def save(self, *args, **kwargs):
        if not self._state.adding and not kwargs.get("force_insert"):
            type(self).objects.filter(
                unit_id=self.unit_id, service_id=self.service_id
            ).update(is_active=self.is_active)
            return
        kwargs["force_insert"] = True
        return super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        return type(self).objects.using(using).filter(
            unit_id=self.unit_id, service_id=self.service_id
        ).delete()

class ServiceStep(models.Model):
    """Etapas do guia passo a passo do serviço (catalogServiceStep)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey("catalog.Service", db_column="serviceid", related_name="steps", on_delete=models.CASCADE)
    step_order = models.IntegerField(db_column="steporder")
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=1000)
    estimated_time = models.CharField(db_column="estimatedtime", max_length=30, null=True, blank=True)
    created_at = models.DateTimeField(db_column="createdat", auto_now_add=True)

    class Meta:
        db_table = "catalogservicestep"
        ordering = ["step_order"]

class ServiceDocument(models.Model):
    """Checklist de documentos exigidos pelo serviço (catalogServiceDocument)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey("catalog.Service", db_column="serviceid", related_name="documents", on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    is_mandatory = models.BooleanField(db_column="ismandatory", default=True)
    template_url = models.CharField(db_column="templateurl", max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(db_column="createdat", auto_now_add=True)

    class Meta:
        db_table = "catalogservicedocument"
        ordering = ["name"]

class Faq(models.Model):
    """Perguntas frequentes vinculadas a serviços ou categorias (catalogFaq)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.CharField(max_length=300)
    answer = models.CharField(max_length=2000)
    service = models.ForeignKey("catalog.Service", db_column="serviceid", on_delete=models.CASCADE, null=True, blank=True)
    category = models.CharField(max_length=30, null=True, blank=True)
    is_active = models.BooleanField(db_column="isactive", default=True)
    created_at = models.DateTimeField(db_column="createdat", auto_now_add=True)
    updated_at = models.DateTimeField(db_column="updatedat", auto_now=True)

    class Meta:
        db_table = "catalogfaq"
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
        ordering = ["-created_at"]

class ServiceVersion(models.Model):
    """Histórico versionado das fichas de serviços (catalogServiceVersion)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey("catalog.Service", db_column="serviceid", related_name="versions", on_delete=models.CASCADE)
    version = models.IntegerField()
    snapshot = models.JSONField()
    created_by = models.ForeignKey("accounts.InternalUser", db_column="createdby", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(db_column="createdat", auto_now_add=True)

    class Meta:
        db_table = "catalogserviceversion"
        unique_together = (("service", "version"),)
        ordering = ["-version"]

class CatalogServiceSearchView(models.Model):
    """View relacional de busca unificada (vw_catalogServiceSearch)."""
    service_id = models.UUIDField(primary_key=True, db_column="serviceid")
    service_name = models.CharField(db_column="servicename", max_length=150)
    category = models.CharField(max_length=30)
    detailed_description = models.TextField(db_column="detaileddescription")
    eligibility = models.TextField()
    channel = models.CharField(max_length=20)
    status = models.CharField(max_length=20)
    agency_id = models.UUIDField(db_column="agencyid", null=True)
    agency_name = models.CharField(db_column="agencyname", max_length=120, null=True)
    agency_acronym = models.CharField(db_column="agencyacronym", max_length=10, null=True)
    synonyms_list = models.TextField(db_column="synonymslist")

    class Meta:
        managed = False
        db_table = "vw_catalogservicesearch"
