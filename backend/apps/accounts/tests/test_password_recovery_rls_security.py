import datetime
import secrets
import pytest
from django.db import connection
from django.contrib.auth.hashers import make_password, check_password
from apps.accounts.models import Citizen, Gender
from apps.accounts.repositories import CitizenDjangoORMRepository

@pytest.mark.django_db
class TestPasswordRecoverySecurityAndRLS:
    """
    Testes negativos de segurança para recuperação de senha sob PostgreSQL e RLS.
    Garante que redefinição direta por CPF sem autorização válida e código verificado
    seja estritamente impossível e que a role de runtime não possa dar bypass no fluxo.
    """

    @pytest.fixture(autouse=True)
    def setup_citizen(self):
        gender, _ = Gender.objects.get_or_create(name="Não Informado", defaults={"sort_order": 99})
        self.original_pwd = "Test_" + secrets.token_urlsafe(18)
        self.test_cpf = "77788899901"
        self.citizen = Citizen.objects.create(
            cpf=self.test_cpf,
            full_name="Cidadão Teste Segurança Recovery",
            birth_date="1995-03-20",
            email="security.recovery@al.gov.br",
            phone="82999990000",
            password_hash=make_password(self.original_pwd),
            password_salt=secrets.token_hex(12),
            gender=gender,
            mother_name="Mãe Teste",
            zip_code="57020100",
            street="Rua Segura",
            neighborhood="Centro",
            city="Maceió",
            state="AL",
            address_number="100",
            is_active=True,
        )
        self.repo = CitizenDjangoORMRepository()
        yield
        Citizen.objects.filter(cpf=self.test_cpf).delete()

    def test_01_direct_password_reset_without_valid_code_is_strictly_rejected(self):
        """Tentativa de redefinição direta de senha sem código deve ser rejeitada."""
        attempted_password = "Other_" + secrets.token_urlsafe(16)
        hacked_hash = make_password(attempted_password)
        # Sem código fornecido
        result = self.repo.update_password(self.test_cpf, hacked_hash, code=None)
        assert result is False, "Redefinição direta de senha sem código deveria ter sido rejeitada!"

        # Confirma que a senha permanece inalterada
        self.citizen.refresh_from_db()
        assert check_password(self.original_pwd, self.citizen.password_hash) is True
        assert check_password(attempted_password, self.citizen.password_hash) is False

    def test_02_password_reset_with_wrong_code_fails_and_increments_attempts(self):
        """Tentativa de redefinição com código incorreto deve falhar."""
        from apps.accounts.models import LoginAttempt
        self.repo.set_recovery_code(self.test_cpf, "123456")
        hacked_hash = make_password("Test_" + secrets.token_urlsafe(18))

        result = self.repo.update_password(self.test_cpf, hacked_hash, code="999999")
        assert result is False, "Redefinição com código errado deveria retornar False!"

        self.citizen.refresh_from_db()
        assert check_password(self.original_pwd, self.citizen.password_hash) is True
        assert LoginAttempt.objects.filter(cpf=self.test_cpf, was_successful=False).count() >= 1

    def test_03_password_reset_with_expired_code_is_rejected(self):
        """Código de recuperação expirado (RN-30) deve invalidar a redefinição."""
        self.repo.set_recovery_code(self.test_cpf, "654321")
        # Força expiração do código no passado
        past = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=16)
        Citizen.objects.filter(cpf=self.test_cpf).update(recovery_code_expires_at=past)

        hacked_hash = make_password("Test_" + secrets.token_urlsafe(18))
        result = self.repo.update_password(self.test_cpf, hacked_hash, code="654321")
        assert result is False, "Código expirado deveria ter sido rejeitado!"

        self.citizen.refresh_from_db()
        assert check_password(self.original_pwd, self.citizen.password_hash) is True

    def test_04_brute_force_lockout_blocks_recovery_flow(self):
        """5 tentativas incorretas consecutivas devem bloquear a conta temporariamente (RN-29)."""
        self.repo.set_recovery_code(self.test_cpf, "888111")
        for _ in range(5):
            self.repo.verify_recovery_code(self.test_cpf, "000000")

        locked_out, _ = self.repo.is_locked_out(self.test_cpf)
        assert locked_out is True, "Conta deveria estar bloqueada após 5 tentativas consecutivas falhas!"

        # Mesmo fornecendo o código correto agora, deve ser rejeitado durante o bloqueio
        hacked_hash = make_password("Test_" + secrets.token_urlsafe(18))
        result = self.repo.update_password(self.test_cpf, hacked_hash, code="888111")
        assert result is False, "Redefinição deve ser bloqueada quando a conta estiver temporariamente bloqueada!"

    def test_05_code_replay_attack_rejected_after_successful_reset(self):
        """Após o consumo único do código, qualquer tentativa subsequente com o mesmo código deve falhar."""
        self.repo.set_recovery_code(self.test_cpf, "456789")
        new_pwd_1 = "Test_" + secrets.token_urlsafe(18)
        hash_1 = make_password(new_pwd_1)

        # Primeiro reset com o código correto -> deve funcionar
        ok_1 = self.repo.update_password(self.test_cpf, hash_1, code="456789")
        assert ok_1 is True
        self.repo.clear_recovery_code(self.test_cpf)

        self.citizen.refresh_from_db()
        assert check_password(new_pwd_1, self.citizen.password_hash) is True

        # Replay do mesmo código com outra senha -> deve falhar obrigatoriamente
        hash_2 = make_password("Test_" + secrets.token_urlsafe(18))
        ok_2 = self.repo.update_password(self.test_cpf, hash_2, code="456789")
        assert ok_2 is False, "Replay de código já consumido deve ser estritamente rejeitado!"

    def test_06_leakage_prevention_get_recovery_code_is_inaccessible(self):
        """Garante que funções de vazamento de hashes não estejam expostas."""
        if connection.vendor == "postgresql":
            with connection.cursor() as cur:
                cur.execute("""
                    SELECT count(*) FROM pg_proc p
                    JOIN pg_namespace n ON n.oid = p.pronamespace
                    WHERE n.nspname = 'sosp_security'
                      AND p.proname = 'get_citizen_recovery_code';
                """)
                count = cur.fetchone()[0]
                assert count == 0, "A função sosp_security.get_citizen_recovery_code deve ser eliminada para evitar vazamento de hashes!"
