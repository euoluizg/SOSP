from rest_framework import serializers

class AgencyUpdateSerializer(serializers.Serializer):
    """Validador para atualização de dados cadastrais de órgão público."""
    name = serializers.CharField(max_length=120, required=False, allow_blank=False)
    acronym = serializers.CharField(max_length=10, required=False, allow_blank=False)
    sphere = serializers.CharField(max_length=20, required=False)
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
