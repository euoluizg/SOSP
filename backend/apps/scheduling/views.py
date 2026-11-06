from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CreateAppointmentSerializer, CancelAppointmentSerializer
from .services import SchedulingService
from .repositories import scheduling_repository
from common.exceptions import ProblemDetailsException

class UnitSlotsView(APIView):
    """Retorna slots de 30 minutos disponíveis para uma unidade e data (RN-18)."""
    def get(self, request, unit_id):
        date_str = request.query_params.get("date")
        if not date_str:
            raise ProblemDetailsException(detail="O parâmetro 'date' (AAAA-MM-DD) é obrigatório.", status_code=400)
        slots = SchedulingService.get_slots_for_unit(unit_id, date_str)
        return Response(slots, status=status.HTTP_200_OK)

class AppointmentCreateListView(APIView):
    def post(self, request):
        serializer = CreateAppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        appt = SchedulingService.create_appointment(
            citizen_id=data.get("citizenId", "citizen-001"),
            service_id=data["serviceId"],
            unit_id=data["unitId"],
            scheduled_date=data["scheduledDate"],
            scheduled_time=data["scheduledTime"],
        )
        return Response(appt, status=status.HTTP_201_CREATED)

    def get(self, request):
        appts = scheduling_repository.list_all()
        return Response(appts, status=status.HTTP_200_OK)

class AppointmentDetailView(APIView):
    def get(self, request, appointment_id):
        appt = scheduling_repository.get_by_id(appointment_id)
        if not appt:
            raise ProblemDetailsException(detail="Agendamento não encontrado.", status_code=404)
        return Response(appt, status=status.HTTP_200_OK)

class AppointmentCancelView(APIView):
    def post(self, request, appointment_id):
        serializer = CancelAppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get("reason")
        result = SchedulingService.cancel_appointment(appointment_id, reason)
        return Response(result, status=status.HTTP_200_OK)

    def patch(self, request, appointment_id):
        return self.post(request, appointment_id)

class AppointmentByProtocolView(APIView):
    def get(self, request, protocol_number):
        appt = scheduling_repository.get_by_protocol(protocol_number)
        if not appt:
            raise ProblemDetailsException(detail="Protocolo não encontrado.", status_code=404)
        return Response(appt, status=status.HTTP_200_OK)

class CitizenAppointmentsView(APIView):
    def get(self, request, citizen_id):
        appts = scheduling_repository.list_by_citizen(citizen_id)
        return Response(appts, status=status.HTTP_200_OK)

class ProtocolTimelineView(APIView):
    def get(self, request, protocol_number):
        timeline = SchedulingService.get_protocol_timeline(protocol_number)
        return Response(timeline, status=status.HTTP_200_OK)

class ProtocolDocumentsUploadView(APIView):
    def post(self, request, protocol_number):
        appt = scheduling_repository.get_by_protocol(protocol_number)
        if not appt:
            raise ProblemDetailsException(detail="Protocolo não encontrado.", status_code=404)

        files = request.FILES.getlist("file") or request.FILES.getlist("files")
        if not files:
            uploaded_name = request.data.get("fileName", "documento.pdf")
            size_mb = float(request.data.get("sizeMb", 1.5))
        else:
            f = files[0]
            uploaded_name = f.name
            size_mb = f.size / (1024 * 1024)

        if size_mb > 10.0:
            raise ProblemDetailsException(
                detail="O arquivo excede o limite máximo permitido de 10 MB (RS-04).",
                title="Arquivo muito grande",
                status_code=400,
            )

        doc_record = {
            "id": f"doc-{int(status.HTTP_200_OK)}",
            "protocolNumber": protocol_number,
            "fileName": uploaded_name,
            "sizeMb": round(size_mb, 2),
            "uploadedAt": "2026-11-05T12:00:00Z",
            "url": f"/mock-storage/{uploaded_name}",
        }
        scheduling_repository.add_attachment(protocol_number, doc_record)
        return Response(doc_record, status=status.HTTP_201_CREATED)

