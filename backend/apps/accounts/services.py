import re
import secrets
import datetime
import hashlib
import logging
from typing import Any, Dict, List, Tuple, Optional
from django.conf import settings
from django.db import transaction
from django.contrib.auth.hashers import make_password, check_password
from common.exceptions import ProblemDetailsException
from common.security.authentication import generate_sosp_token
from .repositories import citizen_repository

logger = logging.getLogger(__name__)

def validate_cpf(cpf: str) -> bool:
    """Valida o formato e os dois dígitos verificadores do CPF."""
    clean = "".join(filter(str.isdigit, cpf))
    if len(clean) != 11:
        return False
    if clean == clean[0] * 11:
        return False

    # 1º dígito verificador
    s = sum(int(clean[i]) * (10 - i) for i in range(9))
    r = (s * 10) % 11
    if r in (10, 11):
        r = 0
    if r != int(clean[9]):
        return False

    # 2º dígito verificador
    s = sum(int(clean[i]) * (11 - i) for i in range(10))
    r = (s * 10) % 11
    if r in (10, 11):
        r = 0
    if r != int(clean[10]):
        return False

    return True

def validate_birth_date(birth_date_str: str) -> Tuple[bool, str]:
    """Valida data de nascimento e idade mínima de 12 anos (RF-01)."""
    try:
        birth = datetime.date.fromisoformat(birth_date_str)
    except Exception:
        return False, "Data de nascimento inválida."

    today = datetime.date.today()
    if birth > today:
        return False, "A data de nascimento não pode ser no futuro."

    age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
    if age < 12:
        return False, "O cidadão deve ter no mínimo 12 anos para criar uma conta."

    return True, ""

def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
    """Valida requisitos de segurança de senha (mínimo 8 caracteres, maiúscula, minúscula, número, especial)."""
    errors = []
    if len(password) < 8:
        errors.append("A senha deve ter no mínimo 8 caracteres.")
    if not re.search(r"[A-Z]", password):
        errors.append("A senha deve conter ao menos uma letra maiúscula.")
    if not re.search(r"[a-z]", password):
        errors.append("A senha deve conter ao menos uma letra minúscula.")
    if not re.search(r"\d", password):
        errors.append("A senha deve conter ao menos um número.")
    if not re.search(r"[^A-Za-z0-9]", password):
        errors.append("A senha deve conter ao menos um caractere especial.")
    return len(errors) == 0, errors

# Hash dummy pré-computado compatível com Argon2id para proteção contra timing attacks (OWASP)
# Impede enumeração de CPFs medindo a latência da resposta (~50ms constante)
DUMMY_ARGON2_HASH = (
    "argon2$argon2id$v=19$m=102400,t=2,p=8$dXVpZGR1bW15c2FsdA$2q5L2+J54q7+O52+K52+K52+K52+K52+K52+K52+K54"
)

class AccountService:
    @staticmethod
    def register_citizen(data: Dict[str, Any]) -> Dict[str, Any]:
        cpf = data.get("cpf", "")
        if not validate_cpf(cpf):
            raise ProblemDetailsException(
                detail="O CPF informado é inválido.",
                title="CPF inválido",
                status_code=400,
                errors=[{"field": "cpf", "message": "O CPF informado é inválido."}],
            )

        if citizen_repository.get_by_cpf(cpf):
            raise ProblemDetailsException(
                detail="Já existe uma conta cadastrada com este CPF.",
                title="CPF já cadastrado",
                status_code=409,
                errors=[{"field": "cpf", "message": "Já existe uma conta cadastrada com este CPF."}],
            )

        birth_date = data.get("birthDate", "")
        valid_birth, birth_msg = validate_birth_date(birth_date)
        if not valid_birth:
            raise ProblemDetailsException(
                detail=birth_msg,
                title="Data de nascimento inválida",
                status_code=400,
                errors=[{"field": "birthDate", "message": birth_msg}],
            )

        password = data.get("password", "")
        valid_pwd, pwd_errors = validate_password_strength(password)
        if not valid_pwd:
            raise ProblemDetailsException(
                detail="A senha não cumpre os requisitos mínimos de segurança.",
                title="Senha fraca",
                status_code=400,
                errors=[{"field": "password", "message": err} for err in pwd_errors],
            )

        # Hash Argon2id
        hashed_password = make_password(password)

        clean_cpf = "".join(filter(str.isdigit, cpf))
        gender_code = data.get("gender", "").strip()
        gender_desc = data.get("genderDescription", "").strip() if gender_code == "O" else ""
        citizen_data = {
            "fullName": data.get("fullName", "").strip(),
            "cpf": clean_cpf,
            "socialName": data.get("socialName", "").strip(),
            "birthDate": birth_date,
            "gender": gender_code,
            "genderDescription": gender_desc[:120],
            "motherName": data.get("motherName", "").strip(),
            "rg": data.get("rg", "").strip(),
            "rgIssuer": data.get("rgIssuer", "").strip(),
            "email": data.get("email", "").strip().lower(),
            "phone": data.get("phone", "").strip(),
            "passwordHash": hashed_password,
            "isPcd": bool(data.get("isPcd", False)),
            "pcdDetails": data.get("pcdDetails", "").strip(),
            "zipCode": data.get("zipCode", "").strip(),
            "street": data.get("street", "").strip(),
            "number": data.get("number", "").strip(),
            "complement": data.get("complement", "").strip(),
            "neighborhood": data.get("neighborhood", "").strip(),
            "city": data.get("city", "").strip(),
            "state": data.get("state", "").strip(),
            "role": "citizen",
            "isActive": True,
            "createdAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

        created = citizen_repository.save(citizen_data)
        # Retorna sem hash de senha
        safe_copy = dict(created)
        safe_copy.pop("passwordHash", None)
        return safe_copy

    @staticmethod
    def login_citizen(cpf: str, password: str) -> Dict[str, Any]:
        clean_cpf = "".join(filter(str.isdigit, cpf))

        # Verifica bloqueio temporário (RN-29)
        is_locked, remaining = citizen_repository.is_locked_out(clean_cpf)
        if is_locked:
            minutes = (remaining // 60) + 1
            raise ProblemDetailsException(
                detail=f"Conta temporariamente bloqueada por excesso de tentativas. Tente novamente em {minutes} minuto(s).",
                title="Acesso Bloqueado Temporariamente",
                status_code=429,
            )

        citizen = citizen_repository.get_by_cpf_for_auth(clean_cpf)

        # Mitigação contra Timing Attack (executa Argon2id mesmo quando CPF não existe)
        target_hash = citizen.get("passwordHash") if citizen else DUMMY_ARGON2_HASH
        pwd_valid = False
        try:
            pwd_valid = check_password(password, target_hash)
        except Exception:
            pwd_valid = False

        if not citizen or not pwd_valid:
            attempts = citizen_repository.record_failed_attempt(clean_cpf)
            if attempts >= 5:
                raise ProblemDetailsException(
                    detail="Número máximo de tentativas atingido. Acesso bloqueado por 5 minutos.",
                    title="Acesso Bloqueado Temporariamente",
                    status_code=429,
                )
            raise ProblemDetailsException(
                detail="CPF ou senha inválidos.",
                title="Credenciais Inválidas",
                status_code=401,
            )

        # Validação de status ativo (RN-40)
        if not citizen.get("isActive", True):
            raise ProblemDetailsException(
                detail="Conta de cidadão desativada ou excluída.",
                title="Conta Inativa",
                status_code=403,
            )

        # Login bem sucedido -> reseta contador
        citizen_repository.reset_failed_attempts(clean_cpf)

        must_change_pwd = bool(citizen.get("mustChangePassword", False))
        token = generate_sosp_token(
            user_id=citizen["id"],
            role=citizen.get("role", "citizen"),
            agency_id=citizen.get("agencyId"),
            cpf=clean_cpf,
            full_name=citizen.get("fullName", ""),
            email=citizen.get("email", ""),
            unit_id=citizen.get("unitId"),
            must_change_password=must_change_pwd,
        )

        # Registra sessão no servidor (accountsSession / RN-28)
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        raw_role = citizen.get("role", "citizen")
        subject_type = "citizen" if raw_role in ("citizen", "cidadao") else "internal"
        try:
            citizen_repository.create_session(
                subject_type=subject_type,
                subject_id=citizen["id"],
                token_hash=token_hash,
                role=raw_role,
                agency_id=citizen.get("agencyId"),
            )
        except Exception as e:
            if getattr(settings, "REPOSITORY_BACKEND", "memory") == "orm":
                logger.error("Falha ao registrar sessão no servidor (Fail-Closed): %s", e)
                raise ProblemDetailsException(
                    detail="Falha ao registrar sessão no servidor.",
                    status_code=500,
                    title="Erro de Persistência de Sessão",
                )
            logger.debug("Falha ao criar sessão em repositório não-ORM: %s", e)

        return {
            "token": token,
            "tokenType": "Bearer",
            "expiresIn": 1800,  # 30 minutos de inatividade (RN-28)
            "citizen": {
                "id": citizen["id"],
                "fullName": citizen["fullName"],
                "cpf": citizen["cpf"],
                "email": citizen["email"],
                "role": citizen.get("role", "citizen"),
                "agencyId": citizen.get("agencyId"),
                "unitId": citizen.get("unitId"),
                "mustChangePassword": must_change_pwd,
            },
        }

    @staticmethod
    def request_password_recovery(cpf: str) -> Dict[str, str]:
        clean_cpf = "".join(filter(str.isdigit, cpf))
        citizen = citizen_repository.get_by_cpf_for_auth(clean_cpf)
        if not citizen:
            # Retorna sucesso neutro para não expor existência de usuário (OWASP)
            return {"message": "Se o CPF estiver cadastrado, um código de verificação será enviado por e-mail."}

        # Gera código aleatório criptograficamente seguro de 6 dígitos
        code = f"{secrets.randbelow(900000) + 100000}"
        citizen_repository.set_recovery_code(clean_cpf, code)

        res: Dict[str, str] = {
            "message": "Código de verificação enviado por e-mail com sucesso."
        }
        django_env = getattr(settings, "DJANGO_ENV", "development").lower()
        is_test_or_dev = getattr(settings, "DEBUG", False) or getattr(settings, "TESTING", False) or django_env in ("development", "test")
        if is_test_or_dev and django_env not in ("staging", "production"):
            res["codeSimulated"] = code
        return res

    @staticmethod
    def reset_password(cpf: str, code: str, new_password: str) -> Dict[str, str]:
        clean_cpf = "".join(filter(str.isdigit, cpf))
        citizen = citizen_repository.get_by_cpf_for_auth(clean_cpf)
        if not citizen:
            raise ProblemDetailsException(detail="CPF não encontrado.", status_code=404)

        if not citizen_repository.verify_recovery_code(clean_cpf, code):
            raise ProblemDetailsException(
                detail="Código de verificação inválido ou expirado.",
                title="Código Inválido",
                status_code=400,
            )

        valid_pwd, pwd_errors = validate_password_strength(new_password)
        if not valid_pwd:
            raise ProblemDetailsException(
                detail="A nova senha não atende aos requisitos mínimos.",
                status_code=400,
                errors=[{"field": "newPassword", "message": err} for err in pwd_errors],
            )

        new_password_hash = make_password(new_password)
        updated = citizen_repository.update_password(clean_cpf, new_password_hash, code=code)
        if not updated:
            raise ProblemDetailsException(
                detail="Código de verificação inválido ou expirado.",
                title="Código Inválido",
                status_code=400,
            )
        citizen_repository.clear_recovery_code(clean_cpf)
        # Revoga todas as sessões ativas no servidor (proteção de redefinição de credencial)
        citizen_repository.revoke_all_sessions(citizen["id"], role=citizen.get("role"))
        return {"message": "Senha redefinida com sucesso."}

    @staticmethod
    def logout_citizen(token: str) -> Dict[str, str]:
        """Revoga a sessão ativamente no servidor (accountsSession)."""
        if token:
            token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
            citizen_repository.revoke_session(token_hash)
        return {"message": "Sessão encerrada e revogada no servidor com sucesso."}

    @staticmethod
    def change_password(user, current_password: str, new_password: str, confirm_password: Optional[str] = None) -> Dict[str, Any]:
        """
        Altera a senha de usuário autenticado (institucional ou cidadão).
        Obrigatório no primeiro acesso de usuários com mustChangePassword = True.
        Valida a credencial atual, requisitos de complexidade, impede reuso da mesma senha,
        persiste o hash Argon2id, remove mustChangePassword, revoga sessões anteriores
        e emite novo token seguro com sessão válida.
        """
        if not user or not getattr(user, "is_authenticated", False):
            raise ProblemDetailsException(
                detail="Usuário não autenticado.",
                title="Acesso Negado",
                status_code=401,
            )

        if not current_password:
            raise ProblemDetailsException(
                detail="A senha atual é obrigatória.",
                title="Dado Obrigatório",
                status_code=400,
                errors=[{"field": "currentPassword", "message": "A senha atual é obrigatória."}],
            )

        if not new_password:
            raise ProblemDetailsException(
                detail="A nova senha é obrigatória.",
                title="Dado Obrigatório",
                status_code=400,
                errors=[{"field": "newPassword", "message": "A nova senha é obrigatória."}],
            )

        if confirm_password and new_password != confirm_password:
            raise ProblemDetailsException(
                detail="A confirmação de senha não coincide com a nova senha.",
                title="Senhas Divergentes",
                status_code=400,
                errors=[{"field": "confirmPassword", "message": "A confirmação de senha não coincide com a nova senha."}],
            )

        if current_password == new_password:
            raise ProblemDetailsException(
                detail="A nova senha deve ser diferente da senha atual.",
                title="Senha Repetida",
                status_code=400,
                errors=[{"field": "newPassword", "message": "A nova senha deve ser diferente da senha atual."}],
            )

        valid_pwd, pwd_errors = validate_password_strength(new_password)
        if not valid_pwd:
            raise ProblemDetailsException(
                detail="A nova senha não cumpre os requisitos mínimos de segurança.",
                title="Senha Fraca",
                status_code=400,
                errors=[{"field": "newPassword", "message": err} for err in pwd_errors],
            )

        user_id = str(user.id)
        role = getattr(user, "role", "citizen")
        is_internal = role not in ("citizen", "cidadao")
        new_hash = make_password(new_password)

        with transaction.atomic():
            if is_internal:
                from .models import InternalUser
                internal_user = InternalUser.objects.select_for_update().filter(id=user_id, is_active=True, deleted_at__isnull=True).first()
                if not internal_user:
                    raise ProblemDetailsException(detail="Usuário institucional não encontrado.", status_code=404)
                if not check_password(current_password, internal_user.password_hash):
                    raise ProblemDetailsException(
                        detail="A senha atual informada está incorreta.",
                        title="Credencial Inválida",
                        status_code=400,
                        errors=[{"field": "currentPassword", "message": "A senha atual informada está incorreta."}],
                    )
                internal_user.password_hash = new_hash
                internal_user.must_change_password = False
                internal_user.save(update_fields=["password_hash", "must_change_password", "updated_at"])
                citizen_repository.revoke_all_sessions(user_id, role="internal")
            else:
                from .models import Citizen
                citizen_user = Citizen.objects.select_for_update().filter(id=user_id, is_active=True, deleted_at__isnull=True).first()
                if not citizen_user:
                    raise ProblemDetailsException(detail="Cidadão não encontrado.", status_code=404)
                if not check_password(current_password, citizen_user.password_hash):
                    raise ProblemDetailsException(
                        detail="A senha atual informada está incorreta.",
                        title="Credencial Inválida",
                        status_code=400,
                        errors=[{"field": "currentPassword", "message": "A senha atual informada está incorreta."}],
                    )
                citizen_user.password_hash = new_hash
                citizen_user.save(update_fields=["password_hash", "updated_at"])
                citizen_repository.revoke_all_sessions(user_id, role="citizen")

            # Emite novo token com must_change_password=False
            new_token = generate_sosp_token(
                user_id=user_id,
                role=role,
                agency_id=getattr(user, "agency_id", None),
                cpf=getattr(user, "cpf", ""),
                full_name=getattr(user, "full_name", ""),
                email=getattr(user, "email", ""),
                unit_id=getattr(user, "unit_id", None),
                must_change_password=False,
            )

            # Registra a nova sessão ativa
            token_hash = hashlib.sha256(new_token.encode("utf-8")).hexdigest()
            subject_type = "citizen" if not is_internal else "internal"
            try:
                citizen_repository.create_session(
                    subject_type=subject_type,
                    subject_id=user_id,
                    token_hash=token_hash,
                    role=role,
                    agency_id=getattr(user, "agency_id", None),
                )
            except Exception as e:
                logger.warning("Falha ao registrar nova sessão após troca de senha: %s", e)

        return {
            "message": "Senha alterada com sucesso.",
            "token": new_token,
            "mustChangePassword": False,
        }

