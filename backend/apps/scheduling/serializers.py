from rest_framework import serializers

class CreateAppointmentSerializer(serializers.Serializer):
    serviceId = serializers.CharField()
    unitId = serializers.CharField()
    scheduledDate = serializers.CharField(max_length=10)
    scheduledTime = serializers.CharField(max_length=5)
    citizenId = serializers.CharField(required=False, default="citizen-001")

class CancelAppointmentSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)

