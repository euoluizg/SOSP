# SOSP — Sistema de Orientação para Serviços Públicos (Global Agent Rules)

Você está atuando no repositório oficial do **SOSP (Sistema de Orientação para Serviços Públicos)**, uma plataforma pública de orientação, checklist de documentos, agendamento presencial e acompanhamento de protocolos para cidadãos, servidores e administradores.

- **Equipe Oficial:**
  - **Product Owner (PO):** Mozart Melo
  - **Tech Lead, Back-end (`Django 5 + DRF`) e DevOps:** Arthur Franco
  - **Front-end (`Next.js 15`), UI/UX Design e QA:** Luiz Gustavo

---

## 1. Hierarquia Inegociável de Fontes de Verdade (Pilar 0)

Em qualquer conflito entre documentos, telas ou código, siga estritamente esta ordem de precedência:

1. **1º — Requisitos Funcionais, Não-Funcionais e de Segurança:** [`docs/01-product-specs.md`](docs/01-product-specs.md), [`docs/Documento_de_Requisitos_SOSP_Final.pdf`](docs/Documento_de_Requisitos_SOSP_Final.pdf) e [`docs/use-cases/README.md`](docs/use-cases/README.md).
2. **2º — Decisões Arquiteturais (ADRs):** [`docs/adr/ADR-001`](docs/adr/ADR-001-monolito-modular-django-nextjs.md) a [`docs/adr/ADR-008`](docs/adr/ADR-008-supabase-postgresql-gerenciado.md).
3. **3º — Contratos Técnicos Executáveis:** [`docs/api/openapi.yaml`](docs/api/openapi.yaml) (`OpenAPI 3.0.3`) e [`docs/database/schema.sql`](docs/database/schema.sql) (`PostgreSQL 17`).
4. **4º — Arquitetura e Engenharia:** [`docs/03-architecture.md`](docs/03-architecture.md), [`docs/04-data-api.md`](docs/04-data-api.md) e [`docs/05-engineering-devops.md`](docs/05-engineering-devops.md).
5. **5º — Design System e Protótipo Visual (Figma):** [`docs/02-design-ux.md`](docs/02-design-ux.md), [`docs/design/README.md`](docs/design/README.md) e [`docs/design/exports/`](docs/design/exports/).
   - **Atenção:** O Figma governa a **aparência visual**, mas sempre que houver divergência funcional ou de rótulo mapeada na **Matriz de Divergências (`D1–D13`)** em [`docs/01-product-specs.md#7-matriz-de-divergências`](docs/01-product-specs.md#7-matriz-de-divergências), **prevalece o requisito**.

---

## 2. Regras Críticas do Escopo do MVP

1. **Autenticação Local para Todos os Perfis (`RF-01`, `RF-02`, `ADR-003`):**
   - No MVP, **Cidadãos, Servidores e Administradores** autenticam-se localmente via **CPF + senha** com hash `Argon2id + salt`.
   - Bloqueio temporário de **5 minutos** após **5 tentativas falhas consecutivas** (`RN-29`).
   - Sessão expira após **30 minutos de inatividade** (`RN-28`).
   - Recuperação de senha via código de **6 dígitos enviado por e-mail**, válido por **15 minutos** (`RN-30`).
   - **Botão `"Entrar com Gov.br"` (`D10`):** Deve ser exibido na tela de login para demonstrar visão de produto, mas ao ser clicado **NÃO redireciona para OAuth externo**; abre exclusivamente um modal informativo com a mensagem literal:
     > *"A integração com o Gov.br estará disponível em uma futura atualização (v2.0). Utilize seu CPF e senha para entrar."*
     E botão `"Entendi, quero usar CPF e senha"`.

2. **Agendamento 100% Interno no SOSP (`RF-08`):**
   - Todo o ciclo de agendamento ocorre dentro do SOSP: cálculo de **slots de 30 minutos** (`RN-18`) dentro do expediente da unidade, desconto de feriados/dias sem atendimento (`RN-19`), controle de **limite diário compartilhado da unidade**, emissão de protocolo no formato **`AAAAMMDD-XXXX`** (`RN-20`), geração de comprovante em PDF, envio de e-mail transacional, remarcação/cancelamento até 24h antes (`RN-22`) e registro de **não comparecimento** pelo servidor.

3. **Feature Flags de Escopo v2.0 (`ADR-007`):**
   - **`RF-10` (Avaliação e Comentário)** e **`RF-13` (Notificações Push, SMS e WhatsApp)** pertencem à `v2.0` e permanecem desligados por padrão no MVP (`FEATURE_REVIEWS_ENABLED=false`, `FEATURE_PUSH_ENABLED=false`, `FEATURE_SMS_ENABLED=false`, `FEATURE_WHATSAPP_ENABLED=false`).
   - E-mail transacional (`RF-01`, `RF-02`, `RF-08`, `RF-09`) e exportação de relatórios CSV/PDF (`RF-14`, `FEATURE_REPORTS_EXPORT=true`) **fazem parte do MVP**.

4. **Exclusão Lógica e Auditoria (`RN-39`, `RN-40`, `RS-05`):**
   - **Jamais execute `DELETE` físico** em registros de negócio. Toda exclusão ou desativação é lógica (`isActive = false`, `deletedAt = NOW()`).
   - Toda operação administrativa ou mudança de estado relevante deve registrar evento imutável em `auditEvent` (ator, IP, timestamp, estado anterior e estado novo).

---

## 3. Convenções de Código, Idioma e Banco de Dados

- **Idioma:**
  - **Código-fonte, identificadores SQL, rotas REST, variáveis e funções:** Inglês (`EN`) em `camelCase`.
  - **Interface do usuário (UI), mensagens de erro/validação, comentários de negócio e documentação:** Português (`PT-BR`), respeitando literalmente as mensagens definidas no PDF de Requisitos (`RF001` a `RF014`).
- **PostgreSQL 17 em `camelCase` sem aspas (`ADR-002`, `ADR-008`):**
  - Todas as 34 tabelas e colunas em [`docs/database/schema.sql`](docs/database/schema.sql) utilizam `camelCase` sem aspas duplas (ex.: `accountsCitizen`, `citizenId`, `serviceId`, `createdAt`, `updatedAt`, `deletedAt`).
  - Nunca crie migrações ou tabelas em `snake_case`.
- **Monólito Modular (`ADR-001`):**
  - Repositório dividido em `portal/` (`Next.js 15` com App Router e TypeScript) e `backend/` (`Django 5 + Django REST Framework`).
  - O `portal/` **nunca** acessa o banco de dados diretamente (nem via SDK do Supabase); consome exclusivamente a API REST `/api/v1` do `backend/`.
  - Os 9 módulos de domínio do `backend/` são: `accounts`, `catalog`, `search`, `guidance`, `scheduling`, `feedback`, `notifications`, `reports` e `audit`. Um módulo **nunca** importa `models.py` de outro módulo (comunicação apenas via `services.py` e `selectors.py`).

---

## 4. Padrão de Branches, Tasks, Commits e PRs (`ADR-004`)

- **Tasks Pareadas por Requisito:**
  - Front-end (Luiz Gustavo): `[FE] [RFXXX] <Título> (<Prioridade>)` → branch `feat/fe/rfxxx-<slug>`
  - Back-end (Arthur Franco): `[BE] [RFXXX] <Título> (<Prioridade>)` → branch `feat/be/rfxxx-<slug>`
- **Commits (Conventional Commits):**
  - Formato: `<tipo>(<fe|be>/rfxxx): <descrição curta em português>` (ex.: `feat(fe/rf001): implementa formulário de cadastro do cidadão com ViaCEP`).
- **Regras detalhadas por camada:**
  - Para tarefas de Front-end (`portal/`), siga `.agents/rules/frontend-nextjs.md` e a skill `sosp-fe-task`.
  - Para tarefas de Back-end (`backend/`), siga `.agents/rules/backend-django.md` e a skill `sosp-be-task`.

---

## 5. Governança Multiagente, Supervisão Humana e as 3 Equipes (23 Agentes)

Este repositório opera com arquitetura multiagente coordenada por **Hermes Agent** (orquestrador principal) em conjunto com **Google Antigravity IDE** e **OpenCode CLI**, organizada em **3 equipes (23 agentes especialistas)** em `.agents/agents/` e `.opencode/agents/`:

### 5.1. Fluxo Operacional entre Equipes
`Usuário` → `Hermes Agent (multiagent-development-orchestrator)` → Líderes de Equipe (`react-cto`, `backend-lead`, `test-lead`) → Especialistas → Validação independente de `QA` → Consolidação e **Aprovação Humana Final**.

### 5.2. Catálogo das 3 Equipes (23 Agentes)
1. **Equipe Frontend — React / Next.js (8 agentes):**
   - `react-cto` (Líder técnico principal de Frontend), `software-architect`, `react-specialist`, `nextjs-specialist`, `ui-ux-engineer`, `backend-engineer` (BFF/Route Handlers/contratos TS), `qa-engineer`, `security-performance-engineer`.
2. **Equipe Backend — Django / PostgreSQL (8 agentes):**
   - `backend-lead` (Líder técnico e arquiteto Django), `django-api-engineer`, `django-domain-engineer`, `postgresql-data-architect`, `django-orm-migrations-engineer`, `backend-auth-security-engineer`, `backend-performance-engineer`, `backend-integration-engineer`.
3. **Equipe QA — Qualidade, Segurança e Performance (7 agentes):**
   - `test-lead` (Líder de QA e auditoria independente), `frontend-test-engineer`, `backend-api-tester`, `integration-e2e-engineer`, `database-test-engineer`, `security-tester`, `performance-engineer`.

### 5.3. Protocolo Obrigatório de Execução Supervisionada e Portões de Aprovação
- **Análise inicial somente leitura:** O diagnóstico inicial, inspeção de arquitetura e planejamento não devem alterar arquivos nem executar ações destrutivas.
- **Portões de aprovação humana explícita:** Antes de instalar software global, executar scripts remotos, instalar plugins comunitários, conectar contas/provedores, alterar credenciais, sobrescrever configurações existentes, executar migrações/seeds/alterações de banco, apagar dados, rodar testes de carga, fazer commit, push, abrir PR ou fazer deploy:
  1. Apresente o plano numerado com arquivos, comandos, ambiente, dependências, riscos e critérios de aceite;
  2. Solicite e aguarde autorização explícita do usuário (aprovação de outro agente não substitui a aprovação humana);
  3. Nunca enfraqueça ou apague testes para fazê-los passar e nunca declare build/teste aprovado sem execução real verificável (diferencie `CONCLUÍDO`, `VERIFICADO`, `NÃO EXECUTADO` e `BLOQUEADO`).
- **Segurança de Segredos:** Jamais leia, exponha, registre em logs ou commite tokens, chaves de API, senhas ou variáveis de `.env`.
- Consulte [`docs/agent-architecture.md`](docs/agent-architecture.md), [`docs/agent-workflow.md`](docs/agent-workflow.md) e [`docs/agent-model-matrix.md`](docs/agent-model-matrix.md) para detalhes completos.
