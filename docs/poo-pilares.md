# Guia Didático: Aplicação dos 4 Pilares de POO no SOSP

Este documento foi elaborado para demonstrar e defender a aplicação prática dos **4 Pilares da Programação Orientada a Objetos** na camada de engenharia do projeto SOSP.

---

## 1. Abstração (Classes Abstratas e Contratos Formais)

A Abstração permite definir contratos claros para o sistema sem amarrar a regra de negócio a implementações de baixo nível:

- **Arquivo:** `backend/common/repositories.py`
  - `AbstractRepository(abc.ABC)` define o contrato abstrato formal obrigatório utilizando `@abc.abstractmethod` para os métodos essenciais de ciclo de vida de dados:
    - `get_by_id(entity_id: str) -> Optional[Dict[str, Any]]`
    - `list_all(**filters: Any) -> List[Dict[str, Any]]`
    - `save(data: Dict[str, Any]) -> Dict[str, Any]`
  - `BaseRepository(Protocol)` estabelece o protocolo de tipagem estática (structural typing) em Python para compatibilidade desacoplada.
- **Arquivo:** `backend/apps/reports/exporters.py`
  - `ReportExporter(abc.ABC)` define o contrato abstrato formal (`format_name`, `content_type`, `file_extension` e `export(summary) -> bytes`) para estratégias de exportação de relatórios gerenciais (`RF-14`).

---

## 2. Encapsulamento (Value Objects e Invariantes Protegidas)

O Encapsulamento garante que dados críticos não sejam manipulados como strings ou dicionários soltos sem validação. Toda mutação e acesso a estados internos é controlado:

- **Arquivo:** `backend/common/domain/value_objects.py` *(integrado em `backend/apps/accounts/services.py`, `backend/apps/scheduling/services.py` e `backend/apps/scheduling/repositories.py`)*
  - **`CpfDocument`:**
    - Atributo privado `_digits`: mantém o estado interno encapsulado.
    - Validação de invariantes no construtor `__init__`: rejeita sequências inválidas e confere matematicamente os dois dígitos verificadores antes de instanciar o objeto.
    - Propriedades somente leitura (`@property`):
      - `clean_value`: retorna os 11 dígitos numéricos limpos (usado em `AccountService.register_citizen` e `validate_cpf`).
      - `formatted`: formata no padrão `XXX.XXX.XXX-XX`.
      - `masked`: mascara dados sensíveis conforme LGPD (`***.XXX.XXX-**`, usado em `SchedulingDjangoORMRepository._to_dict`).
  - **`RegistrationNumber`:**
    - Encapsula a matrícula funcional de servidores (ex.: `202XXXXX`, `SSP-1001`).
    - Atributo privado `_value`, validação por regex `^[A-Za-z0-9-]{4,20}$` e extração protegida de prefixo institucional via `@property prefix` (usado em `AccountService.login_citizen` e `AccountService.create_internal_user`).
  - **`ProtocolCode`:**
    - Encapsula o formato determinístico `AAAAMMDD-XXXX` (RN-20).
    - Validação de data e extração de propriedades (`year`, `month`, `day`, `sequence_number`), usado em `SchedulingService.create_appointment` e `SchedulingService.get_protocol_timeline`.

---

## 3. Herança (Especialização de Comportamento)

A Herança estabelece relações "é-um" (is-a) entre classes, reaproveitando comportamentos compartilhados e especializando implementações:

- **Repositórios de Persistência:**
  - `CitizenInMemoryRepository(AbstractRepository)` e `CitizenDjangoORMRepository(AbstractRepository)` em `backend/apps/accounts/repositories.py`.
  - `SchedulingInMemoryRepository(AbstractRepository)` e `SchedulingDjangoORMRepository(AbstractRepository)` em `backend/apps/scheduling/repositories.py`.
- **Exportadores de Relatórios:**
  - `CsvExporter(ReportExporter)` e `PdfExporter(ReportExporter)` em `backend/apps/reports/exporters.py`.
- **Framework Django / DRF:**
  - Todos os models de domínio (`Citizen`, `InternalUser`, `Service`, `Appointment`) herdam de `django.db.models.Model` e `CompositeKeyModel`.
  - Todas as views de API herdam de `rest_framework.views.APIView`.
  - Todas as políticas de segurança (`IsCitizen`, `IsServerUser`, `IsManagerUser`) herdam de `BasePermission`.

---

## 4. Polimorfismo (Múltiplas Formas e Inversão de Controle)

O Polimorfismo permite que o sistema trate diferentes implementações de maneira uniforme através de uma mesma interface:

- **Repositórios Intercambiáveis via Proxy:**
  - `CitizenRepositoryProxy` e `SchedulingRepositoryProxy`:
    As camadas de serviço (`AccountService`, `SchedulingService`) chamam métodos como `.get_by_id()` ou `.save()` sem saber se o repositório em execução é o repositório em memória (`*InMemoryRepository`) ou o repositório ORM de produção (`*DjangoORMRepository`).
  - O sistema responde dinamicamente de acordo com a variável de ambiente `REPOSITORY_BACKEND` ("memory" ou "orm"), comportando-se polimorficamente sem alterar nenhuma linha da camada de serviço.
- **Exportadores de Relatório (`backend/apps/reports/exporters.py`):**
  - `ReportsService.create_export` resolve o exportador dinamicamente via `get_report_exporter(export_type)` e invoca `.export(summary)`, `.content_type` e `.build_filename()` polimorficamente sobre a interface `ReportExporter`, gerando CSV UTF-8 (`CsvExporter`) ou PDF 1.4 (`PdfExporter`).

