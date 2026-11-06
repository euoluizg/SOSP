import time
from typing import Any, Dict, List, Optional
from django.contrib.auth.hashers import make_password

class CitizenInMemoryRepository:
    """Repositório em memória para Cidadãos e Usuários (sem banco nesta fase)."""
    def __init__(self):
        # Usuário inicial de testes (alinhado com o frontend)
        hashed_password = make_password("S0sp@2026!Fort3")
        self._citizens: Dict[str, Dict[str, Any]] = {
            "citizen-001": {
                "id": "citizen-001",
                "fullName": "Cidadão de Testes",
                "cpf": "11144477705",
                "socialName": "",
                "birthDate": "1990-05-15",
                "motherName": "Maria de Testes",
                "rg": "1234567",
                "rgIssuer": "SSP/AL",
                "email": "cidadao@exemplo.com.br",
                "phone": "82999887766",
                "passwordHash": hashed_password,
                "isPcd": False,
                "pcdDetails": "",
                "zipCode": "57020100",
                "street": "Rua do Comércio",
                "number": "123",
                "complement": "Apto 101",
                "neighborhood": "Centro",
                "city": "Maceió",
                "state": "AL",
                "role": "citizen",
                "isActive": True,
                "createdAt": "2026-11-01T10:00:00Z",
            }
        }
        # Controle de tentativas de login por CPF (RN-29)
        self._failed_attempts: Dict[str, int] = {}
        self._lockout_until: Dict[str, float] = {}
        # Códigos de recuperação de senha válidos por 15 min (RN-30)
        self._recovery_codes: Dict[str, Dict[str, Any]] = {}

    def get_by_id(self, citizen_id: str) -> Optional[Dict[str, Any]]:
        return self._citizens.get(citizen_id)

    def get_by_cpf(self, cpf: str) -> Optional[Dict[str, Any]]:
        clean_cpf = "".join(filter(str.isdigit, cpf))
        for c in self._citizens.values():
            if c.get("cpf") == clean_cpf:
                return c
        return None

    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        clean_email = email.strip().lower()
        for c in self._citizens.values():
            if c.get("email", "").lower() == clean_email:
                return c
        return None

    def save(self, data: Dict[str, Any]) -> Dict[str, Any]:
        citizen_id = data.get("id") or f"citizen-{len(self._citizens) + 1:03d}"
        data["id"] = citizen_id
        if "cpf" in data:
            data["cpf"] = "".join(filter(str.isdigit, data["cpf"]))
        self._citizens[citizen_id] = data
        return data

    def record_failed_attempt(self, cpf: str) -> int:
        clean_cpf = "".join(filter(str.isdigit, cpf))
        attempts = self._failed_attempts.get(clean_cpf, 0) + 1
        self._failed_attempts[clean_cpf] = attempts
        if attempts >= 5:
            # Bloqueio de 5 minutos (300 segundos) - RN-29
            self._lockout_until[clean_cpf] = time.time() + 300
        return attempts

    def is_locked_out(self, cpf: str) -> tuple[bool, int]:
        clean_cpf = "".join(filter(str.isdigit, cpf))
        lock_until = self._lockout_until.get(clean_cpf, 0)
        now = time.time()
        if lock_until > now:
            remaining = int(lock_until - now)
            return True, remaining
        if lock_until > 0 and lock_until <= now:
            self._failed_attempts[clean_cpf] = 0
            del self._lockout_until[clean_cpf]
        return False, 0

    def reset_failed_attempts(self, cpf: str) -> None:
        clean_cpf = "".join(filter(str.isdigit, cpf))
        self._failed_attempts.pop(clean_cpf, None)
        self._lockout_until.pop(clean_cpf, None)

    def set_recovery_code(self, cpf: str, code: str) -> None:
        clean_cpf = "".join(filter(str.isdigit, cpf))
        # Válido por 15 minutos (900 segundos) - RN-30
        self._recovery_codes[clean_cpf] = {
            "code": code,
            "expires_at": time.time() + 900,
        }

    def verify_recovery_code(self, cpf: str, code: str) -> bool:
        clean_cpf = "".join(filter(str.isdigit, cpf))
        rec = self._recovery_codes.get(clean_cpf)
        if not rec:
            return False
        if time.time() > rec["expires_at"]:
            del self._recovery_codes[clean_cpf]
            return False
        return rec["code"] == code

    def clear_recovery_code(self, cpf: str) -> None:
        clean_cpf = "".join(filter(str.isdigit, cpf))
        self._recovery_codes.pop(clean_cpf, None)

# Instância Singleton do repositório em memória
citizen_repository = CitizenInMemoryRepository()

