from typing import Any, Dict, List, Optional

class CatalogInMemoryRepository:
    def __init__(self):
        self._agencies: List[Dict[str, Any]] = [
            {
                "id": "orgao-ssp",
                "name": "Secretaria de Estado da Segurança Pública",
                "acronym": "SSP",
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

    def get_units(self, agency_id: Optional[str] = None) -> List[Dict[str, Any]]:
        units = [u for u in self._units if u.get("isActive", True)]
        if agency_id:
            units = [u for u in units if u.get("agencyId") == agency_id]
        return units

    def get_unit_by_id(self, unit_id: str) -> Optional[Dict[str, Any]]:
        for u in self._units:
            if u["id"] == unit_id:
                return u
        return None

    def get_services(self) -> List[Dict[str, Any]]:
        return [s for s in self._services if s.get("isActive", True)]

    def get_service_by_id(self, service_id: str) -> Optional[Dict[str, Any]]:
        for s in self._services:
            if s["id"] == service_id:
                return s
        return None

    def get_categories(self) -> List[str]:
        return self._categories

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
                "description": a.description or "",
                "isActive": a.is_active,
            }
            for a in agencies
        ]

    def get_agency_by_id(self, agency_id: str) -> Optional[Dict[str, Any]]:
        from .models import Agency
        a = Agency.objects.filter(id=agency_id, is_active=True, deleted_at__isnull=True).first()
        if not a:
            return None
        return {
            "id": str(a.id),
            "name": a.name,
            "acronym": a.acronym,
            "description": a.description or "",
            "isActive": a.is_active,
        }

    def get_units(self, agency_id: Optional[str] = None) -> List[Dict[str, Any]]:
        from .models import Unit
        qs = Unit.objects.filter(is_active=True, deleted_at__isnull=True).select_related("agency").order_by("name")
        if agency_id:
            qs = qs.filter(agency_id=agency_id)
        return [
            {
                "id": str(u.id),
                "agencyId": str(u.agency_id),
                "name": u.name,
                "street": u.street,
                "number": u.address_number,
                "neighborhood": u.neighborhood,
                "city": u.city,
                "state": u.state,
                "zipCode": u.zip_code,
                "phone": u.phone or "",
                "dailyCapacity": u.daily_limit,
                "latitude": float(u.latitude) if u.latitude is not None else None,
                "longitude": float(u.longitude) if u.longitude is not None else None,
                "isActive": u.is_active,
            }
            for u in qs
        ]

    def get_unit_by_id(self, unit_id: str) -> Optional[Dict[str, Any]]:
        from .models import Unit
        u = Unit.objects.filter(id=unit_id, is_active=True, deleted_at__isnull=True).first()
        if not u:
            return None
        return {
            "id": str(u.id),
            "agencyId": str(u.agency_id),
            "name": u.name,
            "street": u.street,
            "number": u.address_number,
            "neighborhood": u.neighborhood,
            "city": u.city,
            "state": u.state,
            "zipCode": u.zip_code,
            "phone": u.phone or "",
            "dailyCapacity": u.daily_limit,
            "latitude": float(u.latitude) if u.latitude is not None else None,
            "longitude": float(u.longitude) if u.longitude is not None else None,
            "isActive": u.is_active,
        }

    def get_services(self) -> List[Dict[str, Any]]:
        from .models import Service
        qs = Service.objects.filter(status="active", deleted_at__isnull=True).order_by("name")
        return [
            {
                "id": str(s.id),
                "name": s.name,
                "summary": s.detailed_description[:120] if s.detailed_description else "",
                "description": s.detailed_description,
                "category": s.category,
                "channel": s.channel,
                "cost": "Gratuito" if s.is_free else (f"R$ {s.cost_amount:.2f}" if s.cost_amount else "Pago"),
                "estimatedDuration": f"{s.average_deadline_days} dias" if s.average_deadline_days else "Imediato",
                "isActive": s.status == "active",
            }
            for s in qs
        ]

    def get_service_by_id(self, service_id: str) -> Optional[Dict[str, Any]]:
        from .models import Service, ServiceStep, ServiceDocument
        s = Service.objects.filter(id=service_id, deleted_at__isnull=True).first()
        if not s:
            return None
        steps = [
            {"stepNumber": step.step_order, "title": step.title, "description": step.description}
            for step in ServiceStep.objects.filter(service=s).order_by("step_order")
        ]
        documents = [
            {"name": doc.name, "isRequired": doc.is_mandatory, "description": doc.template_url or ""}
            for doc in ServiceDocument.objects.filter(service=s).order_by("name")
        ]
        return {
            "id": str(s.id),
            "name": s.name,
            "summary": s.detailed_description[:120] if s.detailed_description else "",
            "description": s.detailed_description,
            "category": s.category,
            "channel": s.channel,
            "cost": "Gratuito" if s.is_free else (f"R$ {s.cost_amount:.2f}" if s.cost_amount else "Pago"),
            "estimatedDuration": f"{s.average_deadline_days} dias" if s.average_deadline_days else "Imediato",
            "targetAudience": s.eligibility,
            "steps": steps,
            "documents": documents,
            "isActive": s.status == "active",
        }

    def get_categories(self) -> List[str]:
        from .models import Service
        cats = Service.objects.filter(status="active", deleted_at__isnull=True).values_list("category", flat=True).distinct()
        result = ["Todos"]
        result.extend(sorted(list(set(cats))))
        return result


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
