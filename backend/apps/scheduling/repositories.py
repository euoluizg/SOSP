from typing import Any, Dict, List, Optional

class SchedulingInMemoryRepository:
    def __init__(self):
        self._appointments: List[Dict[str, Any]] = [
            {
                "id": "appt-001",
                "protocolNumber": "20261105-1042",
                "citizenId": "citizen-001",
                "citizenName": "Cidadão de Testes",
                "citizenCpfMasked": "***.444.777-**",
                "serviceId": "servico-emitir-rg",
                "serviceName": "Emitir Carteira de Identidade Nacional (CIN)",
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
        self._appointments.insert(0, data)
        return data

    def add_attachment(self, protocol_number: str, attachment: Dict[str, Any]) -> None:
        if protocol_number not in self._attachments:
            self._attachments[protocol_number] = []
        self._attachments[protocol_number].append(attachment)

    def get_attachments(self, protocol_number: str) -> List[Dict[str, Any]]:
        return self._attachments.get(protocol_number, [])

scheduling_repository = SchedulingInMemoryRepository()

