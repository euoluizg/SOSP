import os
import secrets
import string
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.hashers import make_password
from apps.accounts.models import Citizen, InternalUser, Gender

class Command(BaseCommand):
    help = "Cria ou atualiza com idempotência os usuários sintéticos de demonstração do SOSP (cidadãos, servidores e gestores)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            type=str,
            default=None,
            help="Senha temporária explícita para as contas sintéticas em ambiente de desenvolvimento local.",
        )

    def handle(self, *args, **options):
        django_env = getattr(settings, "DJANGO_ENV", "development").lower()
        if django_env in ("staging", "production") and not getattr(settings, "ALLOW_DEMO_SEED", False):
            raise CommandError(
                f"Operação bloqueada por política de segurança: O seed de usuários de demonstração com credenciais "
                f"sintéticas é estritamente proibido no ambiente '{django_env}'. Contas privilegiadas demonstrativas "
                "não devem ser provisionadas em ambientes acessíveis ou de produção."
            )

        self.stdout.write("Inicializando seed seguro de usuários de demonstração...")

        # Obtém credencial de demonstração: via flag, variável de ambiente ou gerada dinamicamente
        demo_auth_secret = options.get("password") or os.environ.get("DEMO_ACCOUNTS_PASSWORD")
        is_generated = False
        if not demo_auth_secret:
            token_entropy = secrets.token_urlsafe(16)
            demo_auth_secret = f"A1!{token_entropy}"
            is_generated = True

        pwd_hash = make_password(demo_auth_secret)

        # 1. Garante gênero padrão
        gender_na, _ = Gender.objects.get_or_create(
            name="Não Informado",
            defaults={"sort_order": 99}
        )
        gender_f, _ = Gender.objects.get_or_create(
            name="Feminino",
            defaults={"sort_order": 1}
        )
        gender_m, _ = Gender.objects.get_or_create(
            name="Masculino",
            defaults={"sort_order": 2}
        )

        # 2. Cidadãos de demonstração
        citizens_data = [
            {
                "cpf": "11144477735",
                "full_name": "Cidadão de Testes",
                "email": "cidadao@exemplo.com.br",
                "birth_date": "1990-05-15",
                "mother_name": "Maria de Testes",
                "phone": "82999887766",
                "gender": gender_m,
                "is_pcd": False,
                "zip_code": "57020100",
                "street": "Rua do Comércio",
                "neighborhood": "Centro",
                "city": "Maceió",
                "state": "AL",
                "address_number": "123",
            },
            {
                "cpf": "22255588846",
                "full_name": "Maria Santos Silva",
                "email": "maria.silva@exemplo.com.br",
                "birth_date": "1988-08-20",
                "mother_name": "Ana Maria Santos",
                "phone": "82988776655",
                "gender": gender_f,
                "is_pcd": False,
                "zip_code": "57035000",
                "street": "Av. Álvaro Otacílio",
                "neighborhood": "Ponta Verde",
                "city": "Maceió",
                "state": "AL",
                "address_number": "200",
            },
        ]

        for c_data in citizens_data:
            c, created = Citizen.objects.update_or_create(
                cpf=c_data["cpf"],
                defaults={
                    "full_name": c_data["full_name"],
                    "email": c_data["email"],
                    "birth_date": c_data["birth_date"],
                    "mother_name": c_data["mother_name"],
                    "phone": c_data["phone"],
                    "gender": c_data["gender"],
                    "is_pcd": c_data["is_pcd"],
                    "zip_code": c_data["zip_code"],
                    "street": c_data["street"],
                    "neighborhood": c_data["neighborhood"],
                    "city": c_data["city"],
                    "state": c_data["state"],
                    "address_number": c_data["address_number"],
                    "password_hash": pwd_hash,
                    "password_salt": "argon2_salt",
                    "is_active": True,
                }
            )
            action = "Criado" if created else "Atualizado"
            self.stdout.write(self.style.SUCCESS(f"  [Cidadão] {action}: {c.full_name} ({c.cpf})"))

        # 3. Usuários Internos (Servidores e Gestores)
        internal_data = [
            {
                "cpf": "33366699957",
                "name": "João Servidor Central",
                "email": "joao.servidor@ssp.al.gov.br",
                "role": "server",
                "registration_number": "SSP-1001",
            },
            {
                "cpf": "44477700083",
                "name": "Ana Servidora Farol",
                "email": "ana.servidora@detran.al.gov.br",
                "role": "server",
                "registration_number": "DET-2002",
            },
            {
                "cpf": "55588811194",
                "name": "Carlos Gestor SSP",
                "email": "carlos.gestor@ssp.al.gov.br",
                "role": "manager",
                "registration_number": "GES-3003",
            },
            {
                "cpf": "99988877714",
                "name": "Admin SOSP Geral",
                "email": "admin@sosp.al.gov.br",
                "role": "superadmin",
                "registration_number": "ADM-0001",
            },
        ]

        for u_data in internal_data:
            u, created = InternalUser.objects.update_or_create(
                cpf=u_data["cpf"],
                defaults={
                    "name": u_data["name"],
                    "email": u_data["email"],
                    "role": u_data["role"],
                    "registration_number": u_data["registration_number"],
                    "password_hash": pwd_hash,
                    "is_active": True,
                }
            )
            action = "Criado" if created else "Atualizado"
            self.stdout.write(self.style.SUCCESS(f"  [Interno] {action}: {u.name} (Role: {u.role})"))

        self.stdout.write(self.style.SUCCESS("✓ Seed de usuários concluído com sucesso. Zero agendamentos criados."))
        if is_generated:
            self.stdout.write(self.style.WARNING(
                f"\n[AVISO DE SEGURANÇA] Credencial temporária gerada dinamicamente para esta execução local:\n"
                f"  Credencial: {demo_auth_secret}\n"
                f"Guarde esta credencial se desejar realizar testes manuais. Nenhuma senha estática está gravada no código versionado."
            ))
