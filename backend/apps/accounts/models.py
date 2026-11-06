import uuid
from django.db import models

class Gender(models.Model):
    """Gêneros para cadastro de cidadão (accountsGender)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=40)
    sort_order = models.SmallIntegerField(db_column="sortorder", default=0)
    is_active = models.BooleanField(db_column="isactive", default=True)
    created_at = models.DateTimeField(db_column="createdat", auto_now_add=True)
    updated_at = models.DateTimeField(db_column="updatedat", auto_now=True)

    class Meta:
        db_table = "accountsgender"
        verbose_name = "Gênero"
        verbose_name_plural = "Gêneros"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name

class Citizen(models.Model):
    """Cidadão cadastrado no SOSP (accountsCitizen)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cpf = models.CharField(max_length=11)
    full_name = models.CharField(db_column="fullname", max_length=120)
    birth_date = models.DateField(db_column="birthdate")
    email = models.CharField(max_length=200)
    phone = models.CharField(max_length=11)
    password_hash = models.TextField(db_column="passwordhash")
    password_salt = models.TextField(db_column="passwordsalt")
    recovery_code_hash = models.TextField(db_column="recoverycodehash", null=True, blank=True)
    recovery_code_expires_at = models.DateTimeField(db_column="recoverycodeexpiresat", null=True, blank=True)
    login_attempts = models.IntegerField(db_column="loginattempts", default=0)
    blocked_until = models.DateTimeField(db_column="blockeduntil", null=True, blank=True)
    gender = models.ForeignKey("accounts.Gender", db_column="genderid", on_delete=models.PROTECT)
    is_pcd = models.BooleanField(db_column="ispcd", default=False)
    disability_description = models.CharField(db_column="disabilitydescription", max_length=120, null=True, blank=True)
    mother_name = models.CharField(db_column="mothername", max_length=120)
    father_name = models.CharField(db_column="fathername", max_length=120, null=True, blank=True)
    zip_code = models.CharField(db_column="zipcode", max_length=8)
    street = models.CharField(max_length=120)
    neighborhood = models.CharField(max_length=80)
    city = models.CharField(max_length=80)
    state = models.CharField(max_length=2)
    address_number = models.CharField(db_column="addressnumber", max_length=10)
    address_complement = models.CharField(db_column="addresscomplement", max_length=60, null=True, blank=True)
    avatar_url = models.CharField(db_column="avatarurl", max_length=500, null=True, blank=True)
    govbr_subject_id = models.CharField(db_column="govbrsubjectid", max_length=255, null=True, blank=True)
    email_verified_at = models.DateTimeField(db_column="emailverifiedat", null=True, blank=True)
    last_login_at = models.DateTimeField(db_column="lastloginat", null=True, blank=True)
    is_active = models.BooleanField(db_column="isactive", default=True)
    created_at = models.DateTimeField(db_column="createdat", auto_now_add=True)
    updated_at = models.DateTimeField(db_column="updatedat", auto_now=True)
    deleted_at = models.DateTimeField(db_column="deletedat", null=True, blank=True)

    class Meta:
        db_table = "accountscitizen"
        verbose_name = "Cidadão"
        verbose_name_plural = "Cidadãos"

    def __str__(self):
        return f"{self.full_name} ({self.cpf})"

class InternalUser(models.Model):
    """Servidores públicos e administradores (accountsInternalUser)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cpf = models.CharField(max_length=11)
    full_name = models.CharField(db_column="fullname", max_length=120)
    email = models.CharField(max_length=200)
    registration_number = models.CharField(db_column="registrationnumber", max_length=20)
    agency_id = models.UUIDField(db_column="agencyid", null=True, blank=True)
    role = models.CharField(max_length=20)
    can_manage_catalog = models.BooleanField(db_column="canmanagecatalog", default=False)
    password_hash = models.CharField(db_column="passwordhash", max_length=255)
    must_change_password = models.BooleanField(db_column="mustchangepassword", default=True)
    is_active = models.BooleanField(db_column="isactive", default=True)
    last_login_at = models.DateTimeField(db_column="lastloginat", null=True, blank=True)
    created_at = models.DateTimeField(db_column="createdat", auto_now_add=True)
    updated_at = models.DateTimeField(db_column="updatedat", auto_now=True)
    deleted_at = models.DateTimeField(db_column="deletedat", null=True, blank=True)

    class Meta:
        db_table = "accountsinternaluser"
        verbose_name = "Usuário Interno"
        verbose_name_plural = "Usuários Internos"

    def __str__(self):
        return f"{self.full_name} ({self.role})"

class Session(models.Model):
    """Sessões ativas com expiração de 30 minutos (accountsSession)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject_type = models.CharField(db_column="subjecttype", max_length=20)
    subject_id = models.UUIDField(db_column="subjectid")
    token_hash = models.CharField(db_column="tokenhash", max_length=64)
    ip_address = models.GenericIPAddressField(db_column="ipaddress", null=True, blank=True)
    user_agent = models.CharField(db_column="useragent", max_length=500, null=True, blank=True)
    expires_at = models.DateTimeField(db_column="expiresat")
    revoked_at = models.DateTimeField(db_column="revokedat", null=True, blank=True)
    created_at = models.DateTimeField(db_column="createdat", auto_now_add=True)

    class Meta:
        db_table = "accountssession"
        verbose_name = "Sessão"
        verbose_name_plural = "Sessões"

class LoginAttempt(models.Model):
    """Tentativas de login para controle de lockout após 5 erros (accountsLoginAttempt)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cpf = models.CharField(max_length=11)
    ip_address = models.GenericIPAddressField(db_column="ipaddress", null=True, blank=True)
    was_successful = models.BooleanField(db_column="wassuccessful", default=False)
    attempted_at = models.DateTimeField(db_column="attemptedat", auto_now_add=True)

    class Meta:
        db_table = "accountsloginattempt"
        verbose_name = "Tentativa de Login"
        verbose_name_plural = "Tentativas de Login"

class PasswordReset(models.Model):
    """Recuperação de senha via código seguro de 6 dígitos (accountsPasswordReset)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    internal_user = models.ForeignKey("accounts.InternalUser", db_column="internaluserid", on_delete=models.CASCADE)
    code_hash = models.CharField(db_column="codehash", max_length=255)
    expires_at = models.DateTimeField(db_column="expiresat")
    used_at = models.DateTimeField(db_column="usedat", null=True, blank=True)
    created_at = models.DateTimeField(db_column="createdat", auto_now_add=True)

    class Meta:
        db_table = "accountspasswordreset"
        verbose_name = "Redefinição de Senha"
        verbose_name_plural = "Redefinições de Senha"
