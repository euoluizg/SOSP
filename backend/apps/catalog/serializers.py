from rest_framework import serializers


class AgencyCreateSerializer(serializers.Serializer):
    """Validador para criação de órgão público (catalogAgency)."""
    name = serializers.CharField(max_length=120, allow_blank=False)
    acronym = serializers.CharField(max_length=10, allow_blank=False)
    sphere = serializers.ChoiceField(choices=["municipal", "state", "federal"], default="state")
    description = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")

    def validate_name(self, value):
        trimmed = value.strip()
        if len(trimmed) < 2:
            raise serializers.ValidationError("O nome do órgão deve conter ao menos 2 caracteres.")
        return trimmed

    def validate_acronym(self, value):
        trimmed = value.strip().upper()
        if not trimmed:
            raise serializers.ValidationError("A sigla do órgão não pode ser vazia.")
        return trimmed


class AgencyUpdateSerializer(serializers.Serializer):
    """Validador para atualização de dados cadastrais de órgão público."""
    name = serializers.CharField(max_length=120, required=False, allow_blank=False)
    acronym = serializers.CharField(max_length=10, required=False, allow_blank=False)
    sphere = serializers.ChoiceField(choices=["municipal", "state", "federal"], required=False)
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)
    isActive = serializers.BooleanField(required=False)

    def validate_name(self, value):
        trimmed = value.strip()
        if not trimmed:
            raise serializers.ValidationError("O nome do órgão não pode ser vazio.")
        if len(trimmed) < 2:
            raise serializers.ValidationError("O nome do órgão deve conter ao menos 2 caracteres.")
        return trimmed

    def validate_acronym(self, value):
        trimmed = value.strip().upper()
        if not trimmed:
            raise serializers.ValidationError("A sigla do órgão não pode ser vazia.")
        return trimmed


class UnitCreateSerializer(serializers.Serializer):
    """Validador para criação de unidade de atendimento (catalogUnit)."""
    agencyId = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=120)
    cep = serializers.CharField(max_length=10, required=False, allow_blank=True, default="")
    zipCode = serializers.CharField(max_length=10, required=False, allow_blank=True, default="")
    street = serializers.CharField(max_length=120)
    number = serializers.CharField(max_length=10, required=False, allow_blank=True, default="S/N")
    neighborhood = serializers.CharField(max_length=80, required=False, allow_blank=True, default="Centro")
    city = serializers.CharField(max_length=80, default="Maceió")
    state = serializers.CharField(max_length=2, default="AL")
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    openingHours = serializers.CharField(max_length=120, required=False, allow_blank=True, default="08:00 às 17:00")
    dailyLimit = serializers.IntegerField(min_value=1, max_value=10000, default=60)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    isPcdAccessible = serializers.BooleanField(default=True)
    hasPriorityService = serializers.BooleanField(default=True)

    def validate(self, attrs):
        raw_zip = "".join(filter(str.isdigit, attrs.get("zipCode") or attrs.get("cep") or ""))
        if not raw_zip:
            raw_zip = "57020100"
        if len(raw_zip) != 8:
            raise serializers.ValidationError({"cep": "Informe um CEP válido com 8 dígitos."})
        attrs["zipCode"] = raw_zip
        attrs["state"] = attrs.get("state", "AL").strip().upper()[:2]
        attrs["phone"] = "".join(filter(str.isdigit, attrs.get("phone") or ""))[:11]
        return attrs


class UnitUpdateSerializer(serializers.Serializer):
    """Validador para atualização ou desativação lógica de unidade."""
    name = serializers.CharField(max_length=120, required=False)
    dailyLimit = serializers.IntegerField(min_value=1, max_value=10000, required=False)
    isPcdAccessible = serializers.BooleanField(required=False)
    hasPriorityService = serializers.BooleanField(required=False)
    isActive = serializers.BooleanField(required=False)


class ServiceCreateSerializer(serializers.Serializer):
    """Validador para criação de serviço público (catalogService)."""
    name = serializers.CharField(max_length=150)
    category = serializers.CharField(max_length=50, default="documents")
    channel = serializers.ChoiceField(choices=["online", "inPerson", "hybrid"], default="inPerson")
    agencyId = serializers.CharField(max_length=64)
    description = serializers.CharField(max_length=5000)
    whoCanUse = serializers.CharField(max_length=2000, required=False, allow_blank=True, default="Cidadãos residentes em Alagoas.")
    prerequisites = serializers.CharField(max_length=2000, required=False, allow_blank=True, default="")
    isFree = serializers.BooleanField(default=True)
    costAmount = serializers.FloatField(required=False, allow_null=True, default=None)
    averageDeadlineDays = serializers.IntegerField(min_value=0, default=5)
    externalUrl = serializers.CharField(max_length=300, required=False, allow_blank=True, default="")

    def validate(self, attrs):
        if attrs.get("isFree"):
            attrs["costAmount"] = None
        else:
            cost = attrs.get("costAmount")
            if cost is None or cost < 0.01:
                raise serializers.ValidationError({"costAmount": "Serviços pagos exigem valor superior a R$ 0,01."})
        return attrs


class ServiceUpdateSerializer(serializers.Serializer):
    """Validador para atualização ou desativação lógica de serviço público."""
    name = serializers.CharField(max_length=150, required=False)
    category = serializers.CharField(max_length=50, required=False)
    channel = serializers.ChoiceField(choices=["online", "inPerson", "hybrid"], required=False)
    description = serializers.CharField(max_length=5000, required=False)
    whoCanUse = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    isFree = serializers.BooleanField(required=False)
    costAmount = serializers.FloatField(required=False, allow_null=True)
    averageDeadlineDays = serializers.IntegerField(min_value=0, required=False)
    isActive = serializers.BooleanField(required=False)
