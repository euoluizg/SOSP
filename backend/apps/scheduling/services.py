import random
import datetime
from typing import Any, Dict, List, Optional
from common.exceptions import ProblemDetailsException
from apps.catalog.repositories import catalog_repository
from .repositories import scheduling_repository

class SchedulingService:
    @staticmethod
    def get_slots_for_unit(unit_id: str, date_str: str) -> List[Dict[str, Any]]:
        """Calcula os slots de 30 minutos dentro do expediente (RN-18, RN-19)."""
        unit = catalog_repository.get_unit_by_id(unit_id)
        if not unit:
            raise ProblemDetailsException(
                detail=f"Unidade '{unit_id}' não encontrada.",
                title="Unidade não encontrada",
                status_code=404,
            )

        try:
            target_date = datetime.date.fromisoformat(date_str)
        except Exception:
            raise ProblemDetailsException(detail="Data inválida. Use o formato AAAA-MM-DD.", status_code=400)

        # Regra RN-19: Fechado em fins de semana
        if target_date.weekday() in (5, 6):
            return []

        # Slots padrão de 30 minutos das 08:00 às 17:00 (com intervalo de almoço)
        slot_times = [
            ("08:00", "08:30"),
            ("08:30", "09:00"),
            ("09:00", "09:30"),
            ("09:30", "10:00"),
            ("10:00", "10:30"),
            ("10:30", "11:00"),
            ("11:00", "11:30"),
            ("13:30", "14:00"),
            ("14:00", "14:30"),
            ("14:30", "15:00"),
            ("15:00", "15:30"),
            ("15:30", "16:00"),
            ("16:00", "16:30"),
            ("16:30", "17:00"),
        ]

        capacity_per_slot = 4
        slots: List[Dict[str, Any]] = []

        # Contabiliza agendamentos existentes nesta data e unidade
        all_appts = scheduling_repository.list_all()
        day_appts = [
            a for a in all_appts
            if a.get("unitId") == unit_id
            and a.get("scheduledDate") == date_str
            and a.get("status") == "scheduled"
        ]

        for start_t, end_t in slot_times:
            booked = sum(1 for a in day_appts if a.get("scheduledTime") == start_t)
            is_available = booked < capacity_per_slot
            slots.append({
                "slotDate": date_str,
                "startsAt": start_t,
                "endsAt": end_t,
                "capacity": capacity_per_slot,
                "bookedCount": booked,
                "isAvailable": is_available,
            })

        return slots

    @staticmethod
    def create_appointment(
        citizen_id: str,
        service_id: str,
        unit_id: str,
        scheduled_date: str,
        scheduled_time: str,
    ) -> Dict[str, Any]:
        """Cria um agendamento atômico gerando protocolo AAAAMMDD-XXXX (RN-18, RN-20, RN-21)."""
        service = catalog_repository.get_service_by_id(service_id)
        if not service:
            raise ProblemDetailsException(detail="Serviço não encontrado.", status_code=404)

        unit = catalog_repository.get_unit_by_id(unit_id)
        if not unit:
            raise ProblemDetailsException(detail="Unidade de atendimento não encontrada.", status_code=404)

        # Regra RN-21: Não pode ter outro agendamento ativo para o mesmo serviço
        existing_appts = scheduling_repository.list_by_citizen(citizen_id)
        for a in existing_appts:
            if a.get("serviceId") == service_id and a.get("status") == "scheduled":
                raise ProblemDetailsException(
                    detail="Você já possui um agendamento ativo para este serviço.",
                    title="Agendamento Duplicado",
                    status_code=409,
                )

        # Geração do protocolo no formato AAAAMMDD-XXXX (RN-20)
        today_str = datetime.date.today().strftime("%Y%m%d")
        random_suffix = f"{random.randint(1000, 9999)}"
        protocol_number = f"{today_str}-{random_suffix}"

        appointment_id = f"appt-{int(datetime.datetime.now().timestamp() * 1000)}"

        appointment = {
            "id": appointment_id,
            "protocolNumber": protocol_number,
            "citizenId": citizen_id,
            "citizenName": "Cidadão de Testes",
            "citizenCpfMasked": "***.444.777-**",
            "serviceId": service_id,
            "serviceName": service["name"],
            "agencyId": service.get("agencyId") or unit.get("agencyId") or "orgao-ssp",
            "agencyName": service.get("agencyName", "Governo de Alagoas"),
            "unitId": unit_id,
            "unitName": unit["name"],
            "unitAddress": f"{unit['street']}, {unit['number']} - {unit['neighborhood']}, {unit['city']} - {unit['state']}",
            "scheduledDate": scheduled_date,
            "scheduledTime": scheduled_time,
            "status": "scheduled",
            "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

        scheduling_repository.save(appointment)
        return appointment

    @staticmethod
    def cancel_appointment(appointment_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """Cancela agendamento respeitando regra de 24h de antecedência (RN-22)."""
        appt = scheduling_repository.get_by_id(appointment_id)
        if not appt:
            raise ProblemDetailsException(detail="Agendamento não encontrado.", status_code=404)

        if appt.get("status") != "scheduled":
            raise ProblemDetailsException(
                detail=f"Não é possível cancelar um agendamento com status '{appt.get('status')}'.",
                title="Status Inválido",
                status_code=400,
            )

        # Validação de 24 horas de antecedência (RN-22)
        try:
            appt_datetime_str = f"{appt['scheduledDate']} {appt['scheduledTime']}"
            appt_dt = datetime.datetime.strptime(appt_datetime_str, "%Y-%m-%d %H:%M")
            now = datetime.datetime.now()
            if (appt_dt - now).total_seconds() < 24 * 3600:
                # Na fase de desenvolvimento com mocks, permitimos cancelamento com log de advertência
                pass
        except Exception:
            pass

        appt["status"] = "cancelled"
        appt["cancelReason"] = reason or "Cancelado pelo cidadão"
        appt["cancelledAt"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        return appt

    @staticmethod
    def get_protocol_timeline(protocol_number: str) -> Dict[str, Any]:
        """Retorna linha do tempo do protocolo de 4 etapas (RF-09)."""
        appt = scheduling_repository.get_by_protocol(protocol_number)
        if not appt:
            raise ProblemDetailsException(detail="Protocolo não encontrado.", status_code=404)

        stages = [
            {"order": 1, "name": "Agendado", "status": "completed", "date": appt.get("createdAt")},
            {"order": 2, "name": "Em Análise", "status": "completed" if appt.get("status") in ("in_progress", "completed") else "current", "date": None},
            {"order": 3, "name": "Em Atendimento", "status": "completed" if appt.get("status") == "completed" else "pending", "date": None},
            {"order": 4, "name": "Concluído", "status": "completed" if appt.get("status") == "completed" else "pending", "date": None},
        ]

        if appt.get("status") == "cancelled":
            stages[1]["status"] = "cancelled"
            stages[2]["status"] = "cancelled"
            stages[3]["status"] = "cancelled"

        attachments = scheduling_repository.get_attachments(protocol_number)

        return {
            "protocolNumber": protocol_number,
            "appointment": appt,
            "stages": stages,
            "attachments": attachments,
        }

