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

---

## 2. Encapsulamento (Value Objects e Invariantes Protegidas)

O Encapsulamento garante que dados críticos não sejam manipulados como strings ou dicionários soltos sem validação. Toda mutação e acesso a estados internos é controlado:

- **Arquivo:** `backend/common/domain/value_objects.py`
  - **`CpfDocument`:**
    - Atributo privado `_digits`: mantém o estado interno encapsulado.
    - Validação de invariantes no construtor `__init__`: rejeita sequências inválidas e confere matematicamente os dois dígitos verificadores antes de instanciar o objeto.
    - Propriedades somente leitura (`@property`):
      - `clean_value`: retorna os 11 dígitos numéricos limpos.
      - `formatted`: formata no padrão `XXX.XXX.XXX-XX`.
      - `masked`: mascara dados sensíveis conforme LGPD (`***.XXX.XXX-**`).
  - **`RegistrationNumber`:**
    - Encapsula a matrícula funcional de servidores (ex.: `202XXXXX`, `SSP-1001`).
    - Atributo privado `_value`, validação por regex `^[A-Za-z0-9-]{4,20}$` e extração protegida de prefixo institucional via `@property prefix`.
  - **`ProtocolCode`:**
    - Encapsula o formato determinístico `AAAAMMDD-XXXX` (RN-20).
    - Validação de data e extração de propriedades (`year`, `month`, `day`, `sequence_number`).

---

## 3. Herança (Especialização de Comportamento)

A Herança estabelece relações "é-um" (is-a) entre classes, reaproveitando comportamentos compartilhados e especializando implementações:

- **Repositórios de Persistência:**
  - `CitizenInMemoryRepository(AbstractRepository)` herda de `AbstractRepository` para prover persistência em memória volátil com dados seed.
  - `CitizenDjangoORMRepository(AbstractRepository)` herda de `AbstractRepository` para prover persistência transacional real no PostgreSQL via Django ORM.
  - Arquivo: `backend/apps/accounts/repositories.py`.
- **Framework Django / DRF:**
  - Todos os models de domínio (`Citizen`, `InternalUser`, `Service`, `Appointment`) herdam de `django.db.models.Model` e `CompositeKeyModel`.
  - Todas as views de API herdam de `rest_framework.views.APIView`.
  - Todas as políticas de segurança (`IsCitizen`, `IsServerUser`, `IsManagerUser`) herdam de `BasePermission`.

---

## 4. Polimorfismo (Múltiplas Formas e Inversão de Controle)

O Polimorfismo permite que o sistema trate diferentes implementações de maneira uniforme através de uma mesma interface:

- **Repositórios Intercambiáveis via Proxy:**
  - `CitizenRepositoryProxy` e `SchedulingRepositoryProxy`:
    As camadas de serviço (`AccountService`, `SchedulingService`) chamam métodos como `.get_by_id()` ou `.save()` sem saber se o repositório em execução é o repositório em memória (`CitizenInMemoryRepository`) ou o repositório ORM de produção (`CitizenDjangoORMRepository`).
  - O sistema responde dinamicamente de acordo com a variável de ambiente `REPOSITORY_BACKEND` ("memory" ou "orm"), comportando-se polimorficamente sem alterar nenhuma linha da camada de serviço.
- **Exportadores de Relatório:**
  - Estratégias polimórficas de exportação (`CsvExporter` e `PdfExporter`), ambas respondendo à interface de exportação com formatação especializada.

