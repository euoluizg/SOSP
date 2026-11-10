import os
import secrets
import string
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.hashers import make_password
from apps.accounts.models import InternalUser
from apps.catalog.models import Agency, Unit


def _mask_cpf(cpf: str) -> str:
    clean = "".join(filter(str.isdigit, cpf))
    if len(clean) == 11:
        return f"{clean[:3]}.***.***-{clean[-2:]}"
    return "***"


def _generate_secure_password(length: int = 16) -> str:
    """Gera uma senha segura com maiúsculas, minúsculas, dígitos e símbolos especiais."""
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special = "!@#$%^&*"
    chars = uppercase + lowercase + digits + special

    password = [
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(digits),
        secrets.choice(special),
    ]
    password += [secrets.choice(chars) for _ in range(length - 4)]
    secrets.SystemRandom().shuffle(password)
    return "".join(password)


class Command(BaseCommand):
    help = (
        "Provisiona com estrita idempotência as contas homologatórias institucionais do SOSP "
        "(Admin SOSP Geral e João Servidor Central) com política de troca obrigatória de senha no primeiro acesso."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--admin-password",
            type=str,
            default=None,
            help="Senha temporária para o Admin SOSP Geral (se omitida, gera senha aleatória segura).",
        )
        parser.add_argument(
            "--server-password",
            type=str,
            default=None,
            help="Senha temporária para João Servidor Central (se omitida, gera senha aleatória segura).",
        )
        parser.add_argument(
            "--show-generated-passwords",
            action="store_true",
            help="Exibe as senhas geradas apenas em console local/manual. Nunca utilize em CI/CD público.",
        )

    def handle(self, *args, **options):
        self.stdout.write("=================================================================")
        self.stdout.write("SOSP — Provisionamento de Usuários de Homologação Institucional")
        self.stdout.write("=================================================================")

        # 1. Garante Órgão SSP (Secretaria de Segurança Pública)
        agency_ssp = Agency.objects.filter(acronym="SSP", is_active=True).first()
        if not agency_ssp:
            agency_ssp = Agency.objects.create(
                name="Secretaria de Segurança Pública",
                acronym="SSP",
                sphere="state",
                description="Órgão responsável pela segurança pública e serviços de identificação civil em Alagoas.",
                is_active=True,
            )
            self.stdout.write(self.style.SUCCESS(f"✓ Órgão SSP criado: {agency_ssp.id}"))
        else:
            self.stdout.write(f"✓ Órgão SSP existente confirmado: {agency_ssp.id}")

        # 2. Garante Unidade Central Já! Centro vinculada à SSP
        unit_central = Unit.objects.filter(agency=agency_ssp, name__icontains="Central", is_active=True).first()
        if not unit_central:
            unit_central = Unit.objects.create(
                agency=agency_ssp,
                name="Central Já! Centro",
                zip_code="57020100",
                street="Rua do Sol",
                neighborhood="Centro",
                city="Maceió",
                state="AL",
                address_number="123",
                daily_limit=40,
                is_accessible=True,
                has_priority_service=True,
                is_active=True,
            )
            self.stdout.write(self.style.SUCCESS(f"✓ Unidade Central Já! Centro criada: {unit_central.id}"))
        else:
            self.stdout.write(f"✓ Unidade Central Já! Centro confirmada: {unit_central.id}")

        # 3. Resolve senhas temporárias (Argon2id)
        admin_pwd = options.get("admin_password") or os.environ.get("HOMOLOG_ADMIN_PASSWORD")
        admin_pwd_generated = False
        if not admin_pwd:
            admin_pwd = _generate_secure_password(16)
            admin_pwd_generated = True

        server_pwd = options.get("server_password") or os.environ.get("HOMOLOG_SERVER_PASSWORD")
        server_pwd_generated = False
        if not server_pwd:
            server_pwd = _generate_secure_password(16)
            server_pwd_generated = True

        admin_hash = make_password(admin_pwd)
        server_hash = make_password(server_pwd)

        # 4. Provisiona Conta 1: Admin SOSP Geral
        admin_user, admin_created = InternalUser.objects.update_or_create(
            cpf="99988877714",
            defaults={
                "full_name": "Admin SOSP Geral",
                "email": "admin@sosp.al.gov.br",
                "registration_number": "ADM-0001",
                "role": "superadmin",
                "agency_id": None,
                "unit_id": None,
                "can_manage_catalog": True,
                "password_hash": admin_hash,
                "must_change_password": True,
                "is_active": True,
                "deleted_at": None,
            },
        )
        status_admin = "CRIADO" if admin_created else "ATUALIZADO"
        self.stdout.write(
            self.style.SUCCESS(
                f"✓ [{status_admin}] Admin SOSP Geral:\n"
                f"   - CPF: {_mask_cpf(admin_user.cpf)}\n"
                f"   - Matrícula: {admin_user.registration_number}\n"
                f"   - Papel: {admin_user.role}\n"
                f"   - Troca obrigatória de senha (mustChangePassword): {admin_user.must_change_password}\n"
                f"   - Painel inicial de acesso: /admin/orgaos"
            )
        )

        # 5. Provisiona Conta 2: João Servidor Central
        server_user, server_created = InternalUser.objects.update_or_create(
            cpf="33366699957",
            defaults={
                "full_name": "João Servidor Central",
                "email": "joao.servidor@ssp.al.gov.br",
                "registration_number": "SSP-1001",
                "role": "server",
                "agency_id": agency_ssp.id,
                "unit_id": unit_central.id,
                "can_manage_catalog": False,
                "password_hash": server_hash,
                "must_change_password": True,
                "is_active": True,
                "deleted_at": None,
            },
        )
        status_server = "CRIADO" if server_created else "ATUALIZADO"
        self.stdout.write(
            self.style.SUCCESS(
                f"✓ [{status_server}] João Servidor Central:\n"
                f"   - CPF: {_mask_cpf(server_user.cpf)}\n"
                f"   - Matrícula: {server_user.registration_number}\n"
                f"   - Papel: {server_user.role}\n"
                f"   - Órgão: {agency_ssp.acronym} ({agency_ssp.id})\n"
                f"   - Unidade: {unit_central.name} ({unit_central.id})\n"
                f"   - Troca obrigatória de senha (mustChangePassword): {server_user.must_change_password}\n"
                f"   - Painel inicial de acesso: /servidor/painel"
            )
        )

        self.stdout.write("-----------------------------------------------------------------")
        self.stdout.write(
            "✓ Ambas as contas foram configuradas com hash Argon2id e `must_change_password = True`.\n"
            "✓ No primeiro acesso institucional, o sistema exigirá a definição de uma nova credencial permanente."
        )

        if options.get("show_generated_passwords"):
            self.stdout.write(self.style.WARNING("ATENÇÃO: EXIBIÇÃO DE CREDENCIAIS TEMPORÁRIAS SOLICITADA:"))
            if admin_pwd_generated:
                self.stdout.write(f"   [Admin]: {admin_pwd}")
            if server_pwd_generated:
                self.stdout.write(f"   [Servidor]: {server_pwd}")
        else:
            self.stdout.write(
                "✓ Credenciais temporárias protegidas (zero texto puro em logs públicos).\n"
                "  Use as flags `--admin-password` e `--server-password` para definir senhas conhecidas no staging."
            )
        self.stdout.write("=================================================================")
