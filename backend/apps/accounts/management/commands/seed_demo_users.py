import os
import secrets
import string
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.hashers import make_password
from apps.accounts.models import Citizen, InternalUser, Gender
from apps.catalog.models import (
    Agency,
    Unit,
    Service,
    ServiceAgency,
    UnitService,
    ServiceStep,
    ServiceDocument,
)

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

        # 3. Garante órgãos e unidades institucionais de lotação (ADR-003 / RN-35 / RN-36)
        agency_ssp = Agency.objects.filter(acronym="SSP", is_active=True).first()
        if not agency_ssp:
            agency_ssp = Agency.objects.create(
                name="Secretaria de Estado da Segurança Pública",
                acronym="SSP",
                sphere="state",
                description="Responsável pela segurança pública e identificação civil.",
                is_active=True,
            )

        agency_detran = Agency.objects.filter(acronym__in=["DETRAN", "DETRAN-AL"], is_active=True).first()
        if not agency_detran:
            agency_detran = Agency.objects.create(
                name="Departamento Estadual de Trânsito",
                acronym="DETRAN",
                sphere="state",
                description="Responsável pela habilitação de condutores e trânsito.",
                is_active=True,
            )

        # Garante unidades de atendimento para vinculação de servidores operacionais
        unit_ssp_centro = Unit.objects.filter(agency=agency_ssp, name__icontains="Central", is_active=True).first()
        if not unit_ssp_centro:
            unit_ssp_centro = Unit.objects.create(
                agency=agency_ssp,
                name="Posto Central SSP",
                zip_code="57020100",
                street="Rua do Comércio",
                neighborhood="Centro",
                city="Maceió",
                state="AL",
                address_number="123",
                daily_limit=40,
                is_active=True,
            )

        unit_ssp_interior = Unit.objects.filter(agency=agency_ssp, name__icontains="Interior", is_active=True).first()
        if not unit_ssp_interior:
            unit_ssp_interior = Unit.objects.create(
                agency=agency_ssp,
                name="Posto Interior SSP (Arapiraca)",
                zip_code="57300000",
                street="Rua Esperança",
                neighborhood="Brasília",
                city="Arapiraca",
                state="AL",
                address_number="789",
                daily_limit=30,
                is_active=True,
            )

        unit_detran_farol = Unit.objects.filter(agency=agency_detran, name__icontains="Farol", is_active=True).first()
        if not unit_detran_farol:
            unit_detran_farol = Unit.objects.create(
                agency=agency_detran,
                name="Posto Farol DETRAN",
                zip_code="57051000",
                street="Av. Fernandes Lima",
                neighborhood="Farol",
                city="Maceió",
                state="AL",
                address_number="456",
                daily_limit=40,
                is_active=True,
            )

        # 4. Usuários Internos (Servidores, Gestores e Administradores)
        internal_data = [
            {
                "cpf": "33366699957",
                "full_name": "João Servidor Central",
                "email": "joao.servidor@ssp.al.gov.br",
                "role": "servant",
                "agency_id": agency_ssp.id,
                "unit_id": unit_ssp_centro.id,
                "can_manage_catalog": False,
                "registration_number": "SSP-1001",
            },
            {
                "cpf": "44477700083",
                "full_name": "Ana Servidora Farol",
                "email": "ana.servidora@detran.al.gov.br",
                "role": "servant",
                "agency_id": agency_detran.id,
                "unit_id": unit_detran_farol.id,
                "can_manage_catalog": False,
                "registration_number": "DET-2002",
            },
            {
                "cpf": "55588811194",
                "full_name": "Carlos Gestor SSP",
                "email": "carlos.gestor@ssp.al.gov.br",
                "role": "gestor",
                "agency_id": agency_ssp.id,
                "unit_id": None,
                "can_manage_catalog": True,
                "registration_number": "GES-3003",
            },
            {
                "cpf": "99988877714",
                "full_name": "Admin SOSP Geral",
                "email": "admin@sosp.al.gov.br",
                "role": "superadmin",
                "agency_id": None,
                "unit_id": None,
                "can_manage_catalog": True,
                "registration_number": "ADM-0001",
            },
        ]

        for u_data in internal_data:
            u, created = InternalUser.objects.update_or_create(
                cpf=u_data["cpf"],
                defaults={
                    "full_name": u_data["full_name"],
                    "email": u_data["email"],
                    "role": u_data["role"],
                    "agency_id": u_data.get("agency_id"),
                    "unit_id": u_data.get("unit_id"),
                    "can_manage_catalog": u_data.get("can_manage_catalog", False),
                    "registration_number": u_data["registration_number"],
                    "password_hash": pwd_hash,
                    "is_active": True,
                }
            )
            action = "Criado" if created else "Atualizado"
            self.stdout.write(self.style.SUCCESS(f"  [Interno] {action}: {u.full_name} (Role: {u.role})"))

        # 5. Serviços Demonstrativos do Catálogo SOSP (RF-04, RF-05, RF-06, RF-08)
        cin_service = Service.objects.filter(name__icontains="Identidade Nacional").first()
        if not cin_service:
            cin_service = Service.objects.create(
                name="Emitir Carteira de Identidade Nacional (CIN)",
                category="documents",
                detailed_description="A Carteira de Identidade Nacional (CIN) adota o CPF como número único de identificação em todo o território nacional. Possui versões física em papel de segurança e digital via aplicativo Gov.br.",
                eligibility="Cidadãos brasileiros natos ou naturalizados residentes em Alagoas.",
                prerequisites="Possuir CPF regularizado na Receita Federal e Certidão de Nascimento ou Casamento atualizada.",
                is_free=True,
                channel="inPerson",
                status="active",
                current_version=1,
            )
            ServiceAgency.objects.get_or_create(service=cin_service, agency=agency_ssp)
            UnitService.objects.get_or_create(unit=unit_ssp_centro, service=cin_service, defaults={"is_active": True})
            UnitService.objects.get_or_create(unit=unit_ssp_interior, service=cin_service, defaults={"is_active": True})

            ServiceStep.objects.bulk_create([
                ServiceStep(service=cin_service, step_order=1, title="Agendamento Prévio", description="Agende seu dia e horário no portal SOSP ou compareça a uma Central Já!."),
                ServiceStep(service=cin_service, step_order=2, title="Separação dos Documentos", description="Confira o checklist e leve todos os documentos originais."),
                ServiceStep(service=cin_service, step_order=3, title="Coleta Biométrica", description="Compareça com 15 minutos de antecedência para foto digital e digitais."),
                ServiceStep(service=cin_service, step_order=4, title="Retirada do Documento", description="Retorne à unidade após o prazo informado para receber o documento."),
            ])

            ServiceDocument.objects.bulk_create([
                ServiceDocument(service=cin_service, name="Certidão de Nascimento ou Casamento (Original)", is_mandatory=True),
                ServiceDocument(service=cin_service, name="Comprovante de Residência Atualizado", is_mandatory=True),
                ServiceDocument(service=cin_service, name="Comprovante de Pagamento da Taxa DARE", is_mandatory=False),
            ])
            self.stdout.write(self.style.SUCCESS(f"  [Catálogo] Criado: {cin_service.name}"))

        cnh_service = Service.objects.filter(name__icontains="Habilitação").first()
        if not cnh_service:
            cnh_service = Service.objects.create(
                name="Renovação da Carteira Nacional de Habilitação (CNH)",
                category="transit",
                detailed_description="Renovação periódica do documento de habilitação de condutores de veículos automotores em Alagoas.",
                eligibility="Condutores habilitados com CNH vencida ou a vencer nos próximos 30 dias.",
                prerequisites="Não possuir bloqueio judicial ou administrativo no prontuário.",
                is_free=False,
                cost_amount=110.00,
                channel="hybrid",
                status="active",
                current_version=1,
            )
            ServiceAgency.objects.get_or_create(service=cnh_service, agency=agency_detran)
            UnitService.objects.get_or_create(unit=unit_detran_farol, service=cnh_service, defaults={"is_active": True})

            ServiceStep.objects.bulk_create([
                ServiceStep(service=cnh_service, step_order=1, title="Abertura do Processo", description="Solicite a renovação no portal ou presencialmente."),
                ServiceStep(service=cnh_service, step_order=2, title="Exame de Aptidão Física e Mental", description="Realize os exames na clínica credenciada indicada."),
                ServiceStep(service=cnh_service, step_order=3, title="Pagamento da Taxa", description="Efetue o pagamento da guia DARE na rede bancária."),
                ServiceStep(service=cnh_service, step_order=4, title="Emissão e Envio", description="Acompanhe a entrega pelos Correios ou retire na unidade."),
            ])

            ServiceDocument.objects.bulk_create([
                ServiceDocument(service=cnh_service, name="CNH Anterior ou Documento Oficial de Identidade", is_mandatory=True),
                ServiceDocument(service=cnh_service, name="Comprovante de Residência Atualizado", is_mandatory=True),
            ])
            self.stdout.write(self.style.SUCCESS(f"  [Catálogo] Criado: {cnh_service.name}"))

        self.stdout.write(self.style.SUCCESS("✓ Seed de usuários concluído com sucesso. Zero agendamentos criados."))
        if is_generated:
            self.stdout.write(self.style.SUCCESS(
                "[SEGURANÇA] Credencial temporária gerada e aplicada com sucesso. "
                "Valor mascarado para proteção contra vazamento em logs compartilhados e pipelines de CI."
            ))
