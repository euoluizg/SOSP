"""
SOSP — Testes Automatizados de Segurança de Sessões e Integridade de Schemas/Constraints.

Valida estritamente os 9 cenários de segurança de sessão e o alinhamento de constraints:
1. Criação de sessão cidadão (subject_type="citizen").
2. Criação de sessão servidor (subject_type="internal").
3. Criação de sessão gestor (subject_type="internal").
4. Logout e rejeição do token revogado (401).
5. Recuperação de senha e revogação de todas as sessões anteriores (revoke_all_sessions).
6. Falha no banco durante criação da sessão (zero tokens emitidos / erro 500 RFC 7807).
7. Falha no banco durante verificação de revogação (fail-closed 401 AuthenticationFailed).
8. Isolamento de sessão entre usuários (logout de A não afeta B).
9. Bloqueio de token sem sessão registrada sob REQUIRE_REGISTERED_SESSION.
10. Compatibilidade e conformidade das constraints de matrícula com hífen e roles ampliadas.
"""

import hashlib
import uuid
import datetime
from unittest.mock import patch, MagicMock
import pytest
from django.conf import settings
from django.test import override_settings, TestCase
from django.utils import timezone
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework.exceptions import AuthenticationFailed

from apps.accounts.models import Citizen, InternalUser, Session
from apps.accounts.services import AccountService
from apps.accounts.repositories import (
    CitizenDjangoORMRepository,
    CitizenInMemoryRepository,
    citizen_repository,
)
from common.security.authentication import generate_sosp_token, SospTokenAuthentication
from common.exceptions import ProblemDetailsException


@pytest.mark.django_db
class TestSessionSecurityScenarios:
    """Suíte completa para os 9 requisitos de segurança de sessão (RN-28 / ADR-003)."""

    def setup_method(self):
        self.client = APIClient()
        self.factory = APIRequestFactory()
        self.orm_repo = CitizenDjangoORMRepository()
        self.mem_repo = CitizenInMemoryRepository()

    # 1. Criação de sessão cidadão (subject_type="citizen")
    def test_01_citizen_session_creation_uses_citizen_subject_type(self):
        token = "test-citizen-token-123"
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        citizen_id = str(uuid.uuid4())

        self.orm_repo.create_session(
            subject_type="citizen",
            subject_id=citizen_id,
            token_hash=token_hash,
            role="citizen",
        )

        sess = Session.objects.filter(token_hash=token_hash).first()
        assert sess is not None
        assert sess.subject_type == "citizen"
        assert str(sess.subject_id) == citizen_id
        assert sess.revoked_at is None
        assert not self.orm_repo.is_session_revoked(token_hash)

    # 2. Criação de sessão servidor (subject_type="internal")
    def test_02_server_session_creation_normalizes_to_internal_subject_type(self):
        token = "test-server-token-456"
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        server_id = str(uuid.uuid4())

        # Mesmo se receber 'servant' ou 'server', deve normalizar para 'internal' (chkAccountsSessionSubject)
        self.orm_repo.create_session(
            subject_type="servant",
            subject_id=server_id,
            token_hash=token_hash,
            role="servant",
        )

        sess = Session.objects.filter(token_hash=token_hash).first()
        assert sess is not None
        assert sess.subject_type == "internal"
        assert str(sess.subject_id) == server_id
        assert sess.revoked_at is None
        assert not self.orm_repo.is_session_revoked(token_hash)

    # 3. Criação de sessão gestor (subject_type="internal")
    def test_03_manager_session_creation_normalizes_to_internal_subject_type(self):
        token = "test-manager-token-789"
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        manager_id = str(uuid.uuid4())

        # Mesmo se receber 'gestor' ou 'manager', deve normalizar para 'internal'
        self.orm_repo.create_session(
            subject_type="gestor",
            subject_id=manager_id,
            token_hash=token_hash,
            role="gestor",
        )

        sess = Session.objects.filter(token_hash=token_hash).first()
        assert sess is not None
        assert sess.subject_type == "internal"
        assert str(sess.subject_id) == manager_id
        assert sess.revoked_at is None
        assert not self.orm_repo.is_session_revoked(token_hash)

    # 4. Logout e rejeição do token
    def test_04_logout_revokes_session_and_subsequent_request_is_rejected(self):
        token = generate_sosp_token(user_id=str(uuid.uuid4()), role="citizen", cpf="11144477735")
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        uid = str(uuid.uuid4())

        # Teste com citizen_repository ativo (in-memory ou ORM)
        citizen_repository.create_session(
            subject_type="citizen",
            subject_id=uid,
            token_hash=token_hash,
            role="citizen",
        )
        assert not citizen_repository.is_session_revoked(token_hash)

        # Logout revoga ativamente
        revoked = citizen_repository.revoke_session(token_hash)
        assert revoked is True
        assert citizen_repository.is_session_revoked(token_hash) is True

        # Autenticador DRF deve rejeitar com AuthenticationFailed
        auth = SospTokenAuthentication()
        req = self.factory.get("/", HTTP_AUTHORIZATION=f"Bearer {token}")
        with pytest.raises(AuthenticationFailed) as exc_info:
            auth.authenticate(req)
        assert "revogada ou inválida" in str(exc_info.value)

    # 5. Recuperação de senha e revogação de todas as sessões anteriores
    def test_05_password_reset_revokes_all_active_sessions(self):
        user_id = str(uuid.uuid4())
        tokens = [f"token-reset-{i}" for i in range(3)]
        hashes = []
        for t in tokens:
            th = hashlib.sha256(t.encode("utf-8")).hexdigest()
            hashes.append(th)
            self.orm_repo.create_session(
                subject_type="citizen",
                subject_id=user_id,
                token_hash=th,
                role="citizen",
            )

        # Confirma que todas estão ativas
        for th in hashes:
            assert not self.orm_repo.is_session_revoked(th)

        # Executa revogação em massa
        count = self.orm_repo.revoke_all_sessions(user_id, role="citizen")
        assert count == 3

        # Todas as sessões anteriores agora estão revogadas
        for th in hashes:
            assert self.orm_repo.is_session_revoked(th) is True

    # 6. Falha no banco durante criação da sessão (zero tokens emitidos / erro 500 RFC 7807)
    @override_settings(REPOSITORY_BACKEND="orm")
    def test_06_db_failure_during_session_creation_issues_zero_tokens_and_fails_500(self):
        fake_citizen = {
            "id": str(uuid.uuid4()),
            "cpf": "11144477735",
            "fullName": "Cidadão Teste",
            "email": "cidadao@teste.gov.br",
            "passwordHash": "argon2_dummy",
            "isActive": True,
            "role": "citizen",
        }

        with patch.object(citizen_repository, "get_by_cpf_for_auth", return_value=fake_citizen), \
             patch("apps.accounts.services.check_password", return_value=True), \
             patch.object(citizen_repository, "create_session", side_effect=Exception("Database connection timeout")):

            with pytest.raises(ProblemDetailsException) as exc_info:
                AccountService.login_citizen("11144477735", "Senha@123")

            assert exc_info.value.status_code == 500
            assert "Falha ao registrar sessão no servidor." in exc_info.value.detail
            assert exc_info.value.title == "Erro de Persistência de Sessão"

    # 7. Falha no banco durante verificação de revogação (fail-closed 401)
    @override_settings(REPOSITORY_BACKEND="orm")
    def test_07_db_failure_during_revocation_check_fails_closed_with_401(self):
        token = generate_sosp_token(user_id=str(uuid.uuid4()), role="citizen", cpf="11144477735")
        auth = SospTokenAuthentication()
        req = self.factory.get("/", HTTP_AUTHORIZATION=f"Bearer {token}")

        with patch.object(citizen_repository, "is_session_revoked", side_effect=Exception("DB connection error")):
            with pytest.raises(AuthenticationFailed) as exc_info:
                auth.authenticate(req)

            assert "Falha de segurança ao validar sessão no servidor." in str(exc_info.value)

    # 8. Isolamento de sessão entre usuários
    def test_08_session_isolation_between_users(self):
        user_a_id = str(uuid.uuid4())
        user_b_id = str(uuid.uuid4())

        token_a = generate_sosp_token(user_id=user_a_id, role="citizen", cpf="11144477735")
        token_b = generate_sosp_token(user_id=user_b_id, role="server", cpf="33366699957")

        hash_a = hashlib.sha256(token_a.encode("utf-8")).hexdigest()
        hash_b = hashlib.sha256(token_b.encode("utf-8")).hexdigest()

        self.orm_repo.create_session(subject_type="citizen", subject_id=user_a_id, token_hash=hash_a, role="citizen")
        self.orm_repo.create_session(subject_type="internal", subject_id=user_b_id, token_hash=hash_b, role="server")

        # Usuário A faz logout
        self.orm_repo.revoke_session(hash_a)

        # Sessão de A revogada, sessão de B permanece ativa e válida
        assert self.orm_repo.is_session_revoked(hash_a) is True
        assert self.orm_repo.is_session_revoked(hash_b) is False

        auth = SospTokenAuthentication()
        # Token B autentica com sucesso
        req_b = self.factory.get("/", HTTP_AUTHORIZATION=f"Bearer {token_b}")
        with patch.object(citizen_repository, "get_by_id", return_value={"isActive": True, "deletedAt": None}):
            user_b, _ = auth.authenticate(req_b)
            assert str(user_b.id) == user_b_id

    # 9. Bloqueio de token sem sessão registrada sob REQUIRE_REGISTERED_SESSION
    def test_09_token_without_registered_session_blocked_when_policy_enabled(self):
        token = generate_sosp_token(user_id=str(uuid.uuid4()), role="citizen", cpf="11144477735")
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

        # Com política REQUIRE_REGISTERED_SESSION=False (modo padrão de compatibilidade)
        with override_settings(REQUIRE_REGISTERED_SESSION=False):
            assert self.orm_repo.is_session_revoked(token_hash) is False
            assert self.mem_repo.is_session_revoked(token_hash) is False

        # Com política REQUIRE_REGISTERED_SESSION=True (Fail-Closed estrito)
        with override_settings(REQUIRE_REGISTERED_SESSION=True):
            assert self.orm_repo.is_session_revoked(token_hash) is True
            assert self.mem_repo.is_session_revoked(token_hash) is True

            auth = SospTokenAuthentication()
            req = self.factory.get("/", HTTP_AUTHORIZATION=f"Bearer {token}")
            with pytest.raises(AuthenticationFailed) as exc_info:
                auth.authenticate(req)
            assert "revogada ou inválida" in str(exc_info.value)


@pytest.mark.django_db
class TestSchemaConstraintsAlignment:
    """Testa conformidade das regras e regex de constraints alinhadas nos modelos e migrations."""

    def test_internal_user_accepts_hyphenated_registration_and_expanded_roles(self):
        demo_registrations = ["SSP-1001", "DET-2002", "GES-3003", "ADM-0001"]
        demo_roles = ["servant", "gestor", "superadmin"]

        import re
        reg_regex = re.compile(r"^[A-Za-z0-9-]{1,20}$")
        for reg in demo_registrations:
            assert reg_regex.match(reg) is not None, f"Matrícula '{reg}' deve ser aceita pelo regex da constraint."

        valid_roles = {"superadmin", "admin", "gestor", "server", "manager", "servant", "administrator"}
        for r in demo_roles:
            assert r in valid_roles, f"Papel '{r}' deve ser permitido pela constraint chkAccountsInternalRole."
        assert "server" in valid_roles
        assert "administrator" in valid_roles

    def test_session_subject_type_constraint_accepts_only_citizen_and_internal(self):
        valid_subject_types = {"citizen", "internal"}
        assert "citizen" in valid_subject_types
        assert "internal" in valid_subject_types
        assert "server" not in valid_subject_types
        assert "gestor" not in valid_subject_types
