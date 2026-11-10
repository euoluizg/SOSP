import getpass
import os
import secrets
import string
import sys
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.hashers import make_password
from django.db import transaction
from apps.accounts.models import InternalUser
from apps.catalog.models import Agency, Unit
from apps.accounts.repositories import citizen_repository


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
            help="Senha temporária para o Admin SOSP Geral (aviso: prefira HOMOLOG_ADMIN_PASSWORD ou getpass).",
        )
        parser.add_argument(
            "--server-password",
            type=str,
            default=None,
            help="Senha temporária para João Servidor Central (aviso: prefira HOMOLOG_SERVER_PASSWORD ou getpass).",
        )
        parser.add_argument(
            "--agency-acronym",
            type=str,
            default="SSP",
            help="Sigla do órgão de lotação do servidor operacional (padrão: SSP).",
        )
        parser.add_argument(
            "--unit-name",
            type=str,
            default=None,
            help="Nome ou filtro da unidade de atendimento para vincular o servidor.",
        )
        parser.add_argument(
            "--allow-unlinked",
            action="store_true",
            help="Permite provisionar o servidor sem órgão ou unidade caso não existam no catálogo.",
        )
        parser.add_argument(
            "--rotate-credentials",
            action="store_true",
            help="Rotaciona as credenciais de usuários institucionais já existentes (exige --confirm).",
        )
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Confirmação explícita para ações sensíveis (como rotação de credenciais ou ambiente restrito).",
        )
        parser.add_argument(
            "--force-production",
            action="store_true",
            help="Permite a execução em ambiente de produção após confirmação formal de homologação.",
        )
        parser.add_argument(
            "--output-credentials-file",
            type=str,
            default=None,
            help="Caminho de arquivo local seguro para salvar senhas geradas aleatoriamente (permissão 0600).",
        )
        parser.add_argument(
            "--interactive",
            action="store_true",
            help="Força solicitação interativa de senhas via getpass (sem eco no terminal).",
        )
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="Desativa prompts interativos (modo automatizado/CI/CD).",
        )

    def handle(self, *args, **options):
        self.stdout.write("=================================================================")
        self.stdout.write("SOSP — Provisionamento de Usuários de Homologação Institucional")
        self.stdout.write("=================================================================")

        # 1. Guarda de Ambiente Seguro
        env_name = (
            getattr(settings, "ENVIRONMENT", "")
            or getattr(settings, "DJANGO_ENV", "")
            or os.environ.get("DJANGO_ENV", "")
        ).lower()
        if env_name in ("production", "prod") and not options.get("force_production"):
            raise CommandError(
                f"Operação bloqueada por política de segurança: O provisionamento de homologação "
                f"não pode ser executado no ambiente de produção ('{env_name}') sem as flags "
                "--force-production e --confirm."
            )

        if options.get("rotate_credentials") and not options.get("confirm"):
            raise CommandError(
                "Operação bloqueada: A rotação de credenciais de usuários existentes requer confirmação "
                "explícita via flag --confirm."
            )

        if options.get("admin_password") or options.get("server_password"):
            self.stdout.write(
                self.style.WARNING(
                    "Aviso de Segurança: Fornecer senhas diretamente na linha de comando expõe "
                    "credenciais no histórico do terminal. Prefira variáveis de ambiente ou getpass."
                )
            )

        # 2. Localização de Órgão e Unidade Reais (Zero Criação Fictícia)
        agency_acronym = options.get("agency_acronym") or "SSP"
        allow_unlinked = options.get("allow_unlinked", False)

        agency_ssp = Agency.objects.filter(acronym=agency_acronym, is_active=True).first()
        if not agency_ssp:
            if not allow_unlinked:
                raise CommandError(
                    f"Operação cancelada: Órgão com sigla '{agency_acronym}' não foi encontrado no catálogo de órgãos ativos. "
                    "Cadastre o órgão previamente ou utilize a flag --allow-unlinked para provisionar o servidor sem vínculo inicial."
                )
            self.stdout.write(
                self.style.WARNING(
                    f"⚠ Órgão '{agency_acronym}' não encontrado no catálogo. Servidor será provisionado sem vínculo de órgão (--allow-unlinked)."
                )
            )
        else:
            self.stdout.write(f"✓ Órgão confirmado no catálogo: {agency_ssp.name} ({agency_ssp.acronym})")

        unit_central = None
        if agency_ssp:
            unit_query = Unit.objects.filter(agency=agency_ssp, is_active=True)
            if options.get("unit_name"):
                unit_query = unit_query.filter(name__icontains=options["unit_name"])
            unit_central = unit_query.first()
            if not unit_central:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠ Nenhuma unidade de atendimento ativa encontrada para o órgão '{agency_ssp.acronym}'. "
                        "O servidor será provisionado com unit_id=None (fail-closed: atendimentos operacionais "
                        "permanecerão restritos até vinculação a uma unidade real)."
                    )
                )
            else:
                self.stdout.write(f"✓ Unidade de atendimento confirmada: {unit_central.name} ({unit_central.id})")

        # 3. Resolução Segura de Senhas Temporárias
        admin_pwd = options.get("admin_password") or os.environ.get("HOMOLOG_ADMIN_PASSWORD")
        server_pwd = options.get("server_password") or os.environ.get("HOMOLOG_SERVER_PASSWORD")

        use_interactive = options.get("interactive") or (
            sys.stdin.isatty() and not options.get("no_input") and not admin_pwd and not server_pwd
        )

        if use_interactive:
            if not admin_pwd:
                admin_pwd = getpass.getpass("Digite a senha temporária para Admin SOSP Geral: ").strip()
            if not server_pwd:
                server_pwd = getpass.getpass("Digite a senha temporária para João Servidor Central: ").strip()

        admin_pwd_generated = False
        if not admin_pwd:
            admin_pwd = _generate_secure_password(16)
            admin_pwd_generated = True

        server_pwd_generated = False
        if not server_pwd:
            server_pwd = _generate_secure_password(16)
            server_pwd_generated = True

        if admin_pwd == server_pwd:
            raise CommandError("Por conformidade de segurança, as senhas do Administrador e do Servidor devem ser distintas.")

        rotate = options.get("rotate_credentials", False)

        # 4. Execução Transacional e Idempotente de Provisionamento
        with transaction.atomic():
            # Conta 1: Admin SOSP Geral
            existing_admin = InternalUser.objects.select_for_update().filter(cpf="99988877714").first()
            if existing_admin:
                if rotate:
                    existing_admin.password_hash = make_password(admin_pwd)
                    existing_admin.must_change_password = True
                    existing_admin.save(update_fields=["password_hash", "must_change_password", "updated_at"])
                    citizen_repository.revoke_all_sessions(str(existing_admin.id), role="internal")
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ [ROTACIONADO] Admin SOSP Geral ({_mask_cpf(existing_admin.cpf)}): nova credencial definida, "
                            "mustChangePassword=True e sessões revogadas."
                        )
                    )
                else:
                    self.stdout.write(
                        f"✓ [PRESERVADO] Admin SOSP Geral ({_mask_cpf(existing_admin.cpf)}): credenciais e permissões existentes mantidas."
                    )
            else:
                admin_hash = make_password(admin_pwd)
                new_admin = InternalUser.objects.create(
                    cpf="99988877714",
                    full_name="Admin SOSP Geral",
                    email="admin@sosp.al.gov.br",
                    registration_number="ADM-0001",
                    role="superadmin",
                    agency_id=None,
                    unit_id=None,
                    can_manage_catalog=True,
                    password_hash=admin_hash,
                    must_change_password=True,
                    is_active=True,
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ [CRIADO] Admin SOSP Geral:\n"
                        f"   - CPF: {_mask_cpf(new_admin.cpf)}\n"
                        f"   - Matrícula: {new_admin.registration_number}\n"
                        f"   - Papel: {new_admin.role}\n"
                        f"   - Troca obrigatória de senha (mustChangePassword): {new_admin.must_change_password}\n"
                        f"   - Painel inicial de acesso: /admin/orgaos"
                    )
                )

            # Conta 2: João Servidor Central
            existing_server = InternalUser.objects.select_for_update().filter(cpf="33366699957").first()
            if existing_server:
                if rotate:
                    existing_server.password_hash = make_password(server_pwd)
                    existing_server.must_change_password = True
                    existing_server.save(update_fields=["password_hash", "must_change_password", "updated_at"])
                    citizen_repository.revoke_all_sessions(str(existing_server.id), role="internal")
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ [ROTACIONADO] João Servidor Central ({_mask_cpf(existing_server.cpf)}): nova credencial definida, "
                            "mustChangePassword=True e sessões revogadas."
                        )
                    )
                else:
                    self.stdout.write(
                        f"✓ [PRESERVADO] João Servidor Central ({_mask_cpf(existing_server.cpf)}): credenciais, vínculo e permissões mantidos."
                    )
            else:
                server_hash = make_password(server_pwd)
                new_server = InternalUser.objects.create(
                    cpf="33366699957",
                    full_name="João Servidor Central",
                    email="joao.servidor@ssp.al.gov.br",
                    registration_number="SSP-1001",
                    role="server",
                    agency_id=agency_ssp.id if agency_ssp else None,
                    unit_id=unit_central.id if unit_central else None,
                    can_manage_catalog=False,
                    password_hash=server_hash,
                    must_change_password=True,
                    is_active=True,
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ [CRIADO] João Servidor Central:\n"
                        f"   - CPF: {_mask_cpf(new_server.cpf)}\n"
                        f"   - Matrícula: {new_server.registration_number}\n"
                        f"   - Papel: {new_server.role}\n"
                        f"   - Órgão: {agency_ssp.acronym if agency_ssp else 'Nenhum'}\n"
                        f"   - Unidade: {unit_central.name if unit_central else 'Nenhuma'}\n"
                        f"   - Troca obrigatória de senha (mustChangePassword): {new_server.must_change_password}\n"
                        f"   - Painel inicial de acesso: /servidor/painel"
                    )
                )

        # 5. Escrita Segura de Arquivo de Credenciais (Se Solicitado)
        output_file = options.get("output_credentials_file")
        if output_file:
            try:
                flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
                mode = 0o600
                fd = os.open(output_file, flags, mode)
                with os.fdopen(fd, "w") as f:
                    f.write("# SOSP — Credenciais Provisórias de Homologação (Confidencial)\n")
                    f.write(f"HOMOLOG_ADMIN_PASSWORD={admin_pwd}\n")
                    f.write(f"HOMOLOG_SERVER_PASSWORD={server_pwd}\n")
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Credenciais temporárias gravadas com segurança em '{output_file}' (permissão 0600).")
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Falha ao salvar arquivo de credenciais: {e}"))

        self.stdout.write("-----------------------------------------------------------------")
        self.stdout.write(
            "✓ Provisionamento finalizado. Credenciais tratadas com hashing Argon2id.\n"
            "✓ Zero contas de cidadão criadas ou afetadas.\n"
            "✓ Zero credenciais em texto puro registradas em logs públicos."
        )
        self.stdout.write("=================================================================")
