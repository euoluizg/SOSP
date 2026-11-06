from rest_framework import serializers

class CitizenRegisterSerializer(serializers.Serializer):
    fullName = serializers.CharField(max_length=255)
    cpf = serializers.CharField(max_length=14)
    socialName = serializers.CharField(max_length=255, required=False, allow_blank=True)
    birthDate = serializers.CharField(max_length=10)
    motherName = serializers.CharField(max_length=255)
    rg = serializers.CharField(max_length=20)
    rgIssuer = serializers.CharField(max_length=50)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True)
    isPcd = serializers.BooleanField(default=False)
    pcdDetails = serializers.CharField(required=False, allow_blank=True)
    zipCode = serializers.CharField(max_length=9)
    street = serializers.CharField(max_length=255)
    number = serializers.CharField(max_length=20)
    complement = serializers.CharField(required=False, allow_blank=True)
    neighborhood = serializers.CharField(max_length=100)
    city = serializers.CharField(max_length=100)
    state = serializers.CharField(max_length=2)

class CitizenLoginSerializer(serializers.Serializer):
    cpf = serializers.CharField(max_length=14)
    password = serializers.CharField(write_only=True)

class PasswordRecoveryRequestSerializer(serializers.Serializer):
    cpf = serializers.CharField(max_length=14)

class PasswordResetSerializer(serializers.Serializer):
    cpf = serializers.CharField(max_length=14)
    code = serializers.CharField(max_length=6)
    newPassword = serializers.CharField(write_only=True)

