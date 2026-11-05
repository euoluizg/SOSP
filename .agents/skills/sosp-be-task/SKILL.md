---
name: sosp-be-task
description: >-
  Use this skill when the user asks to implement, update, or review a Back-end
  task ([BE] [RFXXX]), API endpoint, Django model, domain service, or Celery
  worker in the SOSP Django 5 + DRF backend (backend/). Guides the agent through
  PostgreSQL camelCase mapping, modular monolith boundaries, RBAC, RFC 7807 errors,
  auditEvent logging, and pytest verification.
---

# SOSP Back-end Task Workflow (`[BE] [RFXXX]`)

Esta skill define o procedimento passo a passo obrigatório para implementar qualquer task de Back-end (`[BE] [RFXXX]`) no servidor `Django 5 + Django REST Framework` (`backend/`) do projeto SOSP.

## Passo 1: Mapear Requisito, Tabelas SQL e Contrato OpenAPI

1. Leia o requisito (`RF-01` a `RF-14`) em [`docs/01-product-specs.md`](../../../docs/01-product-specs.md) e o Caso de Uso (`UC-01` a `UC-17`) em [`docs/use-cases/README.md`](../../../docs/use-cases/README.md).
2. Localize as tabelas envolvidas em [`docs/database/schema.sql`](../../../docs/database/schema.sql) e confira colunas, tipos, `CHECK` constraints, índices parciais (`WHERE deletedAt IS NULL`) e chaves estrangeiras.
3. Localize as rotas, parâmetros, payloads e códigos de resposta em [`docs/api/openapi.yaml`](../../../docs/api/openapi.yaml).
4. Identifique qual dos **9 módulos de domínio** ([`docs/03-architecture.md`](../../../docs/03-architecture.md)) é o dono da regra:
   - `accounts`, `catalog`, `search`, `guidance`, `scheduling`, `feedback`, `notifications`, `reports` ou `audit`.

## Passo 2: Implementar a Camada de Dados (`models.py`)

1. No módulo dono da entidade, crie ou atualize o Model em `models.py` seguindo estritamente o [`ADR-002`](../../../docs/adr/ADR-002-postgresql-camelcase.md):
   - Defina `db_table = '<nomeEmCamelCase>'` no `class Meta` (ex.: `accountsCitizen`, `catalogAgency`, `catalogUnit`, `catalogService`, `schedulingAppointment`, `schedulingProtocol`);
   - Mapeie cada coluna com `db_column='<colunaEmCamelCase>'` quando necessário para garantir 100% de compatibilidade com `docs/database/schema.sql`;
   - Inclua os campos de controle e exclusão lógica (`isActive`, `createdAt`, `updatedAt`, `deletedAt`).
2. **Proibido:** jamais importe `models.py` de outro módulo diretamente.

## Passo 3: Implementar Consultas (`selectors.py`) e Regras de Negócio (`services.py`)

1. **`selectors.py` (Leitura e Filtros):**
   - Implemente funções de consulta que filtram por padrão `deletedAt__isnull=True` (e `isActive=True` quando aplicável).
   - Aplique paginação de **10 registros por página** (`RN-05`) e ordenação oficial (por relevância no `RF-06` ou alfabética `A–Z` nos cadastros administrativos).
   - Aplique filtro de escopo organizacional (`RN-36`) quando o ator for `Servidor`.
2. **`services.py` (Escrita, Validações, Transações e Auditoria):**
   - Implemente todas as Regras de Negócio (`RN-01` a `RN-40`):
     - `RF-01`: validação de dígito verificador de CPF (`RN-26`), idade ≥ 12 anos, hash `Argon2id + salt`, consulta `ViaCEP` com fallback `IBGE` (`RN-27`);
     - `RF-02`: controle de 5 tentativas com bloqueio de 5 min (`RN-29`), sessão de 30 min (`RN-28`), código de 6 dígitos por 15 min (`RN-30`);
     - `RF-05`: criação de nova versão a cada edição (`RN-34`) e exigência dos 8 blocos + mín. 1 etapa + 1 documento obrigatório para ativar (`RN-07`, `RN-33`);
     - `RF-08`: geração de slots de 30 min (`RN-18`) descontando feriados/fechamentos (`RN-19`), bloqueio de agendamento duplicado para o mesmo CPF e serviço (`RN-21`), exigência de `Idempotency-Key`, geração atômica do protocolo `AAAAMMDD-XXXX` (`RN-20`), regra de 24h para remarcar/cancelar (`RN-22`) e disparo de jobs Celery (`PDF` + `e-mail`) via `transaction.on_commit()`.
   - **Exclusão Lógica (`RN-40`):** implemente desativação preenchendo `isActive = False` e `deletedAt = timezone.now()`.
   - **Auditoria (`RN-39`):** chame o serviço do módulo `audit` para gravar o evento em `auditEvent` (com `beforeState` e `afterState`) dentro da mesma transação.

## Passo 4: Implementar Serializers, Views e Permissões RBAC (`serializers.py`, `views.py`, `urls.py`)

1. Configure os serializers com campos em `camelCase` idênticos ao `openapi.yaml` e mensagens de validação literais em português.
2. Aplique as classes de permissão RBAC ([`ADR-003`](../../../docs/adr/ADR-003-autenticacao-govbr-rbac.md)):
   - Retorne `404 Not Found` (em vez de `403`) quando um cidadão tentar acessar protocolo/agendamento pertencente a outro `citizenId` (`RS-01`).
   - Verifique `canManageCatalog` quando um servidor tentar criar/editar serviços (`RN-35`).
   - Verifique se a feature flag (`ADR-007`) está ativa para rotas de `RF-10` (`FEATURE_REVIEWS_ENABLED`) e `RF-13` (`FEATURE_PUSH_ENABLED` / `SMS` / `WHATSAPP`), retornando `404` ou `503` em formato `RFC 7807` quando desabilitada.
3. Formate todas as exceções no padrão **`RFC 7807` (`application/problem+json`)**.

## Passo 5: Testes Automatizados (`pytest`)

1. Crie testes unitários e de integração em `tests/` cobrindo:
   - Fluxo principal (`200` / `201`);
   - Todos os fluxos alternativos e de exceção do Caso de Uso (`400`, `401`, `403`, `404`, `409`, `422`, `429`);
   - Verificação de gravação em `auditEvent` e preservação de exclusão lógica (`deletedAt`).
2. Execute `pytest` para validar que todos os testes passam e que a cobertura mínima (`≥ 80%` no back-end, `RNF-10`) é mantida.

