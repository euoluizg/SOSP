from rest_framework import serializers

class CitizenRegisterSerializer(serializers.Serializer):
    fullName = serializers.CharField(max_length=255)
    cpf = serializers.CharField(max_length=14)
    socialName = serializers.CharField(max_length=255, required=False, allow_blank=True)
    birthDate = serializers.CharField(max_length=10)
    gender = serializers.CharField(max_length=50, required=False, allow_blank=True, default="")
    genderDescription = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
    motherName = serializers.CharField(max_length=255)
    rg = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    rgIssuer = serializers.CharField(max_length=50, required=False, allow_blank=True, default="")
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    mobilePhone = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    landlinePhone = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    password = serializers.CharField(write_only=True)
    isPcd = serializers.BooleanField(default=False)
    pcdDetails = serializers.CharField(required=False, allow_blank=True, default="")
    disabilityType = serializers.CharField(required=False, allow_blank=True, default="")
    zipCode = serializers.CharField(max_length=10, required=False, allow_blank=True, default="")
    cep = serializers.CharField(max_length=10, required=False, allow_blank=True, default="")
    street = serializers.CharField(max_length=255)
    number = serializers.CharField(max_length=20)
    complement = serializers.CharField(required=False, allow_blank=True, default="")
    neighborhood = serializers.CharField(max_length=100)
    city = serializers.CharField(max_length=100)
    state = serializers.CharField(max_length=2)

    def validate_gender(self, value):
        if value and value not in ("F", "M", "O", "N"):
            raise serializers.ValidationError("Selecione uma opção de gênero válida.")
        return value

    def validate(self, attrs):
        # Normalização de campos com alias (CEP/zipCode, celular/telefone, pcdDetails/disabilityType)
        zip_code = attrs.get("zipCode") or attrs.get("cep") or ""
        if not zip_code:
            raise serializers.ValidationError({"cep": "O CEP / Código postal é obrigatório."})
        attrs["zipCode"] = zip_code

        phone = attrs.get("phone") or attrs.get("mobilePhone") or attrs.get("landlinePhone") or ""
        if not phone:
            raise serializers.ValidationError({"phone": "O telefone de contato é obrigatório."})
        attrs["phone"] = phone

        if not attrs.get("pcdDetails") and attrs.get("disabilityType"):
            attrs["pcdDetails"] = attrs["disabilityType"]

        return attrs

class CitizenLoginSerializer(serializers.Serializer):
    cpf = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True)

class PasswordRecoveryRequestSerializer(serializers.Serializer):
    cpf = serializers.CharField(max_length=14)

class PasswordResetSerializer(serializers.Serializer):
    cpf = serializers.CharField(max_length=14)
    code = serializers.CharField(max_length=6)
    newPassword = serializers.CharField(write_only=True)

class ChangePasswordSerializer(serializers.Serializer):
    currentPassword = serializers.CharField(write_only=True)
    newPassword = serializers.CharField(write_only=True)
    confirmPassword = serializers.CharField(write_only=True, required=False, allow_blank=True)

    def validate(self, attrs):
        confirm = attrs.get("confirmPassword")
        if confirm and attrs.get("newPassword") != confirm:
            raise serializers.ValidationError({"confirmPassword": "A confirmação de senha não coincide com a nova senha."})
        return attrs


class InternalUserCreateSerializer(serializers.Serializer):
    """Validador para criação de servidor/administrador (RF-12)."""
    fullName = serializers.CharField(min_length=3, max_length=120)
    cpf = serializers.CharField(max_length=14)
    email = serializers.EmailField(max_length=200)
    registrationNumber = serializers.CharField(min_length=2, max_length=20)
    role = serializers.ChoiceField(choices=["server", "gestor", "manager", "admin", "superadmin"], default="server")
    agencyId = serializers.CharField(required=False, allow_blank=True, allow_null=True, default=None)
    unitId = serializers.CharField(required=False, allow_blank=True, allow_null=True, default=None)
    canManageCatalog = serializers.BooleanField(default=False)
    temporaryPassword = serializers.CharField(write_only=True, min_length=8, required=False, allow_blank=True, default="")

    def validate_cpf(self, value):
        digits = "".join(filter(str.isdigit, value))
        if len(digits) != 11:
            raise serializers.ValidationError("Informe um CPF válido com 11 dígitos.")
        return digits

    def validate_registrationNumber(self, value):
        cleaned = value.strip().upper()
        import re
        if not re.match(r"^[A-Za-z0-9-]{1,20}$", cleaned):
            raise serializers.ValidationError("A matrícula deve conter até 20 caracteres alfanuméricos ou hífen.")
        return cleaned

