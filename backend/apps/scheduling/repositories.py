import logging
import uuid
import datetime
from typing import Any, Dict, List, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

class SchedulingInMemoryRepository:
    def __init__(self):
        # Inicia estritamente vazio (Regra de Auditoria: zero agendamentos fictícios preexistentes)
        self._appointments: List[Dict[str, Any]] = []
        self._attachments: Dict[str, List[Dict[str, Any]]] = {}

    def seed_test_fixtures(self) -> None:
        """Carrega agendamentos sintéticos exclusivamente para testes automatizados sob demanda."""
        self._appointments = [
            {
                "id": "appt-001",
                "protocolNumber": "20261105-1042",
                "citizenId": "citizen-001",
                "citizenName": "Cidadão de Testes",
                "citizenCpfMasked": "***.444.777-**",
                "serviceId": "servico-emitir-rg",
                "serviceName": "Emitir Carteira de Identidade Nacional (CIN)",
                "agencyId": "orgao-ssp",
                "agencyName": "Secretaria de Estado da Segurança Pública",
                "unitId": "unidade-centro",
                "unitName": "Central Já! Centro",
                "unitAddress": "Rua do Comércio, 123 - Centro, Maceió - AL",
                "scheduledDate": "2026-11-10",
                "scheduledTime": "09:30",
                "status": "scheduled",
                "createdAt": "2026-11-05T10:00:00Z",
            },
            {
                "id": "appt-002",
                "protocolNumber": "20261015-8831",
                "citizenId": "citizen-001",
                "citizenName": "Cidadão de Testes",
                "citizenCpfMasked": "***.444.777-**",
                "serviceId": "servico-renovar-cnh",
                "serviceName": "Renovação da Carteira Nacional de Habilitação (CNH)",
                "agencyId": "orgao-detran",
                "agencyName": "Departamento Estadual de Trânsito",
                "unitId": "unidade-farol",
                "unitName": "Central Já! Shopping Farol",
                "unitAddress": "Av. Fernandes Lima, 500 - Farol, Maceió - AL",
                "scheduledDate": "2026-10-18",
                "scheduledTime": "14:00",
                "status": "completed",
                "createdAt": "2026-10-15T09:12:00Z",
            },
        ]
        self._attachments: Dict[str, List[Dict[str, Any]]] = {}

    def get_by_id(self, appointment_id: str) -> Optional[Dict[str, Any]]:
        for a in self._appointments:
            if a["id"] == appointment_id:
                return a
        return None

    def get_by_protocol(self, protocol_number: str) -> Optional[Dict[str, Any]]:
        for a in self._appointments:
            if a["protocolNumber"] == protocol_number:
                return a
        return None

    def list_by_citizen(self, citizen_id: str) -> List[Dict[str, Any]]:
        return [a for a in self._appointments if a["citizenId"] == citizen_id]

    def list_all(self) -> List[Dict[str, Any]]:
        return list(self._appointments)

    def save(self, data: Dict[str, Any]) -> Dict[str, Any]:
        for i, a in enumerate(self._appointments):
            if a.get("id") == data.get("id") or (data.get("protocolNumber") and a.get("protocolNumber") == data.get("protocolNumber")):
                self._appointments[i] = data
                return data
        self._appointments.insert(0, data)
        return data

    def get_slot_bookings(self, unit_id: str, slot_date: str) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for a in self._appointments:
            if (
                a.get("unitId") == unit_id
                and a.get("scheduledDate") == slot_date
                and a.get("status") in ("scheduled", "confirmed")
            ):
                t = a.get("scheduledTime", "")
                counts[t] = counts.get(t, 0) + 1
        return counts

    def add_attachment(self, protocol_number: str, attachment: Dict[str, Any]) -> None:
        if protocol_number not in self._attachments:
            self._attachments[protocol_number] = []
        self._attachments[protocol_number].append(attachment)

    def get_attachments(self, protocol_number: str) -> List[Dict[str, Any]]:
        return self._attachments.get(protocol_number, [])

_API_TO_DB_STATUS = {
    "scheduled": "scheduled",
    "waiting": "scheduled",
    "confirmed": "confirmed",
    "in_progress": "confirmed",
    "completed": "completed",
    "cancelled": "cancelled",
    "no_show": "noShow",
    "noShow": "noShow",
}

_DB_TO_API_STATUS = {
    "scheduled": "scheduled",
    "confirmed": "confirmed",
    "completed": "completed",
    "cancelled": "cancelled",
    "noShow": "no_show",
}

_APPT_TO_PROTOCOL_STATUS = {
    "scheduled": "scheduled",
    "confirmed": "inReview",
    "completed": "completed",
    "cancelled": "cancelled",
    "noShow": "cancelled",
}


class SchedulingDjangoORMRepository:
    """Implementação real de persistência PostgreSQL via Django ORM com bloqueio transacional (ADR-001 / Etapa 3)."""

    def get_by_id(self, appointment_id: str) -> Optional[Dict[str, Any]]:
        from .models import Appointment
        try:
            appt = Appointment.objects.filter(id=appointment_id).select_related("citizen", "service", "unit", "unit__agency").first()
            return self._to_dict(appt) if appt else None
        except Exception:
            return None

    def get_by_protocol(self, protocol_number: str) -> Optional[Dict[str, Any]]:
        from .models import Appointment
        appt = Appointment.objects.filter(protocol_number=protocol_number).select_related("citizen", "service", "unit", "unit__agency").first()
        return self._to_dict(appt) if appt else None

    def list_by_citizen(self, citizen_id: str) -> List[Dict[str, Any]]:
        from .models import Appointment
        try:
            appts = Appointment.objects.filter(citizen_id=citizen_id).select_related("citizen", "service", "unit", "unit__agency").order_by("-created_at")
            return [self._to_dict(a) for a in appts]
        except Exception:
            return []

    def list_all(self) -> List[Dict[str, Any]]:
        from .models import Appointment
        appts = Appointment.objects.all().select_related("citizen", "service", "unit", "unit__agency").order_by("-scheduled_date", "scheduled_time")
        return [self._to_dict(a) for a in appts]

    def get_slot_bookings(self, unit_id: str, slot_date: str) -> Dict[str, int]:
        from .models import Slot
        try:
            target_date = datetime.date.fromisoformat(slot_date)
            slots = Slot.objects.filter(unit_id=unit_id, slot_date=target_date)
            return {
                s.starts_at.strftime("%H:%M"): int(s.booked_count)
                for s in slots
            }
        except Exception:
            return {}

    def save(self, data: Dict[str, Any]) -> Dict[str, Any]:
        from .models import Appointment, Protocol, ProtocolTransition, Slot
        from apps.catalog.models import Service, Unit
        from apps.accounts.models import Citizen
        from django.db import IntegrityError, transaction
        from django.utils import timezone
        from common.exceptions import ProblemDetailsException

        with transaction.atomic():
            appt_id = data.get("id")
            appt = None
            if appt_id:
                try:
                    parsed_appt_uuid = uuid.UUID(str(appt_id))
                    appt = Appointment.objects.filter(id=parsed_appt_uuid).select_related("citizen", "service", "unit", "unit__agency").first()
                except (ValueError, TypeError):
                    appt = None

            db_status = _API_TO_DB_STATUS.get(data.get("status", "scheduled"), "scheduled")

            if not appt:
                service = Service.objects.filter(id=data["serviceId"]).first()
                unit = Unit.objects.filter(id=data["unitId"]).select_related("agency").first()
                citizen = Citizen.objects.filter(id=data["citizenId"]).first()

                if not service or not unit or not citizen:
                    if not citizen:
                        citizen = Citizen.objects.first()
                    if not unit:
                        unit = Unit.objects.select_related("agency").first()
                    if not service:
                        service = Service.objects.first()

                slot_date = data["scheduledDate"]
                slot_time = data["scheduledTime"]
                if isinstance(slot_date, str):
                    slot_date = datetime.date.fromisoformat(slot_date)
                if isinstance(slot_time, str):
                    parts = slot_time.split(":")
                    slot_time = datetime.time(int(parts[0]), int(parts[1]))

                slot = Slot.objects.select_for_update().filter(
                    unit=unit, slot_date=slot_date, starts_at=slot_time
                ).first()

                if slot:
                    if slot.booked_count >= slot.capacity:
                        raise ProblemDetailsException(
                            title="Vaga Esgotada",
                            detail="Não há vagas disponíveis neste horário.",
                            status_code=409,
                        )
                    slot.booked_count += 1
                    slot.save(update_fields=["booked_count", "updated_at"])
                else:
                    end_dt = datetime.datetime.combine(slot_date, slot_time) + datetime.timedelta(minutes=30)
                    slot = Slot.objects.create(
                        unit=unit,
                        slot_date=slot_date,
                        starts_at=slot_time,
                        ends_at=end_dt.time(),
                        capacity=4,
                        booked_count=1,
                    )

                try:
                    with transaction.atomic():
                        appt = Appointment.objects.create(
                            protocol_number=data["protocolNumber"],
                            citizen=citizen,
                            service=service,
                            unit=unit,
                            slot=slot,
                            scheduled_date=slot_date,
                            scheduled_time=slot_time,
                            status=db_status,
                            cancellation_reason=data.get("cancelReason"),
                        )
                except IntegrityError as exc:
                    err_msg = str(exc).lower()
                    if "uqschedulingappointmentactive" in err_msg or "citizenid" in err_msg:
                        raise ProblemDetailsException(
                            detail="Você já possui um agendamento ativo para este serviço.",
                            title="Agendamento Duplicado",
                            status_code=409,
                        )
                    raise

                proto = Protocol.objects.create(
                    protocol_number=data["protocolNumber"],
                    protocol_type="appointment",
                    citizen=citizen,
                    appointment=appt,
                    status="scheduled",
                )
                # Savepoint isolado: sob RLS p_protocol_trans_insert apenas server/admin podem inserir
                # em schedulingProtocolTransition, então falha de RLS aqui não pode abortar o agendamento do cidadão.
                try:
                    with transaction.atomic():
                        ProtocolTransition.objects.create(
                            protocol=proto,
                            from_status=None,
                            to_status="scheduled",
                            actor_type="citizen",
                            actor_id=citizen.id if citizen else None,
                            note="Agendamento presencial registrado no SOSP.",
                        )
                except Exception as exc:
                    logger.info("Transição inicial de protocolo ignorada sob RLS para cidadão: %s", exc)
            else:
                prev_db_status = appt.status
                appt.status = db_status
                if db_status == "cancelled":
                    appt.cancellation_reason = data.get("cancelReason") or appt.cancellation_reason or "Cancelado pelo solicitante"
                else:
                    appt.cancellation_reason = data.get("cancelReason", appt.cancellation_reason)
                appt.save()

                if prev_db_status != db_status:
                    if db_status == "cancelled" and appt.slot_id:
                        slot_obj = Slot.objects.select_for_update().filter(id=appt.slot_id).first()
                        if slot_obj and slot_obj.booked_count > 0:
                            slot_obj.booked_count -= 1
                            slot_obj.save(update_fields=["booked_count", "updated_at"])

                    proto = Protocol.objects.filter(appointment=appt).first()
                    if proto:
                        old_p_status = proto.status
                        new_p_status = _APPT_TO_PROTOCOL_STATUS.get(db_status, "inReview")
                        proto.status = new_p_status
                        if new_p_status in ("completed", "cancelled"):
                            proto.closed_at = timezone.now()
                        proto.save()
                        actor_id = data.get("_actorId")
                        actor_uuid = None
                        if actor_id:
                            try:
                                actor_uuid = uuid.UUID(str(actor_id))
                            except Exception:
                                actor_uuid = None
                        try:
                            with transaction.atomic():
                                ProtocolTransition.objects.create(
                                    protocol=proto,
                                    from_status=old_p_status,
                                    to_status=new_p_status,
                                    actor_type=data.get("_actorType", "servant"),
                                    actor_id=actor_uuid,
                                    note=data.get("_transitionNote") or data.get("cancelReason") or f"Status atualizado para {db_status}.",
                                )
                        except Exception as exc:
                            logger.info("Transição de protocolo ignorada sob RLS: %s", exc)

            return self._to_dict(appt)

    def add_attachment(self, protocol_number: str, attachment: Dict[str, Any]) -> None:
        from .models import Protocol, ProtocolAttachment
        proto = Protocol.objects.filter(protocol_number=protocol_number).first()
        if not proto:
            return

        allowed_mimes = ("image/jpeg", "image/png", "application/pdf")
        mime_type = attachment.get("mimeType") or "application/pdf"
        if mime_type not in allowed_mimes:
            fname = str(attachment.get("fileName", "")).lower()
            if fname.endswith(".png"):
                mime_type = "image/png"
            elif fname.endswith((".jpg", ".jpeg")):
                mime_type = "image/jpeg"
            else:
                mime_type = "application/pdf"

        raw_size = int(attachment.get("fileSize") or 0)
        safe_size = max(1024, min(raw_size if raw_size > 0 else 1024, 10485760))

        ProtocolAttachment.objects.create(
            protocol=proto,
            citizen=proto.citizen,
            file_name=str(attachment.get("fileName", "anexo.pdf"))[:255],
            file_size=safe_size,
            mime_type=mime_type,
            storage_key=attachment.get("s3Key", f"attachments/{protocol_number}/{attachment.get('fileName', 'anexo.pdf')}")[:500],
            antivirus_status="clean",
        )

    def get_attachments(self, protocol_number: str) -> List[Dict[str, Any]]:
        from .models import ProtocolAttachment
        atts = ProtocolAttachment.objects.filter(protocol__protocol_number=protocol_number).order_by("created_at")
        return [
            {
                "id": str(a.id),
                "protocolNumber": protocol_number,
                "fileName": a.file_name,
                "fileSize": a.file_size,
                "mimeType": a.mime_type,
                "contentType": a.mime_type,
                "uploadedAt": a.created_at.isoformat(),
            }
            for a in atts
        ]

    def _to_dict(self, a) -> Dict[str, Any]:
        unit = getattr(a, "unit", None)
        agency = getattr(unit, "agency", None) if unit else None
        unit_name = unit.name if unit else "Central Já!"
        service_name = a.service.name if getattr(a, "service", None) else "Serviço"
        citizen_name = a.citizen.full_name if getattr(a, "citizen", None) else "Cidadão"
        citizen_cpf = a.citizen.cpf if getattr(a, "citizen", None) else "00000000000"
        masked_cpf = f"***.{citizen_cpf[3:6]}.{citizen_cpf[6:9]}-**" if len(citizen_cpf) == 11 else "***.***.***-**"

        return {
            "id": str(a.id),
            "protocolNumber": a.protocol_number,
            "citizenId": str(a.citizen_id),
            "citizenName": citizen_name,
            "citizenCpfMasked": masked_cpf,
            "serviceId": str(a.service_id),
            "serviceName": service_name,
            "agencyId": str(getattr(unit, "agency_id", None) or getattr(a.service, "agency_id", "") or "orgao-ssp"),
            "agencyName": agency.name if agency else "Governo de Alagoas",
            "unitId": str(a.unit_id),
            "unitName": unit_name,
            "unitAddress": f"{getattr(unit, 'street', '')}, {getattr(unit, 'address_number', '')} - {getattr(unit, 'city', '')}",
            "scheduledDate": a.scheduled_date.isoformat() if hasattr(a.scheduled_date, "isoformat") else str(a.scheduled_date),
            "scheduledTime": a.scheduled_time.strftime("%H:%M") if hasattr(a.scheduled_time, "strftime") else str(a.scheduled_time)[:5],
            "status": _DB_TO_API_STATUS.get(a.status, a.status),
            "cancelReason": a.cancellation_reason,
            "cancelledAt": a.updated_at.isoformat() if a.status == "cancelled" else None,
            "createdAt": a.created_at.isoformat() if a.created_at else None,
        }

_scheduling_memory_repository = SchedulingInMemoryRepository()

def get_scheduling_repository():
    if getattr(settings, "REPOSITORY_BACKEND", "memory") == "orm":
        return SchedulingDjangoORMRepository()
    return _scheduling_memory_repository

class SchedulingRepositoryProxy:
    """Proxy dinâmico que seleciona a implementação configurada (memory ou orm)."""
    def __getattr__(self, name):
        repo = get_scheduling_repository()
        return getattr(repo, name)

scheduling_repository = SchedulingRepositoryProxy()
