import time
import datetime
from typing import Any, Dict, List, Optional
from django.conf import settings
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

class CitizenDjangoORMRepository:
    """Implementação real de persistência PostgreSQL via Django ORM (ADR-001 / Etapa 3)."""

    def get_by_id(self, citizen_id: str) -> Optional[Dict[str, Any]]:
        from .models import Citizen
        c = Citizen.objects.filter(id=citizen_id, is_active=True, deleted_at__isnull=True).first()
        return self._to_dict(c) if c else None

    def get_by_cpf(self, cpf: str) -> Optional[Dict[str, Any]]:
        from .models import Citizen
        clean_cpf = "".join(filter(str.isdigit, cpf))
        c = Citizen.objects.filter(cpf=clean_cpf, is_active=True, deleted_at__isnull=True).first()
        return self._to_dict(c) if c else None

    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        from .models import Citizen
        c = Citizen.objects.filter(email__iexact=email.strip(), is_active=True, deleted_at__isnull=True).first()
        return self._to_dict(c) if c else None

    def save(self, data: Dict[str, Any]) -> Dict[str, Any]:
        from .models import Citizen, Gender
        clean_cpf = "".join(filter(str.isdigit, data["cpf"]))
        
        gender_id = data.get("genderId")
        gender = Gender.objects.filter(id=gender_id).first() if gender_id else None
        if not gender:
            gender = Gender.objects.first()
            if not gender:
                gender = Gender.objects.create(name="Não Informado", sort_order=99)

        citizen_id = data.get("id")
        citizen = None
        if citizen_id:
            citizen = Citizen.objects.filter(id=citizen_id).first()

        if not citizen:
            citizen = Citizen(
                cpf=clean_cpf,
                full_name=data.get("fullName", "").strip(),
                birth_date=data.get("birthDate"),
                email=data.get("email", "").strip().lower(),
                phone="".join(filter(str.isdigit, data.get("phone", ""))),
                password_hash=data.get("passwordHash", ""),
                password_salt=data.get("passwordSalt", "salt"),
                gender=gender,
                is_pcd=data.get("isPcd", False),
                disability_description=data.get("pcdDetails") or data.get("disabilityDescription", ""),
                mother_name=data.get("motherName", "").strip(),
                father_name=data.get("fatherName", "").strip() or None,
                zip_code="".join(filter(str.isdigit, data.get("zipCode", ""))),
                street=data.get("street", "").strip(),
                neighborhood=data.get("neighborhood", "").strip(),
                city=data.get("city", "").strip(),
                state=data.get("state", "").strip(),
                address_number=str(data.get("addressNumber") or data.get("number", "S/N")).strip(),
                address_complement=data.get("complement") or data.get("addressComplement", ""),
                avatar_url=data.get("avatarUrl", ""),
            )
            citizen.save()
        else:
            if "fullName" in data: citizen.full_name = data["fullName"]
            if "email" in data: citizen.email = data["email"].strip().lower()
            if "phone" in data: citizen.phone = "".join(filter(str.isdigit, data["phone"]))
            citizen.save()

        return self._to_dict(citizen)

    def record_failed_attempt(self, cpf: str) -> int:
        from .models import Citizen, LoginAttempt
        from django.utils import timezone

        clean_cpf = "".join(filter(str.isdigit, cpf))
        LoginAttempt.objects.create(cpf=clean_cpf, was_successful=False)

        c = Citizen.objects.filter(cpf=clean_cpf, is_active=True, deleted_at__isnull=True).first()
        if not c:
            return 1

        c.login_attempts += 1
        if c.login_attempts >= 5:
            c.blocked_until = timezone.now() + datetime.timedelta(minutes=5)
        c.save(update_fields=["login_attempts", "blocked_until", "updated_at"])
        return c.login_attempts

    def is_locked_out(self, cpf: str) -> tuple[bool, int]:
        from .models import Citizen
        from django.utils import timezone

        clean_cpf = "".join(filter(str.isdigit, cpf))
        c = Citizen.objects.filter(cpf=clean_cpf).first()
        if not c or not c.blocked_until:
            return False, 0
        now = timezone.now()
        if c.blocked_until > now:
            remaining = int((c.blocked_until - now).total_seconds())
            return True, remaining
        c.login_attempts = 0
        c.blocked_until = None
        c.save(update_fields=["login_attempts", "blocked_until", "updated_at"])
        return False, 0

    def reset_failed_attempts(self, cpf: str) -> None:
        from .models import Citizen
        clean_cpf = "".join(filter(str.isdigit, cpf))
        Citizen.objects.filter(cpf=clean_cpf).update(login_attempts=0, blocked_until=None)

    def set_recovery_code(self, cpf: str, code: str) -> None:
        from .models import Citizen
        from django.utils import timezone
        clean_cpf = "".join(filter(str.isdigit, cpf))
        exp = timezone.now() + datetime.timedelta(minutes=15)
        Citizen.objects.filter(cpf=clean_cpf).update(
            recovery_code_hash=code,
            recovery_code_expires_at=exp
        )

    def verify_recovery_code(self, cpf: str, code: str) -> bool:
        from .models import Citizen
        from django.utils import timezone
        clean_cpf = "".join(filter(str.isdigit, cpf))
        c = Citizen.objects.filter(cpf=clean_cpf).first()
        if not c or not c.recovery_code_hash:
            return False
        if c.recovery_code_expires_at and timezone.now() > c.recovery_code_expires_at:
            return False
        return c.recovery_code_hash == code

    def clear_recovery_code(self, cpf: str) -> None:
        from .models import Citizen
        clean_cpf = "".join(filter(str.isdigit, cpf))
        Citizen.objects.filter(cpf=clean_cpf).update(
            recovery_code_hash=None,
            recovery_code_expires_at=None
        )

    def _to_dict(self, c) -> Dict[str, Any]:
        return {
            "id": str(c.id),
            "fullName": c.full_name,
            "cpf": c.cpf,
            "birthDate": c.birth_date.isoformat() if hasattr(c.birth_date, "isoformat") else str(c.birth_date),
            "motherName": c.mother_name,
            "fatherName": c.father_name or "",
            "rg": "",
            "rgIssuer": "",
            "email": c.email,
            "phone": c.phone,
            "passwordHash": c.password_hash,
            "passwordSalt": c.password_salt,
            "isPcd": c.is_pcd,
            "pcdDetails": c.disability_description or "",
            "zipCode": c.zip_code,
            "street": c.street,
            "number": c.address_number,
            "complement": c.address_complement or "",
            "neighborhood": c.neighborhood,
            "city": c.city,
            "state": c.state,
            "role": "citizen",
            "isActive": c.is_active,
            "createdAt": c.created_at.isoformat() if c.created_at else "",
        }

_citizen_memory_repository = CitizenInMemoryRepository()

def get_citizen_repository():
    if getattr(settings, "REPOSITORY_BACKEND", "memory") == "orm":
        return CitizenDjangoORMRepository()
    return _citizen_memory_repository

class CitizenRepositoryProxy:
    """Proxy dinâmico que seleciona a implementação configurada (memory ou orm)."""
    def __getattr__(self, name):
        repo = get_citizen_repository()
        return getattr(repo, name)

citizen_repository = CitizenRepositoryProxy()
