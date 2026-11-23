import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional

CATEGORY_SLUG_TO_LABEL: Dict[str, str] = {
    "documents": "Documentos",
    "health": "Saúde",
    "education": "Educação",
    "transport": "Transporte",
    "transit": "Transporte",
    "socialAssistance": "Assistência Social",
    "taxes": "Tributos",
    "work": "Trabalho",
    "housing": "Habitação",
    "environment": "Meio Ambiente",
    "business": "Empresas",
    "general": "Geral",
}

BASELINE_CATEGORY_SLUGS = {
    "documents",
    "health",
    "education",
    "transport",
    "socialAssistance",
    "taxes",
    "work",
}

CATEGORY_LABEL_TO_SLUG: Dict[str, str] = {
    "documentos": "documents",
    "documentos pessoais": "documents",
    "saúde": "health",
    "saude": "health",
    "educação": "education",
    "educacao": "education",
    "transporte": "transport",
    "transporte e mobilidade": "transport",
    "trânsito": "transport",
    "transito": "transport",
    "transit": "transport",
    "trânsito e veículos": "transport",
    "assistência social": "socialAssistance",
    "assistencia social": "socialAssistance",
    "tributos": "taxes",
    "tributos e impostos": "taxes",
    "trabalho": "work",
    "habitação": "socialAssistance",
    "habitacao": "socialAssistance",
    "housing": "socialAssistance",
    "meio ambiente": "documents",
    "environment": "documents",
    "empresas": "work",
    "business": "work",
    "geral": "documents",
    "general": "documents",
    "cidadania e direitos": "documents",
}


def normalize_category_slug(raw_category: str) -> str:
    val = (raw_category or "documents").strip()
    if val in BASELINE_CATEGORY_SLUGS:
        return val
    return CATEGORY_LABEL_TO_SLUG.get(val.lower(), "documents")


def category_slug_to_label(raw_category: str) -> str:
    val = (raw_category or "general").strip()
    return CATEGORY_SLUG_TO_LABEL.get(val, val)


class CatalogInMemoryRepository:
    def __init__(self):
        self._agencies: List[Dict[str, Any]] = [
            {
                "id": "orgao-ssp",
                "name": "Secretaria de Estado da Segurança Pública",
                "acronym": "SSP",
                "sphere": "state",
                "description": "Responsável pela segurança pública, identificação civil e perícia oficial do Estado de Alagoas.",
                "website": "https://seguranca.al.gov.br",
                "phone": "(82) 3315-2822",
                "email": "contato@ssp.al.gov.br",
                "isActive": True,
            },
            {
                "id": "orgao-detran",
                "name": "Departamento Estadual de Trânsito",
                "acronym": "DETRAN-AL",
                "sphere": "state",
                "description": "Responsável pela habilitação de condutores, registro de veículos e fiscalização do trânsito.",
                "website": "https://www.detran.al.gov.br",
                "phone": "(82) 3315-1533",
                "email": "ouvidoria@detran.al.gov.br",
                "isActive": True,
            },
            {
                "id": "orgao-sefaz",
                "name": "Secretaria de Estado da Fazenda",
                "acronym": "SEFAZ-AL",
                "sphere": "state",
                "description": "Gestão tributária, arrecadação e administração financeira do Estado.",
                "website": "https://www.sefaz.al.gov.br",
                "phone": "(82) 3315-7000",
                "email": "atendimento@sefaz.al.gov.br",
                "isActive": True,
            },
            {
                "id": "orgao-seduc",
                "name": "Secretaria de Estado da Educação",
                "acronym": "SEDUC",
                "sphere": "state",
                "description": "Coordenação das políticas educacionais e rede escolar estadual.",
                "website": "https://www.educacao.al.gov.br",
                "phone": "(82) 3315-1200",
                "email": "contato@educacao.al.gov.br",
                "isActive": True,
            },
            {
                "id": "orgao-sesau",
                "name": "Secretaria de Estado da Saúde",
                "acronym": "SESAU",
                "sphere": "state",
                "description": "Gestão do Sistema Único de Saúde (SUS) no âmbito estadual.",
                "website": "https://saude.al.gov.br",
                "phone": "(82) 3315-1100",
                "email": "ouvidoria@saude.al.gov.br",
                "isActive": True,
            },
        ]

        self._units: List[Dict[str, Any]] = [
            {
                "id": "unidade-centro",
                "agencyId": "orgao-ssp",
                "name": "Central Já! Centro",
                "street": "Rua do Comércio",
                "number": "123",
                "neighborhood": "Centro",
                "city": "Maceió",
                "state": "AL",
                "zipCode": "57020-100",
                "phone": "(82) 3315-1000",
                "businessHours": "08:00 às 17:00 (Segunda a Sexta)",
                "dailyCapacity": 120,
                "hasPcdAccess": True,
                "latitude": -9.6658,
                "longitude": -35.7353,
                "isActive": True,
            },
            {
                "id": "unidade-farol",
                "agencyId": "orgao-detran",
                "name": "Central Já! Shopping Farol",
                "street": "Av. Fernandes Lima",
                "number": "500",
                "neighborhood": "Farol",
                "city": "Maceió",
                "state": "AL",
                "zipCode": "57055-000",
                "phone": "(82) 3315-2000",
                "businessHours": "10:00 às 19:00 (Segunda a Sexta)",
                "dailyCapacity": 160,
                "hasPcdAccess": True,
                "latitude": -9.6450,
                "longitude": -35.7280,
                "isActive": True,
            },
            {
                "id": "unidade-mangabeiras",
                "agencyId": "orgao-ssp",
                "name": "Central Já! Maceió Shopping",
                "street": "Av. Comendador Gustavo Paiva",
                "number": "2990",
                "neighborhood": "Mangabeiras",
                "city": "Maceió",
                "state": "AL",
                "zipCode": "57037-901",
                "phone": "(82) 3315-3000",
                "businessHours": "10:00 às 19:00 (Segunda a Sexta)",
                "dailyCapacity": 180,
                "hasPcdAccess": True,
                "latitude": -9.6432,
                "longitude": -35.7088,
                "isActive": True,
            },
            {
                "id": "unidade-arapiraca",
                "agencyId": "orgao-ssp",
                "name": "Central Já! Arapiraca",
                "street": "Rua São Francisco",
                "number": "450",
                "neighborhood": "Centro",
                "city": "Arapiraca",
                "state": "AL",
                "zipCode": "57300-000",
                "phone": "(82) 3521-1234",
                "businessHours": "08:00 às 17:00 (Segunda a Sexta)",
                "dailyCapacity": 100,
                "hasPcdAccess": True,
                "latitude": -9.7517,
                "longitude": -36.6603,
                "isActive": True,
            },
        ]

        self._services: List[Dict[str, Any]] = [
            {
                "id": "servico-emitir-rg",
                "name": "Emitir Carteira de Identidade Nacional (CIN)",
                "summary": "Emissão da 1ª ou 2ª via da Carteira de Identidade Nacional física e digital.",
                "description": "A Carteira de Identidade Nacional (CIN) adota o CPF como número único de identificação em todo o território nacional. Possui versões física em papel de segurança e digital via aplicativo Gov.br.",
                "category": "Documentos Pessoais",
                "channel": "inPerson",
                "agencyId": "orgao-ssp",
                "agencyName": "Secretaria de Estado da Segurança Pública",
                "agencyAcronym": "SSP",
                "unitId": "unidade-centro",
                "unitName": "Central Já! Centro",
                "requiresAppointment": True,
                "isOnline": False,
                "estimatedDuration": "30 a 45 minutos no atendimento; entrega em até 10 dias úteis",
                "cost": "Gratuito para 1ª via; R$ 42,00 para 2ª via",
                "targetAudience": "Cidadãos brasileiros natos ou naturalizados residentes em Alagoas.",
                "requirements": [
                    "Possuir CPF regularizado na Receita Federal",
                    "Apresentar Certidão de Nascimento (se solteiro) ou Casamento (se casado)",
                    "Comprovante de residência atualizado",
                ],
                "documents": [
                    {"name": "Certidão de Nascimento ou Casamento (Original)", "isRequired": True, "description": "Legível e sem rasuras."},
                    {"name": "Comprovante de Residência", "isRequired": True, "description": "Conta de água, luz ou telefone dos últimos 3 meses."},
                    {"name": "Comprovante de Pagamento da Taxa DARE", "isRequired": False, "description": "Apenas em caso de 2ª via."},
                ],
                "steps": [
                    {"stepNumber": 1, "title": "Agendamento Prévio", "description": "Agende seu dia e horário no portal SOSP ou compareça a uma Central Já!."},
                    {"stepNumber": 2, "title": "Separação dos Documentos", "description": "Confira o checklist e leve todos os documentos originais."},
                    {"stepNumber": 3, "title": "Coleta Biométrica", "description": "Compareça com 15 minutos de antecedência para foto digital e digitais."},
                    {"stepNumber": 4, "title": "Retirada do Documento", "description": "Retorne à unidade após o prazo informado para receber o documento."},
                ],
                "isActive": True,
            },
            {
                "id": "servico-renovar-cnh",
                "name": "Renovação da Carteira Nacional de Habilitação (CNH)",
                "summary": "Renovação periódica do documento de habilitação de condutores de veículos automotores.",
                "description": "Procedimento obrigatório para condutores cuja habilitação está vencida ou prestes a vencer nos próximos 30 dias.",
                "category": "Trânsito e Veículos",
                "channel": "hybrid",
                "agencyId": "orgao-detran",
                "agencyName": "Departamento Estadual de Trânsito",
                "agencyAcronym": "DETRAN-AL",
                "unitId": "unidade-farol",
                "unitName": "Central Já! Shopping Farol",
                "requiresAppointment": True,
                "isOnline": False,
                "estimatedDuration": "Atendimento em 20 min; entrega em 5 dias úteis",
                "cost": "R$ 138,50 (taxa Detran) + R$ 120,00 (exame médico)",
                "targetAudience": "Condutores habilitados em Alagoas.",
                "requirements": [
                    "CNH atual legível",
                    "Aprovação em exame de aptidão física e mental",
                ],
                "documents": [
                    {"name": "CNH Anterior ou Documento com Foto", "isRequired": True, "description": "Original."},
                    {"name": "Comprovante de Residência Atualizado", "isRequired": True, "description": "Últimos 90 dias."},
                ],
                "steps": [
                    {"stepNumber": 1, "title": "Abertura do Processo", "description": "Inicie pelo portal e pague a taxa emitida."},
                    {"stepNumber": 2, "title": "Exame Médico", "description": "Realize o exame na clínica credenciada indicada."},
                    {"stepNumber": 3, "title": "Retirada ou Envio", "description": "Receba sua CNH em domicílio ou retire na unidade."},
                ],
                "isActive": True,
            },
            {
                "id": "servico-isencao-ipva",
                "name": "Solicitação de Isenção de IPVA para PCD",
                "summary": "Pedido de não incidência do imposto sobre propriedade de veículos destinados a pessoas com deficiência.",
                "description": "Benefício fiscal concedido a proprietários de veículos portadores de deficiência física, visual, mental severa ou autismo.",
                "category": "Tributos e Impostos",
                "channel": "online",
                "agencyId": "orgao-sefaz",
                "agencyName": "Secretaria de Estado da Fazenda",
                "agencyAcronym": "SEFAZ-AL",
                "unitId": "unidade-centro",
                "unitName": "Central Já! Centro",
                "requiresAppointment": False,
                "isOnline": True,
                "estimatedDuration": "Até 30 dias úteis para análise fiscal",
                "cost": "Gratuito",
                "targetAudience": "Pessoas com deficiência proprietárias de veículo automotor registrado em Alagoas.",
                "requirements": [
                    "Laudo médico pericial conclusivo emitido pelo SUS ou Detran",
                    "Veículo com valor venal dentro do teto estipulado pela legislação estadual",
                ],
                "documents": [
                    {"name": "Laudo Pericial Oficial", "isRequired": True, "description": "Com CID da patologia."},
                    {"name": "CRLV do Veículo", "isRequired": True, "description": "Em nome do beneficiário ou representante."},
                ],
                "steps": [
                    {"stepNumber": 1, "title": "Envio Digital dos Documentos", "description": "Faça upload pelo portal do SOSP ou SEFAZ."},
                    {"stepNumber": 2, "title": "Análise da Procuradoria", "description": "A SEFAZ analisa o laudo médico e os requisitos legais."},
                    {"stepNumber": 3, "title": "Deferimento", "description": "Acompanhe o protocolo até a expedição do certificado de isenção."},
                ],
                "isActive": True,
            },
            {
                "id": "servico-passe-livre",
                "name": "Passe Livre Intermunicipal para Idosos e PCD",
                "summary": "Gratuidade no transporte rodoviário intermunicipal em Alagoas.",
                "description": "Benefício de transporte gratuito concedido a pessoas idosas e com deficiência comprovadamente carentes.",
                "category": "Transporte e Mobilidade",
                "channel": "inPerson",
                "agencyId": "orgao-seduc",
                "agencyName": "Secretaria de Estado da Educação",
                "agencyAcronym": "SEDUC",
                "unitId": "unidade-centro",
                "unitName": "Central Já! Centro",
                "requiresAppointment": True,
                "isOnline": False,
                "estimatedDuration": "20 minutos para entrega dos documentos",
                "cost": "Gratuito",
                "targetAudience": "Idosos acima de 65 anos e pessoas com deficiência com renda de até 1 salário mínimo.",
                "requirements": ["Comprovante de renda familiar", "Laudo médico para PCD"],
                "documents": [
                    {"name": "Documento de Identidade com Foto", "isRequired": True, "description": "Original e cópia."},
                    {"name": "Comprovante de Renda", "isRequired": True, "description": "Extrato de benefício do INSS."},
                ],
                "steps": [
                    {"stepNumber": 1, "title": "Agendamento", "description": "Agende na Central Já!."},
                    {"stepNumber": 2, "title": "Entrega dos Laudos", "description": "Apresente a documentação comprobatória."},
                ],
                "isActive": True,
            },
            {
                "id": "servico-cartao-sus",
                "name": "Emissão e Atualização do Cartão SUS",
                "summary": "Documento nacional de identificação do usuário do Sistema Único de Saúde.",
                "description": "Cadastro nacional com dados de atendimento do paciente na rede pública de saúde.",
                "category": "Saúde",
                "channel": "inPerson",
                "agencyId": "orgao-sesau",
                "agencyName": "Secretaria de Estado da Saúde",
                "agencyAcronym": "SESAU",
                "unitId": "unidade-centro",
                "unitName": "Central Já! Centro",
                "requiresAppointment": True,
                "isOnline": False,
                "estimatedDuration": "15 minutos",
                "cost": "Gratuito",
                "targetAudience": "Todos os cidadãos residentes.",
                "requirements": ["CPF regularizado"],
                "documents": [
                    {"name": "Documento com Foto", "isRequired": True, "description": "RG ou CNH."},
                    {"name": "Comprovante de Residência", "isRequired": True, "description": "Atualizado."},
                ],
                "steps": [
                    {"stepNumber": 1, "title": "Atendimento Presencial", "description": "Emissão imediata no balcão."},
                ],
                "isActive": True,
            },
        ]

        self._categories: List[str] = [
            "Todos",
            "Documentos Pessoais",
            "Trânsito e Veículos",
            "Tributos e Impostos",
            "Saúde",
            "Transporte e Mobilidade",
            "Cidadania e Direitos",
        ]

    def get_agencies(self) -> List[Dict[str, Any]]:
        return [a for a in self._agencies if a.get("isActive", True)]

    def get_agency_by_id(self, agency_id: str) -> Optional[Dict[str, Any]]:
        for a in self._agencies:
            if a["id"] == agency_id:
                return dict(a)
        return None

    def create_agency(self, data: Dict[str, Any]) -> Dict[str, Any]:
        agency = {
            "id": str(uuid.uuid4()),
            "name": data["name"].strip(),
            "acronym": data["acronym"].strip().upper(),
            "sphere": data.get("sphere", "state"),
            "description": (data.get("description") or "").strip(),
            "isActive": True,
        }
        self._agencies.insert(0, agency)
        return dict(agency)

    def update_agency(self, agency_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for a in self._agencies:
            if a["id"] == agency_id:
                if "name" in data:
                    a["name"] = data["name"].strip()
                if "acronym" in data:
                    a["acronym"] = data["acronym"].strip().upper()
                if "sphere" in data:
                    a["sphere"] = data["sphere"].strip()
                if "description" in data:
                    a["description"] = data["description"].strip()
                if "isActive" in data:
                    a["isActive"] = bool(data["isActive"])
                return dict(a)
        return None

    def deactivate_agency(self, agency_id: str) -> Optional[Dict[str, Any]]:
        return self.update_agency(agency_id, {"isActive": False})

    def get_units(self, agency_id: Optional[str] = None) -> List[Dict[str, Any]]:
        units = [u for u in self._units if u.get("isActive", True)]
        if agency_id:
            units = [u for u in units if u.get("agencyId") == agency_id]
        return units

    def get_unit_by_id(self, unit_id: str) -> Optional[Dict[str, Any]]:
        for u in self._units:
            if u["id"] == unit_id:
                return dict(u)
        return None

    def create_unit(self, data: Dict[str, Any]) -> Dict[str, Any]:
        unit = {
            "id": str(uuid.uuid4()),
            "agencyId": data["agencyId"],
            "name": data["name"].strip(),
            "cep": data.get("zipCode", "57020100"),
            "zipCode": data.get("zipCode", "57020100"),
            "street": data["street"].strip(),
            "number": data.get("number", "S/N").strip(),
            "neighborhood": data.get("neighborhood", "Centro").strip(),
            "city": data.get("city", "Maceió").strip(),
            "state": data.get("state", "AL").strip().upper(),
            "phone": data.get("phone", ""),
            "email": data.get("email", ""),
            "openingHours": data.get("openingHours", "08:00 às 17:00"),
            "dailyLimit": int(data.get("dailyLimit", 60)),
            "dailyCapacity": int(data.get("dailyLimit", 60)),
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "isPcdAccessible": bool(data.get("isPcdAccessible", True)),
            "hasPriorityService": bool(data.get("hasPriorityService", True)),
            "isActive": True,
        }
        self._units.insert(0, unit)
        return dict(unit)

    def update_unit(self, unit_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for u in self._units:
            if u["id"] == unit_id:
                for key in ("name", "dailyLimit", "isPcdAccessible", "hasPriorityService", "isActive"):
                    if key in data:
                        u[key] = data[key]
                if "dailyLimit" in data:
                    u["dailyCapacity"] = data["dailyLimit"]
                return dict(u)
        return None

    def deactivate_unit(self, unit_id: str) -> Optional[Dict[str, Any]]:
        return self.update_unit(unit_id, {"isActive": False})

    def get_services(self) -> List[Dict[str, Any]]:
        return [s for s in self._services if s.get("isActive", True)]

    def get_service_by_id(self, service_id: str) -> Optional[Dict[str, Any]]:
        for s in self._services:
            if s["id"] == service_id:
                return dict(s)
        return None

    def create_service(self, data: Dict[str, Any], created_by_id: Optional[str] = None) -> Dict[str, Any]:
        agency = self.get_agency_by_id(data["agencyId"])
        is_free = bool(data.get("isFree", True))
        cost_amount = None if is_free else float(data.get("costAmount") or 0)
        deadline = int(data.get("averageDeadlineDays", 5))
        cat_slug = normalize_category_slug(data.get("category", "documents"))
        svc = {
            "id": str(uuid.uuid4()),
            "name": data["name"].strip(),
            "category": category_slug_to_label(cat_slug),
            "categorySlug": cat_slug,
            "channel": data.get("channel", "inPerson"),
            "agencyId": data["agencyId"],
            "agencyAcronym": agency["acronym"] if agency else "SOSP",
            "agencyName": agency["name"] if agency else "Governo de Alagoas",
            "isFree": is_free,
            "costAmount": cost_amount,
            "cost": "Gratuito" if is_free else f"R$ {cost_amount:.2f}",
            "averageDeadlineDays": deadline,
            "estimatedDuration": "Imediato" if deadline == 0 else f"{deadline} dias úteis",
            "summary": data["description"].strip()[:160],
            "description": data["description"].strip(),
            "whoCanUse": data.get("whoCanUse", "Cidadãos residentes em Alagoas.").strip(),
            "targetAudience": data.get("whoCanUse", "Cidadãos residentes em Alagoas.").strip(),
            "prerequisites": data.get("prerequisites", "").strip(),
            "externalUrl": data.get("externalUrl", "").strip() or None,
            "updatedAt": "2026-11-22T00:00:00Z",
            "unitCount": 1,
            "cities": ["Maceió"],
            "documents": [],
            "steps": [],
            "isActive": True,
        }
        self._services.insert(0, svc)
        return dict(svc)

    def update_service(self, service_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for s in self._services:
            if s["id"] == service_id:
                if "name" in data:
                    s["name"] = data["name"].strip()
                if "description" in data:
                    s["description"] = data["description"].strip()
                    s["summary"] = s["description"][:160]
                if "category" in data:
                    slug = normalize_category_slug(data["category"])
                    s["categorySlug"] = slug
                    s["category"] = category_slug_to_label(slug)
                if "channel" in data:
                    s["channel"] = data["channel"]
                if "isActive" in data:
                    s["isActive"] = bool(data["isActive"])
                return dict(s)
        return None

    def deactivate_service(self, service_id: str) -> Optional[Dict[str, Any]]:
        return self.update_service(service_id, {"isActive": False})

    def get_categories(self) -> List[str]:
        return self._categories

    def list_faqs(self) -> List[Dict[str, Any]]:
        return []

_catalog_memory_repository = CatalogInMemoryRepository()


class CatalogDjangoORMRepository:
    """Implementação real de persistência PostgreSQL via Django ORM (ADR-001 / Etapa 3)."""

    def get_agencies(self) -> List[Dict[str, Any]]:
        from .models import Agency
        agencies = Agency.objects.filter(is_active=True, deleted_at__isnull=True).order_by("name")
        return [
            {
                "id": str(a.id),
                "name": a.name,
                "acronym": a.acronym,
                "sphere": a.sphere,
                "description": a.description or "",
                "isActive": a.is_active,
            }
            for a in agencies
        ]

    def get_agency_by_id(self, agency_id: str) -> Optional[Dict[str, Any]]:
        from .models import Agency
        from django.core.exceptions import ValidationError
        try:
            a = Agency.objects.filter(id=agency_id, is_active=True, deleted_at__isnull=True).first()
        except (ValidationError, ValueError):
            return None
        if not a:
            return None
        return {
            "id": str(a.id),
            "name": a.name,
            "acronym": a.acronym,
            "sphere": a.sphere,
            "description": a.description or "",
            "isActive": a.is_active,
        }

    def create_agency(self, data: Dict[str, Any]) -> Dict[str, Any]:
        from .models import Agency
        from django.db import IntegrityError
        from common.exceptions import ProblemDetailsException

        try:
            a = Agency.objects.create(
                name=data["name"].strip(),
                acronym=data["acronym"].strip().upper(),
                sphere=data.get("sphere", "state"),
                description=(data.get("description") or "").strip() or None,
                is_active=True,
            )
        except IntegrityError:
            raise ProblemDetailsException(
                detail="Já existe um órgão ativo cadastrado com esta sigla ou nome.",
                title="Órgão duplicado",
                status_code=409,
            )
        return {
            "id": str(a.id),
            "name": a.name,
            "acronym": a.acronym,
            "sphere": a.sphere,
            "description": a.description or "",
            "isActive": a.is_active,
        }

    def update_agency(self, agency_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        from .models import Agency
        from django.utils import timezone
        from django.core.exceptions import ValidationError
        try:
            a = Agency.objects.filter(id=agency_id, deleted_at__isnull=True).first()
        except (ValidationError, ValueError):
            return None
        if not a:
            return None
        if "name" in data:
            a.name = data["name"].strip()
        if "acronym" in data:
            a.acronym = data["acronym"].strip().upper()
        if "sphere" in data:
            a.sphere = data["sphere"].strip()
        if "description" in data:
            a.description = data["description"].strip()
        if "isActive" in data:
            a.is_active = bool(data["isActive"])
            if not a.is_active and not a.deleted_at:
                a.deleted_at = timezone.now()
        a.save()
        return {
            "id": str(a.id),
            "name": a.name,
            "acronym": a.acronym,
            "sphere": a.sphere,
            "description": a.description or "",
            "isActive": a.is_active,
        }

    def deactivate_agency(self, agency_id: str) -> Optional[Dict[str, Any]]:
        return self.update_agency(agency_id, {"isActive": False})

    @staticmethod
    def _serialize_unit(u, opening_hours_map: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        uid = str(u.id)
        zip_digits = u.zip_code or ""
        cep_formatted = f"{zip_digits[:5]}-{zip_digits[5:]}" if len(zip_digits) == 8 else zip_digits
        hours = (opening_hours_map or {}).get(uid, "08:00 às 17:00 (Seg a Sex)")
        return {
            "id": uid,
            "agencyId": str(u.agency_id),
            "name": u.name,
            "cep": cep_formatted,
            "zipCode": zip_digits,
            "street": u.street,
            "number": u.address_number,
            "neighborhood": u.neighborhood,
            "city": u.city,
            "state": u.state,
            "phone": u.phone or "",
            "email": u.email or "",
            "openingHours": hours,
            "dailyLimit": u.daily_limit,
            "dailyCapacity": u.daily_limit,
            "latitude": float(u.latitude) if u.latitude is not None else None,
            "longitude": float(u.longitude) if u.longitude is not None else None,
            "isPcdAccessible": bool(u.is_accessible),
            "hasPriorityService": bool(u.has_priority_service),
            "isActive": u.is_active,
        }

    def get_units(self, agency_id: Optional[str] = None) -> List[Dict[str, Any]]:
        from .models import Unit, UnitOpeningHour
        from django.core.exceptions import ValidationError

        qs = Unit.objects.filter(is_active=True, deleted_at__isnull=True).select_related("agency").order_by("name")
        if agency_id:
            try:
                qs = qs.filter(agency_id=agency_id)
            except (ValidationError, ValueError):
                return []
        units = list(qs)
        unit_ids = [u.id for u in units]
        hours_map: Dict[str, str] = {}
        if unit_ids:
            for oh in UnitOpeningHour.objects.filter(unit_id__in=unit_ids).order_by("weekday"):
                uid = str(oh.unit_id)
                if uid not in hours_map:
                    hours_map[uid] = f"{oh.opens_at.strftime('%H:%M')} às {oh.closes_at.strftime('%H:%M')} (Seg a Sex)"
        return [self._serialize_unit(u, hours_map) for u in units]

    def get_unit_by_id(self, unit_id: str) -> Optional[Dict[str, Any]]:
        from .models import Unit, UnitOpeningHour
        from django.core.exceptions import ValidationError
        try:
            u = Unit.objects.filter(id=unit_id, is_active=True, deleted_at__isnull=True).first()
        except (ValidationError, ValueError):
            return None
        if not u:
            return None
        oh = UnitOpeningHour.objects.filter(unit=u).order_by("weekday").first()
        hours_map = {}
        if oh:
            hours_map[str(u.id)] = f"{oh.opens_at.strftime('%H:%M')} às {oh.closes_at.strftime('%H:%M')} (Seg a Sex)"
        return self._serialize_unit(u, hours_map)

    def create_unit(self, data: Dict[str, Any]) -> Dict[str, Any]:
        import datetime as dt
        from .models import Agency, Unit, UnitOpeningHour
        from django.db import transaction
        from common.exceptions import ProblemDetailsException

        agency = Agency.objects.filter(id=data["agencyId"], deleted_at__isnull=True).first()
        if not agency:
            raise ProblemDetailsException(
                detail="Órgão informado para a unidade não foi encontrado.",
                title="Órgão inválido",
                status_code=400,
            )

        with transaction.atomic():
            u = Unit.objects.create(
                agency=agency,
                name=data["name"].strip(),
                zip_code=data["zipCode"],
                street=data["street"].strip(),
                address_number=data.get("number", "S/N").strip()[:10],
                neighborhood=data.get("neighborhood", "Centro").strip(),
                city=data.get("city", "Maceió").strip(),
                state=data.get("state", "AL").strip().upper()[:2],
                phone=data.get("phone") or None,
                email=data.get("email") or None,
                latitude=Decimal(str(data["latitude"])) if data.get("latitude") is not None else None,
                longitude=Decimal(str(data["longitude"])) if data.get("longitude") is not None else None,
                is_accessible=bool(data.get("isPcdAccessible", True)),
                has_priority_service=bool(data.get("hasPriorityService", True)),
                daily_limit=int(data.get("dailyLimit", 60)),
                is_active=True,
            )
            for weekday in range(1, 6):
                UnitOpeningHour.objects.create(
                    unit=u,
                    weekday=weekday,
                    opens_at=dt.time(8, 0),
                    closes_at=dt.time(17, 0),
                )
        return self._serialize_unit(u)

    def update_unit(self, unit_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        from .models import Unit
        from django.utils import timezone
        from django.core.exceptions import ValidationError

        try:
            u = Unit.objects.filter(id=unit_id, deleted_at__isnull=True).first()
        except (ValidationError, ValueError):
            return None
        if not u:
            return None
        if "name" in data:
            u.name = data["name"].strip()
        if "dailyLimit" in data:
            u.daily_limit = int(data["dailyLimit"])
        if "isPcdAccessible" in data:
            u.is_accessible = bool(data["isPcdAccessible"])
        if "hasPriorityService" in data:
            u.has_priority_service = bool(data["hasPriorityService"])
        if "isActive" in data:
            u.is_active = bool(data["isActive"])
            if not u.is_active and not u.deleted_at:
                u.deleted_at = timezone.now()
        u.save()
        return self._serialize_unit(u)

    def deactivate_unit(self, unit_id: str) -> Optional[Dict[str, Any]]:
        return self.update_unit(unit_id, {"isActive": False})

    @staticmethod
    def _serialize_service(
        s,
        agency_info: Optional[Dict[str, str]] = None,
        units_info: Optional[List[Any]] = None,
        steps_list: Optional[List[Any]] = None,
        docs_list: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:
        agency = agency_info or {}
        units = units_info or []
        cities = sorted({u.city for u in units if getattr(u, "city", None)})
        steps = [
            {
                "stepOrder": step.step_order,
                "stepNumber": step.step_order,
                "title": step.title,
                "description": step.description,
                "estimatedTime": step.estimated_time or "",
            }
            for step in (steps_list or [])
        ]
        documents = [
            {
                "id": str(doc.id),
                "name": doc.name,
                "isRequired": bool(doc.is_mandatory),
                "description": doc.template_url or "",
                "sampleUrl": doc.template_url or None,
            }
            for doc in (docs_list or [])
        ]
        cost_float = float(s.cost_amount) if s.cost_amount is not None else None
        deadline_days = int(s.average_deadline_days or 0)
        desc = s.detailed_description or ""
        return {
            "id": str(s.id),
            "name": s.name,
            "summary": desc[:160] + ("..." if len(desc) > 160 else ""),
            "description": desc,
            "category": category_slug_to_label(s.category),
            "categorySlug": s.category,
            "channel": s.channel,
            "agencyId": agency.get("id", ""),
            "agencyAcronym": agency.get("acronym", "SOSP"),
            "agencyName": agency.get("name", "Governo de Alagoas"),
            "isFree": bool(s.is_free),
            "costAmount": cost_float,
            "cost": "Gratuito" if s.is_free else (f"R$ {cost_float:.2f}" if cost_float is not None else "Pago"),
            "averageDeadlineDays": deadline_days,
            "estimatedDuration": "Imediato" if deadline_days == 0 else f"{deadline_days} dias úteis",
            "whoCanUse": s.eligibility or "Cidadãos residentes em Alagoas.",
            "targetAudience": s.eligibility or "Cidadãos residentes em Alagoas.",
            "prerequisites": s.prerequisites or "",
            "externalUrl": s.external_url or None,
            "updatedAt": s.updated_at.isoformat() if s.updated_at else "",
            "unitCount": len(units),
            "cities": cities,
            "steps": steps,
            "documents": documents,
            "isActive": s.status == "active",
        }

    def get_services(self) -> List[Dict[str, Any]]:
        from .models import Service, ServiceAgency, UnitService, ServiceStep, ServiceDocument

        services = list(Service.objects.filter(status="active", deleted_at__isnull=True).order_by("name"))
        if not services:
            return []
        svc_ids = [s.id for s in services]

        agency_by_svc: Dict[Any, Dict[str, str]] = {}
        for sa in ServiceAgency.objects.filter(service_id__in=svc_ids).select_related("agency"):
            if sa.service_id not in agency_by_svc and sa.agency:
                agency_by_svc[sa.service_id] = {
                    "id": str(sa.agency.id),
                    "acronym": sa.agency.acronym,
                    "name": sa.agency.name,
                }

        units_by_svc: Dict[Any, List[Any]] = {}
        for us in UnitService.objects.filter(service_id__in=svc_ids, is_active=True).select_related("unit"):
            if us.unit and us.unit.is_active and us.unit.deleted_at is None:
                units_by_svc.setdefault(us.service_id, []).append(us.unit)

        steps_by_svc: Dict[Any, List[Any]] = {}
        for st in ServiceStep.objects.filter(service_id__in=svc_ids).order_by("step_order"):
            steps_by_svc.setdefault(st.service_id, []).append(st)

        docs_by_svc: Dict[Any, List[Any]] = {}
        for doc in ServiceDocument.objects.filter(service_id__in=svc_ids).order_by("name"):
            docs_by_svc.setdefault(doc.service_id, []).append(doc)

        return [
            self._serialize_service(
                s,
                agency_info=agency_by_svc.get(s.id),
                units_info=units_by_svc.get(s.id),
                steps_list=steps_by_svc.get(s.id),
                docs_list=docs_by_svc.get(s.id),
            )
            for s in services
        ]

    def get_service_by_id(self, service_id: str) -> Optional[Dict[str, Any]]:
        from .models import Service, ServiceAgency, UnitService, ServiceStep, ServiceDocument
        from django.core.exceptions import ValidationError
        try:
            s = Service.objects.filter(id=service_id, deleted_at__isnull=True).first()
        except (ValidationError, ValueError):
            return None
        if not s:
            return None
        sa = ServiceAgency.objects.filter(service=s).select_related("agency").first()
        agency_info = (
            {"id": str(sa.agency.id), "acronym": sa.agency.acronym, "name": sa.agency.name}
            if sa and sa.agency
            else {}
        )
        units = [
            us.unit
            for us in UnitService.objects.filter(service=s, is_active=True).select_related("unit")
            if us.unit and us.unit.is_active and us.unit.deleted_at is None
        ]
        steps = list(ServiceStep.objects.filter(service=s).order_by("step_order"))
        docs = list(ServiceDocument.objects.filter(service=s).order_by("name"))
        return self._serialize_service(
            s,
            agency_info=agency_info,
            units_info=units,
            steps_list=steps,
            docs_list=docs,
        )

    def create_service(self, data: Dict[str, Any], created_by_id: Optional[str] = None) -> Dict[str, Any]:
        from .models import Agency, Unit, Service, ServiceAgency, UnitService
        from django.db import transaction
        from common.exceptions import ProblemDetailsException

        agency = Agency.objects.filter(id=data["agencyId"], deleted_at__isnull=True).first()
        if not agency:
            raise ProblemDetailsException(
                detail="Órgão informado para o serviço não foi encontrado.",
                title="Órgão inválido",
                status_code=400,
            )

        is_free = bool(data.get("isFree", True))
        cost_val = None if is_free else Decimal(str(round(float(data.get("costAmount") or 0), 2)))
        cat_slug = normalize_category_slug(data.get("category", "documents"))

        channel = data.get("channel", "inPerson")
        ext_url = (data.get("externalUrl") or "").strip() or None
        if channel in ("online", "hybrid") and (not ext_url or not ext_url.startswith("https://")):
            ext_url = "https://sosp.al.gov.br"

        with transaction.atomic():
            s = Service.objects.create(
                name=data["name"].strip(),
                category=cat_slug,
                detailed_description=data["description"].strip(),
                eligibility=data.get("whoCanUse", "Cidadãos residentes em Alagoas.").strip(),
                prerequisites=(data.get("prerequisites") or "").strip() or None,
                is_free=is_free,
                cost_amount=cost_val,
                average_deadline_days=int(data.get("averageDeadlineDays", 5)),
                channel=channel,
                external_url=ext_url,
                status="active",
                created_by_id=created_by_id if created_by_id and len(str(created_by_id)) == 36 else None,
            )
            ServiceAgency.objects.create(service=s, agency=agency)
            agency_units = list(Unit.objects.filter(agency=agency, is_active=True, deleted_at__isnull=True))
            for u in agency_units:
                UnitService.objects.create(unit=u, service=s, is_active=True)

        return self.get_service_by_id(str(s.id)) or self._serialize_service(s)

    def update_service(self, service_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        from .models import Service
        from django.utils import timezone
        from django.core.exceptions import ValidationError

        try:
            s = Service.objects.filter(id=service_id, deleted_at__isnull=True).first()
        except (ValidationError, ValueError):
            return None
        if not s:
            return None
        if "name" in data:
            s.name = data["name"].strip()
        if "category" in data:
            s.category = normalize_category_slug(data["category"])
        if "channel" in data:
            s.channel = data["channel"]
        if "description" in data:
            s.detailed_description = data["description"].strip()
        if "whoCanUse" in data:
            s.eligibility = data["whoCanUse"].strip()
        if "isFree" in data:
            s.is_free = bool(data["isFree"])
            if s.is_free:
                s.cost_amount = None
        if "costAmount" in data and not s.is_free and data["costAmount"] is not None:
            s.cost_amount = Decimal(str(round(float(data["costAmount"]), 2)))
        if "averageDeadlineDays" in data:
            s.average_deadline_days = int(data["averageDeadlineDays"])
        if "isActive" in data:
            if not bool(data["isActive"]):
                s.status = "inactive"
                if not s.deleted_at:
                    s.deleted_at = timezone.now()
            else:
                s.status = "active"
        s.save()
        return self.get_service_by_id(str(s.id)) or self._serialize_service(s)

    def deactivate_service(self, service_id: str) -> Optional[Dict[str, Any]]:
        return self.update_service(service_id, {"isActive": False})

    def get_categories(self) -> List[str]:
        from .models import Service
        cats = Service.objects.filter(status="active", deleted_at__isnull=True).values_list("category", flat=True).distinct()
        result = ["Todos"]
        result.extend(sorted({category_slug_to_label(c) for c in cats if c}))
        return result

    def list_faqs(self) -> List[Dict[str, Any]]:
        from .models import Faq
        try:
            qs = Faq.objects.filter(is_active=True).order_by("-created_at")
            return [
                {
                    "id": str(f.id),
                    "category": category_slug_to_label(f.category or "general"),
                    "question": f.question,
                    "answer": f.answer,
                }
                for f in qs
            ]
        except Exception:
            return []


def get_catalog_repository():
    from django.conf import settings
    if getattr(settings, "REPOSITORY_BACKEND", "memory") == "orm":
        return CatalogDjangoORMRepository()
    return _catalog_memory_repository


class CatalogRepositoryProxy:
    """Proxy dinâmico que seleciona a implementação configurada (memory ou orm)."""
    def __getattr__(self, name):
        repo = get_catalog_repository()
        return getattr(repo, name)


catalog_repository = CatalogRepositoryProxy()
