---
name: sosp-contract-db
description: >-
  Use this skill when the user asks to create, modify, audit, or synchronize
  the OpenAPI 3.0.3 contract (docs/api/openapi.yaml), the PostgreSQL 17 DDL
  schema (docs/database/schema.sql), or Pillar 4 (docs/04-data-api.md).
  Enforces camelCase unquoted SQL identifiers (ADR-002), RFC 7807 ProblemDetails,
  and feature flag metadata (ADR-007).
---

# SOSP Contract & Database Maintenance (`openapi.yaml` + `schema.sql`)

Use esta skill sempre que for necessário adicionar ou alterar tabelas/colunas em [`docs/database/schema.sql`](../../../docs/database/schema.sql) ou rotas/schemas em [`docs/api/openapi.yaml`](../../../docs/api/openapi.yaml).

## Passo 1: Regras para Alterações em `docs/database/schema.sql` (`PostgreSQL 17`)

1. **Identificadores `camelCase` sem aspas (`ADR-002`):**
   - Nomes de tabelas devem seguir o prefixo do módulo em `camelCase`: `accounts*`, `catalog*`, `search*`, `guidance*`, `scheduling*`, `feedback*`, `notifications*`, `reports*`, `audit*`.
   - Nomes de colunas, constraints e índices devem usar `camelCase` sem aspas duplas (`citizenId`, `serviceId`, `createdAt`, `updatedAt`, `deletedAt`).
2. **Colunas de Auditoria e Exclusão Lógica (`RN-40`):**
   - Toda tabela de entidade mutável deve possuir `isActive BOOLEAN NOT NULL DEFAULT TRUE`, `createdAt TIMESTAMPTZ NOT NULL DEFAULT NOW()`, `updatedAt TIMESTAMPTZ NOT NULL DEFAULT NOW()` e `deletedAt TIMESTAMPTZ NULL`.
   - Índices de unicidade de negócio devem ser parciais quando aplicável (`WHERE deletedAt IS NULL`).

## Passo 2: Regras para Alterações em `docs/api/openapi.yaml` (`OpenAPI 3.0.3`)

1. **Versão do Especificador:**
   - Mantenha sempre `openapi: 3.0.3` no topo do arquivo (compatível com `drf-spectacular` e validadores CI).
2. **Padronização de Rotas e Payloads:**
   - Todas as rotas públicas/autenticadas ficam sob `/api/v1/...`.
   - Propriedades JSON devem estar em `camelCase` (`citizenId`, `protocolNumber`, `pageSize`, `totalItems`).
   - Listagens paginadas devem usar `pageSize = 10` por padrão (`RN-05`).
   - Todas as respostas de erro (`400`, `401`, `403`, `404`, `409`, `422`, `429`, `500`) devem referenciar `#/components/schemas/ProblemDetails` (`application/problem+json` — `RFC 7807`).
3. **Feature Flags (`ADR-007`):**
   - Rotas de `RF-10` (Avaliação) e `RF-13` (Preferências/Notificações v2.0) devem incluir a extensão `x-feature-flag` indicando a flag correspondente (`FEATURE_REVIEWS_ENABLED`, `FEATURE_PUSH_ENABLED`, etc.) e estar refletidas no [`.env.example`](../../../.env.example).

## Passo 3: Sincronização Documental Obrigatória

1. Atualize [`docs/04-data-api.md`](../../../docs/04-data-api.md) se a contagem de tabelas, índices, endpoints ou regras de contrato mudar.
2. Registre a alteração em [`CHANGELOG.md`](../../../CHANGELOG.md).
3. Valide a sintaxe YAML do `docs/api/openapi.yaml` antes de encerrar.

