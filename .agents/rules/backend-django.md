---
trigger: always_on
description: Regras de Back-end Django 5 + DRF, PostgreSQL 17 em camelCase, RBAC, RFC 7807 e auditoria para o SOSP.
---

# Rules de Back-end, Banco de Dados e API — SOSP (`Django 5 + DRF`)

> **Escopo:** Diretório `backend/`, migrações, schema SQL, workers Celery e contrato OpenAPI do SOSP.
> **Responsável Principal:** Arthur Franco (Tech Lead, Back-end e DevOps).

---

## 1. Arquitetura de Monólito Modular (`ADR-001` e `Pilar 3`)

1. **Os 9 Módulos de Domínio:**
   - `accounts` (Cidadãos, usuários internos, autenticação CPF + Argon2id, sessões, RBAC)
   - `catalog` (Órgãos, unidades de atendimento, catálogo de serviços, documentos, etapas, versionamento)
   - `search` (Busca full-text PostgreSQL `tsvector` + `unaccent`, filtros combináveis e log anônimo de busca)
   - `guidance` (Guia passo a passo, progresso de checklist por CPF, geração de PDF assíncrono)
   - `scheduling` (Cálculo de slots de 30 min, reserva atômica com `Idempotency-Key`, protocolos `AAAAMMDD-XXXX`, linha do tempo e anexos S3)
   - `feedback` (Avaliações 1–5 estrelas na `v2.0` sob `FEATURE_REVIEWS_ENABLED`)
   - `notifications` (E-mail transacional no MVP; Push/SMS/WhatsApp na `v2.0`)
   - `reports` (Relatórios gerenciais agregados por órgão/unidade/período e exportação CSV/PDF)
   - `audit` (Trilha de auditoria imutável `auditEvent` e solicitações LGPD `auditDataSubjectRequest`)

2. **Fronteira Estrita entre Módulos (Proibido Importar `models.py` Cruzado):**
   - Um módulo **jamais** faz `from apps.<outro_modulo>.models import ...`.
   - Toda leitura entre módulos deve passar por funções públicas em `selectors.py`.
   - Toda mutação/regra de negócio deve residir em `services.py` (views e serializers apenas validam entrada/saída e chamam `services` ou `selectors`).

---

## 2. Banco de Dados `PostgreSQL 17` em `camelCase` (`ADR-002`, `ADR-008`)

1. **Alinhamento Fiel ao `docs/database/schema.sql`:**
   - Todos os nomes de tabelas e colunas seguem `camelCase` sem aspas duplas (ex.: `accountsCitizen`, `catalogService`, `schedulingAppointment`, `citizenId`, `serviceId`, `createdAt`, `updatedAt`, `deletedAt`).
   - Em todo Model do Django, defina explicitamente `db_table` no `Meta` e `db_column` nos campos com chaves estrangeiras ou nomes compostos para espelhar exatamente o [`docs/database/schema.sql`](../../docs/database/schema.sql).
2. **Exclusão Lógica Obrigatória (`RN-40`, `RS-05`):**
   - Nenhum registro de negócio pode sofrer `DELETE` físico no banco.
   - Utilize sempre desativação lógica (`isActive = False`, `deletedAt = timezone.now()`) e filtre registros ativos por padrão nos `selectors.py`.
3. **Auditoria Transversal (`RN-39`, `RS-03`):**
   - Toda operação de criação, edição, publicação de versão ou desativação administrativa deve gravar um registro em `auditEvent` contendo `actorUserId` (ou `actorCitizenId`), `action`, `targetTable`, `targetId`, `beforeState`, `afterState`, `ipAddress` e `createdAt` dentro da mesma transação.

---

## 3. Segurança, Autenticação e Autorização (`ADR-003`, `RS-01` a `RS-05`)

1. **Hash de Senha e Proteção de Sessão (`RF-01`, `RF-02`):**
   - Utilize `Argon2PasswordHasher` (`Argon2id + salt`) como hasher primário do Django.
   - Bloqueie o login por **5 minutos** após **5 tentativas inválidas** (`RN-29`).
   - Expire sessões após **30 minutos de inatividade** (`RN-28`).
2. **RBAC e Escopo de Dados (`RS-01`, `RS-03`, `RN-35`, `RN-36`):**
   - **Cidadão:** acessa apenas seus próprios agendamentos, protocolos e checklists filtrados por `citizenId` (retornar `404` em vez de `403` ao tentar acessar protocolo de terceiro para evitar enumeração — `STRIDE`).
   - **Servidor:** opera apenas sobre protocolos, agendamentos e relatórios do seu `agencyId`/`unitId` de lotação (`RN-36`). Só pode editar serviços se possuir `canManageCatalog = True` (`RN-35`).
   - **Administrador / Super Administrador:** gerencia órgãos, unidades, catálogo global, FAQ e usuários internos conforme matriz RBAC do `ADR-003`.
3. **Uploads Seguros (`ADR-006`, `RS-04`, `RN-25`):**
   - Anexos de protocolo aceitam apenas `.jpg`, `.png` e `.pdf` até **10 MB** (avatar do cidadão: `.jpg`/`.png` até **2 MB**), validando magic bytes, verificação antivírus (`ClamAV`) e armazenamento em bucket privado S3/MinIO com acesso via URL pré-assinada de curta duração.

---

## 4. Contratos REST, Idempotência, Filas e Erros (`Pilar 4`, `ADR-005`)

1. **Erros Padronizados em `RFC 7807` (`application/problem+json`):**
   - Toda resposta `4xx` ou `5xx` deve retornar `type`, `title`, `status`, `detail`, `instance`, `traceId` e, quando houver erro de validação de campos, a lista `errors: [{ field, message }]` usando **exatamente as mensagens literais em português** definidas no requisito.
2. **Transação Atômica e Fila Assíncrona (`RF-08`, `ADR-005`):**
   - Em `POST /api/v1/appointments`, exija o header `Idempotency-Key`, valide que o cidadão não possui outro agendamento ativo para o mesmo serviço (`RN-21`), verifique a vaga no slot de 30 min e o limite diário da unidade com lock transacional, gere o protocolo `AAAAMMDD-XXXX` (`RN-20`) e enfileire a geração de PDF e envio de e-mail no Celery/Redis **somente dentro de `transaction.on_commit()`**.
3. **Paginação Padrão (`RN-05`):**
   - Todas as listagens paginadas retornam **10 registros por página** com metadados `page`, `pageSize` (`10`), `totalItems` e `totalPages`.

