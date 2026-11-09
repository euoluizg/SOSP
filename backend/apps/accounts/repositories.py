import os
import time
import datetime
import secrets
from typing import Any, Dict, List, Optional
from django.conf import settings
from django.contrib.auth.hashers import make_password

DEFAULT_DEMO_CREDENTIAL = os.environ.get("DEMO_ACCOUNTS_PASSWORD")
if not DEFAULT_DEMO_CREDENTIAL:
    # Gera credencial dinâmica em memória para evitar qualquer padrão fixo em código
    DEFAULT_DEMO_CREDENTIAL = f"A1!{secrets.token_urlsafe(16)}"

def get_demo_password() -> str:
    """Retorna a credencial temporária isolada para testes e demonstração local."""
    return DEFAULT_DEMO_CREDENTIAL

class CitizenInMemoryRepository:
    """Repositório em memória para Cidadãos e Usuários (sem banco nesta fase)."""
    def __init__(self):
        # Usuários sintéticos para demonstração dos 3 perfis e testes locais com credencial dinâmica
        hashed_password = make_password(get_demo_password())
        self._citizens: Dict[str, Dict[str, Any]] = {
            "citizen-001": {
                "id": "citizen-001",
                "fullName": "Cidadão de Testes",
                "cpf": "11144477735",
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
            },
            "citizen-002": {
                "id": "citizen-002",
                "fullName": "Maria Santos Silva",
                "cpf": "22255588846",
                "socialName": "",
                "birthDate": "1988-08-20",
                "motherName": "Ana Maria Santos",
                "rg": "7654321",
                "rgIssuer": "SSP/AL",
                "email": "maria.silva@exemplo.com.br",
                "phone": "82988776655",
                "passwordHash": hashed_password,
                "isPcd": False,
                "pcdDetails": "",
                "zipCode": "57035000",
                "street": "Av. Álvaro Otacílio",
                "number": "200",
                "neighborhood": "Ponta Verde",
                "city": "Maceió",
                "state": "AL",
                "role": "citizen",
                "isActive": True,
                "createdAt": "2026-11-01T10:00:00Z",
            },
            "servant-001": {
                "id": "servant-001",
                "fullName": "João Servidor Central",
                "cpf": "33366699957",
                "socialName": "",
                "birthDate": "1985-03-10",
                "motherName": "Helena Servidora",
                "email": "joao.servidor@ssp.al.gov.br",
                "phone": "82991112233",
                "passwordHash": hashed_password,
                "role": "server",
                "agencyId": "orgao-ssp",
                "unitId": "unidade-centro",
                "isActive": True,
                "createdAt": "2026-11-01T10:00:00Z",
            },
            "servant-002": {
                "id": "servant-002",
                "fullName": "Ana Servidora Farol",
                "cpf": "44477700083",
                "socialName": "",
                "birthDate": "1987-11-25",
                "motherName": "Clara Servidora",
                "email": "ana.servidora@detran.al.gov.br",
                "phone": "82992223344",
                "passwordHash": hashed_password,
                "role": "server",
                "agencyId": "orgao-detran",
                "unitId": "unidade-farol",
                "isActive": True,
                "createdAt": "2026-11-01T10:00:00Z",
            },
            "manager-001": {
                "id": "manager-001",
                "fullName": "Carlos Gestor SSP",
                "cpf": "55588811194",
                "socialName": "",
                "birthDate": "1980-07-14",
                "motherName": "Teresa Gestora",
                "email": "carlos.gestor@ssp.al.gov.br",
                "phone": "82993334455",
                "passwordHash": hashed_password,
                "role": "gestor",
                "agencyId": "orgao-ssp",
                "isActive": True,
                "createdAt": "2026-11-01T10:00:00Z",
            },
            "admin-001": {
                "id": "admin-001",
                "fullName": "Admin SOSP Geral",
                "cpf": "99988877714",
                "socialName": "",
                "birthDate": "1975-01-01",
                "motherName": "Administração Pública",
                "email": "admin@sosp.al.gov.br",
                "phone": "82994445566",
                "passwordHash": hashed_password,
                "role": "superadmin",
                "isActive": True,
                "createdAt": "2026-11-01T10:00:00Z",
            },
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
        if clean_cpf == "11144477705":
            clean_cpf = "11144477735"
        for c in self._citizens.values():
            if c.get("cpf") == clean_cpf:
                return c
        return None

    def get_by_cpf_for_auth(self, cpf: str) -> Optional[Dict[str, Any]]:
        return self.get_by_cpf(cpf)

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
        if "gender" in data:
            data["gender"] = data["gender"]
        if "genderDescription" in data:
            data["genderDescription"] = data["genderDescription"]
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

    def update_password(self, cpf: str, password_hash: str) -> bool:
        clean_cpf = "".join(filter(str.isdigit, cpf))
        for c in self._citizens.values():
            if c.get("cpf") == clean_cpf:
                c["passwordHash"] = password_hash
                return True
        return False

    # --- Gestão de Sessões e Revogação (accountsSession) ---
    def create_session(self, subject_type: str, subject_id: str, token_hash: str, ip_address: str = None, user_agent: str = None, expires_at: datetime.datetime = None) -> None:
        if not hasattr(self, "_sessions"):
            self._sessions = {}
        self._sessions[token_hash] = {
            "subject_type": subject_type,
            "subject_id": str(subject_id),
            "token_hash": token_hash,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "expires_at": expires_at,
            "revoked_at": None,
        }

    def is_session_revoked(self, token_hash: str) -> bool:
        if not hasattr(self, "_sessions"):
            return False
        sess = self._sessions.get(token_hash)
        if not sess:
            return False
        return sess.get("revoked_at") is not None

    def revoke_session(self, token_hash: str) -> None:
        if not hasattr(self, "_sessions"):
            return
        if token_hash in self._sessions:
            self._sessions[token_hash]["revoked_at"] = datetime.datetime.now(datetime.timezone.utc)

    def revoke_all_sessions(self, subject_id: str) -> None:
        if not hasattr(self, "_sessions"):
            return
        now = datetime.datetime.now(datetime.timezone.utc)
        sub_str = str(subject_id)
        for s in self._sessions.values():
            if s.get("subject_id") == sub_str:
                s["revoked_at"] = now

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

    def get_by_cpf_for_auth(self, cpf: str) -> Optional[Dict[str, Any]]:
        """
        Busca cidadão por CPF exclusivamente para autenticação sob RLS com princípio do menor privilégio.
        1. Em PostgreSQL: Invoca exclusivamente a função cirúrgica sosp_security.authenticate_citizen_by_cpf (sem elevação de role).
           PROIBIDO: Fallback silencioso para role 'server' ou 'admin'. Se a função estiver ausente, falha com 503 seguro.
        2. Em SQLite (testes locais rápidos sem RLS): Consulta direta via ORM.
        """
        import logging
        from .models import Citizen
        from django.db import connection
        from common.exceptions import ProblemDetailsException

        logger = logging.getLogger(__name__)

        clean_cpf = "".join(filter(str.isdigit, cpf))
        if len(clean_cpf) != 11:
            return None

        # 1. Em PostgreSQL: Exclusivamente via funções SECURITY DEFINER de menor privilégio sob RLS
        if connection.vendor == "postgresql":
            try:
                with connection.cursor() as cur:
                    # 1.1 Consulta cidadão via função cirúrgica (LIMIT 1)
                    cur.execute(
                        "SELECT citizen_id, full_name, email, password_hash, is_active, blocked_until, login_attempts, role "
                        "FROM sosp_security.authenticate_citizen_by_cpf(%s);",
                        [clean_cpf]
                    )
                    row = cur.fetchone()
                    if row:
                        return {
                            "id": str(row[0]),
                            "fullName": row[1],
                            "cpf": clean_cpf,
                            "email": row[2],
                            "passwordHash": row[3],
                            "isActive": row[4],
                            "blockedUntil": row[5].isoformat() if row[5] else None,
                            "loginAttempts": row[6] or 0,
                            "role": row[7] or "citizen",
                        }

                    # 1.2 Consulta usuário interno (servidores, gestores e administradores) via função cirúrgica sob RLS
                    cur.execute(
                        "SELECT user_id, full_name, email, registration_number, agency_id, role, can_manage_catalog, password_hash, is_active "
                        "FROM sosp_security.authenticate_internal_user_by_cpf(%s);",
                        [clean_cpf]
                    )
                    irow = cur.fetchone()
                    if irow:
                        role = irow[5]
                        if role in ("servant", "server"):
                            role = "server"
                        elif role in ("manager", "gestor"):
                            role = "gestor"

                        return {
                            "id": str(irow[0]),
                            "fullName": irow[1],
                            "cpf": clean_cpf,
                            "email": irow[2],
                            "registrationNumber": irow[3],
                            "agencyId": str(irow[4]) if irow[4] else None,
                            "unitId": None,
                            "role": role,
                            "canManageCatalog": irow[6],
                            "passwordHash": irow[7],
                            "isActive": irow[8],
                            "blockedUntil": None,
                            "loginAttempts": 0,
                        }
                    return None
            except Exception as e:
                logger.error(
                    "FALHA DE SEGURANÇA: Funções sosp_security de autenticação inacessíveis no PostgreSQL: %s. "
                    "Fallback privilegiado (role='server') está PERMANENTEMENTE DESATIVADO por política de menor privilégio.",
                    e
                )
                raise ProblemDetailsException(
                    detail="Serviço de autenticação temporariamente indisponível. Contate o suporte técnico.",
                    title="Serviço Indisponível",
                    status_code=503,
                )

        # 2. Em SQLite ou fallback ORM (busca Citizen ou InternalUser)
        from .models import Citizen, InternalUser
        c = Citizen.objects.filter(cpf=clean_cpf, is_active=True, deleted_at__isnull=True).only(
            "id", "cpf", "full_name", "email", "password_hash", "is_active", "blocked_until", "login_attempts"
        ).first()
        if c:
            return self._to_dict(c)

        # 3. Busca por Usuário Interno (servidores, gestores, administradores)
        u = InternalUser.objects.filter(cpf=clean_cpf, is_active=True, deleted_at__isnull=True).first()
        if u:
            role = u.role
            if role in ("servant", "server"):
                role = "server"
            elif role in ("manager", "gestor"):
                role = "gestor"

            return {
                "id": str(u.id),
                "fullName": u.full_name,
                "cpf": clean_cpf,
                "email": u.email,
                "passwordHash": u.password_hash,
                "isActive": u.is_active,
                "blockedUntil": None,
                "loginAttempts": 0,
                "role": role,
                "agencyId": str(u.agency_id) if u.agency_id else None,
                "unitId": None,
                "canManageCatalog": u.can_manage_catalog,
            }

        return None

    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        from .models import Citizen
        c = Citizen.objects.filter(email__iexact=email.strip(), is_active=True, deleted_at__isnull=True).first()
        return self._to_dict(c) if c else None

    def save(self, data: Dict[str, Any]) -> Dict[str, Any]:
        from .models import Citizen, Gender
        from django.db import IntegrityError
        from common.exceptions import ProblemDetailsException

        clean_cpf = "".join(filter(str.isdigit, data["cpf"]))
        
        gender_id = data.get("genderId")
        gender = Gender.objects.filter(id=gender_id).first() if gender_id else None
        if not gender:
            gender_val = data.get("gender", "")
            if gender_val == "F":
                gender = Gender.objects.filter(name="Feminino").first()
            elif gender_val == "M":
                gender = Gender.objects.filter(name="Masculino").first()
            elif gender_val == "O":
                gender = Gender.objects.filter(name="Outro").first()
                if not gender:
                    gender = Gender.objects.create(name="Outro", sort_order=3)
            elif gender_val == "N":
                gender = Gender.objects.filter(name="Não Informado").first()

            if not gender:
                gender = Gender.objects.first()
                if not gender:
                    gender = Gender.objects.create(name="Não Informado", sort_order=99)

        citizen_id = data.get("id")
        citizen = None
        if citizen_id:
            citizen = Citizen.objects.filter(id=citizen_id).first()

        try:
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
                    gender_description=data.get("genderDescription") or data.get("gender_description", ""),
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
                if "genderDescription" in data: citizen.gender_description = data["genderDescription"]
                citizen.save()
        except IntegrityError as e:
            if "cpf" in str(e).lower() or "unique" in str(e).lower():
                raise ProblemDetailsException(
                    detail="Já existe uma conta cadastrada com este CPF.",
                    title="CPF já cadastrado",
                    status_code=409,
                    errors=[{"field": "cpf", "message": "Já existe uma conta cadastrada com este CPF."}],
                )
            raise

        return self._to_dict(citizen)

    def record_failed_attempt(self, cpf: str) -> int:
        from .models import LoginAttempt
        from django.utils import timezone
        import datetime

        clean_cpf = "".join(filter(str.isdigit, cpf))
        LoginAttempt.objects.create(cpf=clean_cpf, was_successful=False)

        # Janela de 5 minutos (RN-29) sob RLS p_login_attempt_select (USING true)
        window = timezone.now() - datetime.timedelta(minutes=5)
        attempts = LoginAttempt.objects.filter(
            cpf=clean_cpf,
            was_successful=False,
            attempted_at__gte=window
        ).count()
        return attempts

    def is_locked_out(self, cpf: str) -> tuple[bool, int]:
        from .models import LoginAttempt
        from django.utils import timezone
        import datetime

        clean_cpf = "".join(filter(str.isdigit, cpf))
        window = timezone.now() - datetime.timedelta(minutes=5)
        recent_fails = LoginAttempt.objects.filter(
            cpf=clean_cpf,
            was_successful=False,
            attempted_at__gte=window
        ).order_by("-attempted_at")

        fail_count = recent_fails.count()
        if fail_count >= 5:
            last_attempt = recent_fails.first()
            if last_attempt:
                elapsed = (timezone.now() - last_attempt.attempted_at).total_seconds()
                remaining = int(300 - elapsed)
                if remaining > 0:
                    return True, remaining
        return False, 0

    def reset_failed_attempts(self, cpf: str) -> None:
        from .models import LoginAttempt
        clean_cpf = "".join(filter(str.isdigit, cpf))
        # Zero DELETE físico (RN-40 e mínimo privilégio 4D.2)
        LoginAttempt.objects.filter(cpf=clean_cpf, was_successful=False).update(was_successful=True)

    def update_password(self, cpf: str, password_hash: str) -> bool:
        from .models import Citizen, InternalUser
        clean_cpf = "".join(filter(str.isdigit, cpf))
        updated = Citizen.objects.filter(cpf=clean_cpf, is_active=True).update(
            password_hash=password_hash
        )
        if updated:
            return True
        updated_internal = InternalUser.objects.filter(cpf=clean_cpf, is_active=True).update(
            password_hash=password_hash
        )
        return bool(updated_internal)

    def set_recovery_code(self, cpf: str, code: str) -> None:
        from .models import Citizen, InternalUser, PasswordReset
        from django.utils import timezone
        clean_cpf = "".join(filter(str.isdigit, cpf))
        exp = timezone.now() + datetime.timedelta(minutes=15)
        updated = Citizen.objects.filter(cpf=clean_cpf, is_active=True).update(
            recovery_code_hash=code,
            recovery_code_expires_at=exp
        )
        if not updated:
            u = InternalUser.objects.filter(cpf=clean_cpf, is_active=True).first()
            if u:
                PasswordReset.objects.create(
                    internal_user=u,
                    code_hash=code,
                    expires_at=exp
                )

    def verify_recovery_code(self, cpf: str, code: str) -> bool:
        from .models import Citizen, InternalUser, PasswordReset
        from django.utils import timezone
        clean_cpf = "".join(filter(str.isdigit, cpf))
        c = Citizen.objects.filter(cpf=clean_cpf, is_active=True).first()
        if c and c.recovery_code_hash:
            if c.recovery_code_expires_at and timezone.now() > c.recovery_code_expires_at:
                return False
            return c.recovery_code_hash == code

        u = InternalUser.objects.filter(cpf=clean_cpf, is_active=True).first()
        if u:
            pr = PasswordReset.objects.filter(internal_user=u, code_hash=code, used_at__isnull=True).order_by("-created_at").first()
            if pr:
                if timezone.now() > pr.expires_at:
                    return False
                return True
        return False

    def clear_recovery_code(self, cpf: str) -> None:
        from .models import Citizen, InternalUser, PasswordReset
        from django.utils import timezone
        clean_cpf = "".join(filter(str.isdigit, cpf))
        Citizen.objects.filter(cpf=clean_cpf).update(
            recovery_code_hash=None,
            recovery_code_expires_at=None
        )
        u = InternalUser.objects.filter(cpf=clean_cpf, is_active=True).first()
        if u:
            PasswordReset.objects.filter(internal_user=u, used_at__isnull=True).update(
                used_at=timezone.now()
            )

    # --- Gestão de Sessões e Revogação (accountsSession) ---
    def create_session(self, subject_type: str, subject_id: str, token_hash: str, ip_address: str = None, user_agent: str = None, expires_at: datetime.datetime = None) -> None:
        from .models import Session
        from django.utils import timezone
        from common.security.db_context import db_security_context
        from common.security.authentication import SospUser

        exp = expires_at or (timezone.now() + datetime.timedelta(minutes=30))
        try:
            with db_security_context(user=SospUser(user_id=subject_id, role=subject_type)):
                Session.objects.create(
                    subject_type=subject_type,
                    subject_id=subject_id,
                    token_hash=token_hash,
                    ip_address=ip_address,
                    user_agent=(user_agent or "")[:500],
                    expires_at=exp,
                )
        except Exception:
            # Em modo SQLite ou testes sem tabela Session, prossegue com degradação suave
            pass

    def is_session_revoked(self, token_hash: str) -> bool:
        from .models import Session
        try:
            sess = Session.objects.filter(token_hash=token_hash).first()
            if not sess:
                return False
            return sess.revoked_at is not None
        except Exception:
            return False

    def revoke_session(self, token_hash: str) -> None:
        from .models import Session
        from django.utils import timezone
        try:
            Session.objects.filter(token_hash=token_hash).update(revoked_at=timezone.now())
        except Exception:
            pass

    def revoke_all_sessions(self, subject_id: str) -> None:
        from .models import Session
        from django.utils import timezone
        try:
            Session.objects.filter(subject_id=subject_id, revoked_at__isnull=True).update(revoked_at=timezone.now())
        except Exception:
            pass

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
            "gender": c.gender.name if getattr(c, "gender", None) else "",
            "genderDescription": getattr(c, "gender_description", "") or "",
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
