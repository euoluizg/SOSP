# SOSP — Relatório Consolidado de Auditoria e Conformidade de Requisitos

**Documento Auditado:** [`docs/Documento_de_Requisitos_SOSP_Final.pdf`](../Documento_de_Requisitos_SOSP_Final.pdf) (CESMAC – Engenharia de Software)  
**Data da Auditoria:** 09/11/2026  
**Ambiente de Staging:** Frontend: `https://portal.sosp.workers.dev` | Backend: `https://sosp-backend-staging.onrender.com` | Banco: Supabase PostgreSQL 17  
**Branch de Documentação:** `docs/requirements-compliance-audit` (baseada em `origin/develop` no commit `ceec994`)  
**Responsável:** Equipe Multiagente SOSP sob Supervisão Humana  

---

## 1. Resumo Executivo e Indicadores em 3 Níveis

A presente auditoria realizou uma varredura exaustiva no documento oficial de requisitos do SOSP ([`docs/Documento_de_Requisitos_SOSP_Final.pdf`](../Documento_de_Requisitos_SOSP_Final.pdf), 30 páginas), confrontando cada um dos **85 itens normativos** (14 Requisitos Funcionais, 17 Requisitos Não-Funcionais, 14 Requisitos de Segurança e 40 Regras de Negócio) com a implementação no frontend (`portal/`), no backend (`backend/`), no banco de dados (`docs/database/schema.sql`) e no contrato OpenAPI (`docs/api/openapi.yaml`).

Para garantir precisão técnica e transparência irrestrita, esta auditoria adota a separação estrita em **três níveis de conformidade**:
1. **Nível 1 — Conformidade Documental e Contratual:** O requisito está especificado de forma inequívoca nos documentos oficiais, ADRs e OpenAPI?
2. **Nível 2 — Implementação e Verificação Local:** O código-fonte está implementado e validado pela suíte automatizada local (139 testes no Django + 54 testes no Next.js)?
3. **Nível 3 — Homologação Real em STAGING:** O comportamento foi homologado de ponta a ponta na infraestrutura real de staging (Cloudflare Workers + Render + Supabase PostgreSQL 17 gerenciado)?

> [!IMPORTANT]
> **Critério de Rigor Técnico:** Nenhum requisito cuja validação dependa de persistência no PostgreSQL remoto, dados de seed institucionais ou execução das 12 jornadas completas no navegador é classificado como "Homologado em Staging". O status em Nível 3 permanece expressamente como **Pendente de Homologação em Staging** até a conclusão autorizada das **Tarefas 1 (DDL Supabase)**, **2 (Seed de Staging)** e **3 (E2E das 12 Jornadas)**.

---

### 1.1. Painel Consolidado de Métricas por Nível

```
================================================================================================
           PAINEL DE CONFORMIDADE NORMATIVA DO SOSP (85 ITENS AUDITADOS)
================================================================================================
  Nível 1: Conformidade Documental / Arquitetural    [ 85 / 85 ]  100,0%  CONFORME
  Nível 2: Implementação e Testes Locais (MVP)       [ 80 / 80 ]  100,0%  VERIFICADO LOCALMENTE
  Nível 3: Homologação Real em Staging               [  0 / 80 ]    0,0%  PENDENTE STAGING REAL
  Recursos Futuros Protegidos por Flag (v2.0)        [  4 / 85 ]    4,7%  DESATIVADOS (ADR-007)
  Processo de Homologação Externa Contratante        [  1 / 85 ]    1,2%  AGUARDA ACEITE FORMAL
================================================================================================
```

### 1.2. Quadro Quantitativo Detalhado por Categoria

| Categoria | Total de Itens | Nível 1: Documental | Nível 2: Implementado Local | Nível 3: Homologado Staging | Escopo v2.0 (ADR-007) | Processual / Externo |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Requisitos Funcionais (RF)** | 14 | 14 (100%) | 12 (100% MVP) | 0 (0% - Pendente E2E) | 2 (`RF010`, `RF013*`) | 0 |
| **Requisitos Não-Funcionais (RNF)** | 17 | 17 (100%) | 15 (100% MVP) | 0 (0% - Pendente Staging) | 1 (`RNF14*`) | 1 (`RNF16`) |
| **Requisitos de Segurança (RS)** | 14 | 14 (100%) | 14 (100% MVP) | 0 (0% - Pendente Staging DDL) | 0 | 0 |
| **Regras de Negócio (RN)** | 40 | 40 (100%) | 39 (100% MVP) | 0 (0% - Pendente Staging Seed) | 1 (`RN-37`) | 0 |
| **TOTAL GERAL** | **85** | **85 (100%)** | **80 (100% MVP)** | **0 (0%)** | **4 (4,7%)** | **1 (1,2%)** |

*\* Nota de Escopo: No `RF013` e `RNF14`, o canal de e-mail transacional faz parte do MVP (implementado e testado localmente). Os canais WhatsApp Business, SMS e Web Push pertencem à v2.0 e encontram-se desativados por feature flag.*

---

## 2. Metodologia de Classificação e Critérios dos 3 Níveis

### 2.1. Nível 1 — Conformidade Documental / Arquitetural
- **Critério:** O requisito está descrito com clareza nos documentos normativos ([`docs/Documento_de_Requisitos_SOSP_Final.pdf`](../Documento_de_Requisitos_SOSP_Final.pdf), [`docs/01-product-specs.md`](../01-product-specs.md)), possui decisão arquitetural registrada ([`docs/adr/`](../adr/)) e reflete fielmente o contrato de API ([`docs/api/openapi.yaml`](../api/openapi.yaml)) e o schema relacional ([`docs/database/schema.sql`](../database/schema.sql)).
- **Resultado:** **100,0% Conforme (85/85 itens)**. A especificação técnica cobre todos os 14 RFs, 17 RNFs, 14 RSs e 40 RNs sem omissões conceituais.

### 2.2. Nível 2 — Implementação e Verificação Local
- **Critério:** O código correspondente existe em `portal/` e `backend/`, respeita as convenções de arquitetura limpa e monólito modular (`ADR-001`, `ADR-002`, `ADR-003`), e passa com 100% de sucesso nas suítes automatizadas de testes locais (`pytest` e `vitest`).
- **Resultado:** **100,0% Verificado no MVP (80/80 itens aplicáveis)**:
  - 139 testes aprovados no backend (`cd backend && .venv/bin/pytest -q`);
  - 54 testes aprovados no frontend (`npm --prefix portal test`);
  - Typecheck sem erros (`tsc --noEmit`);
  - Django system check sem advertências (`python manage.py check`).

### 2.3. Nível 3 — Homologação Real em STAGING
- **Critério:** Execução real e verificável em ambiente integrado de STAGING com frontend em Cloudflare Workers (`portal.sosp.workers.dev`), backend no Render (`sosp-backend-staging.onrender.com`) e banco no Supabase PostgreSQL 17 (`aws-1-sa-east-1.pooler.supabase.com`).
- **Resultado:** **0,0% Homologado em Staging Real (0/80 itens)**.
- **Motivo do Bloqueio:** As etapas remotas dependem de autorização humana explícita conforme o protocolo `AGENTS.md` e regras de segurança:
  1. **Tarefa 1 (DDL Supabase):** Executar a criação das 34 tabelas, 2 views, extensões e funções (`sosp_security.authenticate_citizen_by_cpf`) no Supabase de staging;
  2. **Tarefa 2 (Seed de Staging):** Carga dos 5 serviços públicos, 3 unidades com expediente e usuário cidadão de teste (`11144477705`);
  3. **Tarefa 3 (Validação E2E das 12 Jornadas):** Execução automatizada e manual dos fluxos de cidadão, servidor e administrador no ambiente integrado.

---

## 3. Inventário de Dependências de Staging por Grupo de Requisitos

A tabela abaixo resume exatamente o que cada grupo de requisitos requer para atingir o status **Homologado em Staging**:

| Requisito / Grupo | Dependência Crítica de Staging | Objeto / Recurso no Supabase ou Staging | Impacto se não executado |
|---|---|---|---|
| **RF001, RF002, RN-01, RN-02, RN-26, RN-28, RN-29, RS001, RS002** | DDL do schema `sosp_security` e tabelas de contas; Seed do cidadão oficial. | `sosp_security.authenticate_citizen_by_cpf`, `accountsCitizen`, `accountsLoginAttempt` | Login e cadastro falharão no portal de staging por ausência de tabelas no banco. |
| **RF003, RF004, RN-31, RN-32** | DDL das tabelas de catálogo organizacional; Seed de Órgãos e Unidades. | `catalogAgency`, `catalogUnit`, `catalogUnitOpeningHour`, `catalogNonWorkingDay` | Telas de órgãos e unidades não listarão registros em staging. |
| **RF005, RF006, RN-03 a RN-09, RN-13, RN-33, RN-34** | DDL das tabelas de serviços e etapas; Índices `tsvector` para busca; Seed dos 5 serviços municipais. | `catalogService`, `catalogServiceStep`, `catalogServiceDocument`, `catalogServiceVersion`, `searchQueryLog` | Busca de serviços retornará lista vazia ou erro 500 no portal de staging. |
| **RF007, RN-10 a RN-12** | DDL das tabelas de checklist; Worker assíncrono para geração de PDF. | `guidanceProgress`, `guidanceGeneratedPdf` | Persistência de checklist por CPF e geração de PDF orientativo indisponíveis. |
| **RF008, RN-15, RN-18 a RN-24, RS010** | DDL de agendamento; Sequencial atômico de protocolos; Validação de limite diário. | `schedulingSlot`, `schedulingAppointment`, `schedulingProtocol` | Falha na emissão de agendamentos reais em staging. |
| **RF009, RN-25, RS005, RS011** | DDL de protocolos, histórico e anexos; Integração com MinIO / S3. | `schedulingProtocolTransition`, `schedulingProtocolAttachment` | Acompanhamento de protocolo e upload de documentos bloqueados em staging. |
| **RF011, RN-38** | DDL de FAQ e dúvidas; Seed inicial de perguntas frequentes. | `catalogFaq`, `feedbackQuestion` | Dúvidas autenticadas não serão salvas no banco. |
| **RF012, RN-35, RS012** | DDL de usuários internos e perfis; Seed de servidor e admin. | `accountsInternalUser`, `accountsInternalRole` | Acesso do servidor e do administrador impossibilitado em staging. |
| **RF014, RN-36** | DDL de exportações gerenciais; Agregação SQL por unidade e órgão. | `reportsExport`, view `schedulingUpcomingAppointmentsView` | Relatórios gerenciais sem dados reais agregados. |
| **RS008, RN-39, RN-40** | DDL da trilha de auditoria append-only; Trigger ou interceptor transacional. | `auditEvent`, `auditDataSubjectRequest` | Trilha de auditoria não persistida no banco remoto. |

---

## 4. Estado Atual das Branches, PRs e Histórico Git

1. **PR #27 e PR #28 Concluídos:**
   - O PR #27 (`feat/be/rf008-authorization-ownership-rbac`) foi incorporado em `develop` através do commit `ed17a1b`.
   - O PR #28 (`fix/be/rf008-authorization-scope-followup`), contendo a correção de escopo estrito de unidade para servidores (`RN-36`), modo fail-closed para servidores sem escopo e RBAC para gestores institucionais, foi aberto pelo `sosp-agents-bot[bot]` e mesclado em `develop` no commit `ceec994`.
2. **Sincronização Local:**
   - A branch local `develop` está perfeitamente alinhada com `origin/develop` no commit `ceec994`.
3. **Branch Atual de Auditoria:**
   - `docs/requirements-compliance-audit` criada a partir de `develop` (`ceec994`), incorporando o relatório e a matriz consolidada com o PDF oficial atualizado ([`docs/Documento_de_Requisitos_SOSP_Final.pdf`](../Documento_de_Requisitos_SOSP_Final.pdf)).

---

## 5. Próximos Passos e Transição para a Tarefa 1 (DDL Supabase Staging)

Com a consolidação documental e a auditoria em 3 níveis finalizada:

1. **Abertura do PR de Auditoria:**
   - Submissão da branch `docs/requirements-compliance-audit` e criação do Pull Request oficial pelo bot `sosp-agents-bot[bot]`, sem merge automático.
2. **Início da Preparação Local da Tarefa 1 (DDL Supabase Staging):**
   - Criação da branch `feat/be/supabase-ddl-prep` a partir de `develop`;
   - Análise estrita do [`docs/database/schema.sql`](../database/schema.sql);
   - Verificação das 34 tabelas e 2 views (`catalogActiveServicesView`, `schedulingUpcomingAppointmentsView`), todas em `camelCase` sem aspas duplas (`ADR-002`);
   - Verificação da segurança da função `sosp_security.authenticate_citizen_by_cpf` (`SECURITY DEFINER`, `search_path`, permissões mínimas);
   - Elaboração de scripts idempotentes e transacionais de pré-voo, aplicação e pós-voo;
   - **Garantia de segurança:** Nenhuma execução de escrita remota no Supabase de staging ocorrerá sem prévia aprovação humana explícita.
