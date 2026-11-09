from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import CreateAppointmentSerializer, CancelAppointmentSerializer
from .services import SchedulingService
from .repositories import scheduling_repository
from common.exceptions import ProblemDetailsException


def check_appointment_access(request_user, appt) -> None:
    """
    Valida autorização de acesso ao agendamento (ownership e RBAC — ADR-003, RS-01 a RS-03, RN-36):
    - Cidadão: apenas o proprietário (appt['citizenId'] == user.id). Se não for, 404 (anti-enumeração / STRIDE).
    - Servidor: apenas se for da mesma unidade (appt['unitId'] == user.unit_id) ou órgão (RN-36). Se não for, 403.
    - Administrador: acesso irrestrito.
    """
    user_role = getattr(request_user, "role", "citizen")
    user_id = str(request_user.id)

    if user_role in ("citizen", "cidadao"):
        if str(appt.get("citizenId")) != user_id:
            raise ProblemDetailsException(
                detail="Agendamento não encontrado.",
                status_code=404,
                title="Recurso não encontrado",
            )
        return

    if user_role in ("server", "servant", "servidor"):
        server_unit = str(getattr(request_user, "unit_id", "") or "")
        server_agency = str(getattr(request_user, "agency_id", "") or "")
        appt_unit = str(appt.get("unitId") or "")
        appt_agency = str(appt.get("agencyId") or "")

        unit_match = bool(server_unit and appt_unit and server_unit == appt_unit)
        agency_match = bool(server_agency and appt_agency and server_agency == appt_agency)

        if not (unit_match or agency_match):
            raise ProblemDetailsException(
                detail="Servidor não possui permissão para acessar recursos fora de sua unidade/órgão de lotação (RN-36).",
                status_code=403,
                title="Acesso não autorizado",
            )
        return

    if user_role in ("admin", "administrator", "superadmin", "administrador"):
        return

    raise ProblemDetailsException(
        detail="Acesso não autorizado ao recurso.",
        status_code=403,
        title="Acesso não autorizado",
    )


class UnitSlotsView(APIView):
    """Retorna slots de 30 minutos disponíveis para uma unidade e data (RN-18)."""

    permission_classes = [AllowAny]

    def get(self, request, unit_id):
        date_str = request.query_params.get("date")
        if not date_str:
            raise ProblemDetailsException(
                detail="O parâmetro 'date' (AAAA-MM-DD) é obrigatório.", status_code=400
            )
        slots = SchedulingService.get_slots_for_unit(unit_id, date_str)
        return Response(slots, status=status.HTTP_200_OK)


class AppointmentCreateListView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        idempotency_key = request.headers.get("Idempotency-Key") or request.META.get(
            "HTTP_IDEMPOTENCY_KEY"
        )
        if not idempotency_key:
            raise ProblemDetailsException(
                detail="O cabeçalho 'Idempotency-Key' é obrigatório para criação de agendamento.",
                title="Cabeçalho Ausente",
                status_code=400,
            )

        serializer = CreateAppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if request.user and getattr(request.user, "is_authenticated", False):
            # Cidadão autenticado: a identidade DEVE ser a do próprio usuário (anti-spoofing)
            if getattr(request.user, "role", "citizen") in ("citizen", "cidadao"):
                citizen_id = str(request.user.id)
            else:
                # Servidor ou admin agendando para terceiro: usa citizenId do payload
                citizen_id = str(data.get("citizenId") or request.user.id)
        else:
            citizen_id = data.get("citizenId", "citizen-001")

        appt = SchedulingService.create_appointment(
            citizen_id=citizen_id,
            service_id=data["serviceId"],
            unit_id=data["unitId"],
            scheduled_date=data["scheduledDate"],
            scheduled_time=data["scheduledTime"],
        )
        return Response(appt, status=status.HTTP_201_CREATED)


class AppointmentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, appointment_id):
        appt = scheduling_repository.get_by_id(appointment_id)
        if not appt:
            raise ProblemDetailsException(detail="Agendamento não encontrado.", status_code=404)
        check_appointment_access(request.user, appt)
        return Response(appt, status=status.HTTP_200_OK)


class AppointmentCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, appointment_id):
        appt = scheduling_repository.get_by_id(appointment_id)
        if not appt:
            raise ProblemDetailsException(detail="Agendamento não encontrado.", status_code=404)
        check_appointment_access(request.user, appt)

        serializer = CancelAppointmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data.get("reason")
        result = SchedulingService.cancel_appointment(appointment_id, reason)
        return Response(result, status=status.HTTP_200_OK)

    def patch(self, request, appointment_id):
        return self.post(request, appointment_id)


class AppointmentByProtocolView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, protocol_number):
        appt = scheduling_repository.get_by_protocol(protocol_number)
        if not appt:
            raise ProblemDetailsException(detail="Protocolo não encontrado.", status_code=404)
        check_appointment_access(request.user, appt)
        return Response(appt, status=status.HTTP_200_OK)


class CitizenAppointmentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, citizen_id):
        user_role = getattr(request.user, "role", "citizen")
        user_id = str(request.user.id)

        # Cidadão só pode listar os próprios agendamentos (RS-01, STRIDE)
        if user_role in ("citizen", "cidadao"):
            if user_id != str(citizen_id):
                raise ProblemDetailsException(
                    detail="Cidadão não encontrado ou você não possui permissão para consultar estes agendamentos.",
                    status_code=404,
                    title="Recurso não encontrado",
                )
            appts = scheduling_repository.list_by_citizen(citizen_id)
            return Response(appts, status=status.HTTP_200_OK)

        # Servidor só lista agendamentos da sua unidade ou órgão (RN-36)
        if user_role in ("server", "servant", "servidor"):
            appts = scheduling_repository.list_by_citizen(citizen_id)
            server_unit = str(getattr(request.user, "unit_id", "") or "")
            server_agency = str(getattr(request.user, "agency_id", "") or "")
            filtered = [
                a
                for a in appts
                if (server_unit and str(a.get("unitId") or "") == server_unit)
                or (server_agency and str(a.get("agencyId") or "") == server_agency)
            ]
            return Response(filtered, status=status.HTTP_200_OK)

        # Administrador: acesso irrestrito
        if user_role in ("admin", "administrator", "superadmin", "administrador"):
            appts = scheduling_repository.list_by_citizen(citizen_id)
            return Response(appts, status=status.HTTP_200_OK)

        raise ProblemDetailsException(
            detail="Acesso não autorizado.",
            status_code=403,
            title="Acesso não autorizado",
        )


class ProtocolTimelineView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, protocol_number):
        appt = scheduling_repository.get_by_protocol(protocol_number)
        if not appt:
            raise ProblemDetailsException(detail="Protocolo não encontrado.", status_code=404)
        check_appointment_access(request.user, appt)
        timeline = SchedulingService.get_protocol_timeline(protocol_number)
        return Response(timeline, status=status.HTTP_200_OK)


class ProtocolDirectView(APIView):
    """
    Bloqueia chamadas diretas a /protocols/{protocolNumber} retornando 405 Method Not Allowed.
    O endpoint de consulta oficial é /appointments/by-protocol/{protocol} ou /protocols/{protocolNumber}/timeline.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, protocol_number):
        raise ProblemDetailsException(
            detail="A rota /protocols/{protocolNumber} não permite o método GET diretamente. O endpoint de consulta é /appointments/by-protocol/{protocol} ou /protocols/{protocolNumber}/timeline.",
            status_code=405,
            title="Método não permitido",
            type_uri="https://sosp.al.gov.br/errors/405",
        )

    def post(self, request, protocol_number):
        return self.get(request, protocol_number)

    def put(self, request, protocol_number):
        return self.get(request, protocol_number)

    def delete(self, request, protocol_number):
        return self.get(request, protocol_number)


class ProtocolDocumentsUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, protocol_number):
        appt = scheduling_repository.get_by_protocol(protocol_number)
        if not appt:
            raise ProblemDetailsException(detail="Protocolo não encontrado.", status_code=404)
        check_appointment_access(request.user, appt)

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
