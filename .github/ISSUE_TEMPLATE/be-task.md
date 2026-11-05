---
name: "⚙️ Task de Back-end ([BE] [RFXXX])"
about: "Criação de card de Back-end (Django 5 + DRF / PostgreSQL 17 / Celery) seguindo o padrão ADR-004"
title: "[BE] [RFXXX] <Título do Requisito> (Essencial | Importante | Desejável)"
labels: ["backend", "api"]
assignees: []
---

## 1. Identificação da Task (`ADR-004`)

- **Responsável Principal:** Arthur Franco (Tech Lead / Back-end / DevOps)
- **Requisito Funcional (`RF`):** `RF-XX` ([`docs/01-product-specs.md`](../../docs/01-product-specs.md))
- **Caso de Uso (`UC`):** `UC-XX` ([`docs/use-cases/README.md`](../../docs/use-cases/README.md))
- **Módulo(s) de Domínio (`Pilar 3`):** `accounts | catalog | search | guidance | scheduling | feedback | notifications | reports | audit`
- **Branch Oficial:** `feat/be/rfxxx-<slug>`

## 2. Tabelas SQL e Contrato OpenAPI (`Pilar 4`)

- **Tabelas em `docs/database/schema.sql` (`camelCase`):** 
- **Rotas em `docs/api/openapi.yaml` (`/api/v1/...`):** 
- **Regras de Negócio (`RN-01` a `RN-40`) e Segurança (`RS-01` a `RS-05`):** 

## 3. Critérios de Aceite e Checklist `[BE]`

- [ ] Models mapeados em `camelCase` (`db_table` / `db_column`) idênticos ao `schema.sql` (`ADR-002`)
- [ ] Regras de negócio isoladas em `services.py` e leituras em `selectors.py` (sem import cruzado de `models.py` — `ADR-001`)
- [ ] Autorização RBAC aplicada (`ADR-003`) e escopo por órgão/cidadão validado
- [ ] Exclusão lógica (`isActive=False` / `deletedAt`) e gravação em `auditEvent` (`RN-39`, `RN-40`)
- [ ] Respostas de erro no formato `RFC 7807` (`application/problem+json`) com mensagens literais em português
- [ ] Testes unitários e de integração (`pytest`) cobrindo fluxo principal, alternativos e exceções (`≥ 80%` cobertura)

