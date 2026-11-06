from rest_framework import serializers

class CitizenRegisterSerializer(serializers.Serializer):
    fullName = serializers.CharField(max_length=255)
    cpf = serializers.CharField(max_length=14)
    socialName = serializers.CharField(max_length=255, required=False, allow_blank=True)
    birthDate = serializers.CharField(max_length=10)
    gender = serializers.CharField(max_length=50, required=False, allow_blank=True, default="")
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
    cpf = serializers.CharField(max_length=14)
    password = serializers.CharField(write_only=True)

class PasswordRecoveryRequestSerializer(serializers.Serializer):
    cpf = serializers.CharField(max_length=14)

class PasswordResetSerializer(serializers.Serializer):
    cpf = serializers.CharField(max_length=14)
    code = serializers.CharField(max_length=6)
    newPassword = serializers.CharField(write_only=True)

