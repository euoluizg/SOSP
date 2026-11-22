# Matriz Individual de Modelos — Hermes + 23 Agentes (SOSP)

> **Projeto:** SOSP — Sistema de Orientação para Serviços Públicos
> **Data da Auditoria:** 05/11/2026
> **Ferramentas Auditadas:** Hermes Agent `v0.21.7+758.gd97007c`, OpenCode `v2.0.15` e Google Antigravity IDE.

---

## 1. Descoberta Real de Provedores e Modelos no Ambiente

Antes de configurar os modelos individuais, foram executadas verificações reais nos binários locais (`hermes auth status`, `opencode auth list`, `opencode models`, `opencode debug agents` e inspeção de `~/.hermes/provider_models_cache.json`):

| Ferramenta | Provedores Autenticados (`logged in` / `stored`) | Modelos Verificados no Catálogo Real | Formato Suportado pela Ferramenta |
|---|---|---|---|
| **Hermes Agent (`~/.hermes/config.yaml`)** | `nous` (`logged in` — ativo por padrão: modelo `BRAD`) e `copilot` (`logged in` no credential pool) | **Nous Portal:** `BRAD`<br/>**Copilot Pool:** `claude-opus-4.8`, `claude-sonnet-5`, `gemini-3.8-flash`, `gpt-4.1`, `gpt-4o`, `claude-haiku-4.5` | `model.default` + `model.provider` em `~/.hermes/config.yaml` ou flags `--provider` / `--model` por execução |
| **OpenCode (`v2.0.15` — `.opencode/agents/*.md`)** | `OpenRouter` (`stored`), `GitHub Copilot` (`stored`), `figma` (`stored`) | `openrouter/anthropic/claude-opus-4.6`<br/>`openrouter/anthropic/claude-sonnet-4.6`<br/>`openrouter/anthropic/claude-sonnet-4.5`<br/>`openrouter/google/gemini-2.5-pro-preview`<br/>`openrouter/google/gemini-3-flash-preview`<br/>`openrouter/deepseek/deepseek-r1-0528`<br/>`openrouter/deepseek/deepseek-chat-v3-0324`<br/>`openrouter/openai/gpt-4.1` | Campo `model: <provider>/<model_id>` no frontmatter de cada `.opencode/agents/<nome>.md` (validado via `opencode debug agents`) |
| **Google Antigravity IDE (`.agents/agents/*.md`)** | Sessão nativa do Antigravity IDE | `inherit` (herda o modelo ativo da sessão), `pro`, `flash`, `flash_lite` | Campo `model: inherit` nos arquivos `.agents/agents/*.md` e parâmetro `Model` (`inherit`, `pro`, `flash`, `flash_lite`) em `invoke_subagent` |

---

## 2. Matriz Individual de Modelos (Hermes + 23 Agentes)

Todos os identificadores abaixo na coluna **Modelo Principal (OpenCode)** foram verificados no catálogo de `opencode models` e confirmados como carregados e parseados pela saída JSON de `opencode debug agents` (`providerID: "openrouter"`).

| # | Nome do Agente | Equipe | Modelo Principal (OpenCode / Hermes) | Provedor Principal | Modelo Alternativo (Fallback Documentado) | Provedor Alternativo | Configuração no Antigravity (`.agents/agents/`) | Justificativa Técnica | Status de Validação |
|---|---|---|---|---|---|---|---|---|---|
| **0** | **`hermes`** *(Orquestrador)* | Coordenação Principal | `BRAD` *(padrão ativo)* / `claude-opus-4.8` | `nous` (`https://inference-api.nousresearch.com/v1`) | `gpt-4.1` / `claude-sonnet-5` | `copilot` (`credential_pool`) | N/A *(Orquestrador externo)* | Raciocínio avançado, planejamento multi-equipe e decomposição de tarefas com `delegate_task`. | **Configuração Válida + Provedor Autenticado (`nous: logged in`)** |
| **1** | **`react-cto`** | Frontend (Líder) | `openrouter/anthropic/claude-opus-4.6` | `openrouter` | `openrouter/openai/gpt-4.1` | `openrouter` / `copilot` | `model: inherit` (`pro`) | Líder técnico frontend: exige raciocínio arquitetural profundo e consolidação de planos. | **Agente e Modelo Reconhecidos (`opencode debug agents`)** |
| **2** | **`software-architect`** | Frontend | `openrouter/anthropic/claude-opus-4.6` | `openrouter` | `openrouter/google/gemini-2.5-pro-preview` | `openrouter` | `model: inherit` (`pro`) | Avaliação de modularidade, fronteiras de componentes, trade-offs e ADRs. | **Agente e Modelo Reconhecidos (`opencode debug agents`)** |
| **3** | **`react-specialist`** | Frontend | `openrouter/anthropic/claude-sonnet-4.6` | `openrouter` | `openrouter/deepseek/deepseek-chat-v3-0324` | `openrouter` | `model: inherit` | Alta precisão em programação React 19, hooks, TypeScript estrito e estado. | **Agente e Modelo Reconhecidos (`opencode debug agents`)** |
| **4** | **`nextjs-specialist`** | Frontend | `openrouter/anthropic/claude-sonnet-4.6` | `openrouter` | `openrouter/openai/gpt-4.1` | `openrouter` | `model: inherit` | Especialista em Next.js 15 App Router, Server/Client Components, caching e rotas. | **Agente e Modelo Reconhecidos (`opencode debug agents`)** |
| **5** | **`ui-ux-engineer`** | Frontend | `openrouter/google/gemini-2.5-pro-preview` | `openrouter` | `openrouter/anthropic/claude-sonnet-4.6` | `openrouter` | `model: inherit` | Forte capacidade multimodal e visual para leitura de frames do Figma, tokens `.sosp-` e WCAG. | **Agente e Modelo Reconhecidos (`opencode debug agents`)** |
| **6** | **`backend-engineer`** | Frontend (BFF/TS) | `openrouter/anthropic/claude-sonnet-4.6` | `openrouter` | `openrouter/deepseek/deepseek-chat-v3-0324` | `openrouter` | `model: inherit` | Forte em contratos tipados TypeScript, Route Handlers e integração com OpenAPI. | **Agente e Modelo Reconhecidos (`opencode debug agents`)** |
| **7** | **`qa-engineer`** | Frontend | `openrouter/anthropic/claude-sonnet-4.5` | `openrouter` | `openrouter/google/gemini-3-flash-preview` | `openrouter` | `model: inherit` | Escrita ágil e determinística de testes Vitest, Testing Library e Playwright. | **Agente e Modelo Reconhecidos (`opencode debug agents`)** |
| **8** | **`security-performance-engineer`** | Frontend | `openrouter/anthropic/claude-opus-4.6` | `openrouter` | `openrouter/deepseek/deepseek-r1-0528` | `openrouter` | `model: inherit` (`pro`) | Análise rigorosa de AppSec web (CSP, XSS, CSRF) e profiling de Core Web Vitals. | **Agente e Modelo Reconhecidos (`opencode debug agents`)** |
| **9** | **`backend-lead`** | Backend (Líder) | `openrouter/anthropic/claude-opus-4.6` | `openrouter` | `openrouter/openai/gpt-4.1` | `openrouter` / `copilot` | `model: inherit` (`pro`) | Líder e arquiteto Django: governa as fronteiras dos 9 módulos do monólito modular. | **Agente e Modelo Reconhecidos (`opencode debug agents`)** |
| **10** | **`django-api-engineer`** | Backend | `openrouter/anthropic/claude-sonnet-4.6` | `openrouter` | `openrouter/deepseek/deepseek-chat-v3-0324` | `openrouter` | `model: inherit` | Excelente em código Django REST Framework, serializers, paginação e `RFC 7807`. | **Agente e Modelo Reconhecidos (`opencode debug agents`)** |
| **11** | **`django-domain-engineer`** | Backend | `openrouter/anthropic/claude-sonnet-4.6` | `openrouter` | `openrouter/openai/gpt-4.1` | `openrouter` | `model: inherit` | Implementação de regras de negócio (`RN-01..40`), `services.py`, transações e Celery. | **Agente e Modelo Reconhecidos (`opencode debug agents`)** |
| **12** | **`postgresql-data-architect`** | Backend | `openrouter/anthropic/claude-opus-4.6` | `openrouter` | `openrouter/deepseek/deepseek-r1-0528` | `openrouter` | `model: inherit` (`pro`) | Raciocínio avançado em modelagem relacional PostgreSQL 17 (`camelCase`), constraints e índices. | **Agente e Modelo Reconhecidos (`opencode debug agents`)** |
| **13** | **`django-orm-migrations-engineer`** | Backend | `openrouter/anthropic/claude-sonnet-4.6` | `openrouter` | `openrouter/deepseek/deepseek-chat-v3-0324` | `openrouter` | `model: inherit` | Mapeamento ORM (`db_table`/`db_column`), `select_related` e migrations seguras. | **Agente e Modelo Reconhecidos (`opencode debug agents`)** |
| **14** | **`backend-auth-security-engineer`** | Backend | `openrouter/anthropic/claude-opus-4.6` | `openrouter` | `openrouter/anthropic/claude-sonnet-4.6` | `openrouter` | `model: inherit` (`pro`) | Raciocínio crítico em segurança: hash `Argon2id`, RBAC, bloqueio de tentativas e `auditEvent`. | **Agente e Modelo Reconhecidos (`opencode debug agents`)** |
| **15** | **`backend-performance-engineer`** | Backend | `openrouter/deepseek/deepseek-r1-0528` | `openrouter` | `openrouter/anthropic/claude-sonnet-4.6` | `openrouter` | `model: inherit` | Modelo de raciocínio analítico profundo para `EXPLAIN ANALYZE`, locks, `N+1` e caching. | **Agente e Modelo Reconhecidos (`opencode debug agents`)** |
| **16** | **`backend-integration-engineer`** | Backend | `openrouter/anthropic/claude-sonnet-4.5` | `openrouter` | `openrouter/google/gemini-3-flash-preview` | `openrouter` | `model: inherit` | Implementação confiável de clientes HTTP (`ViaCEP`, `IBGE`, `S3`), retries, timeouts e logs. | **Agente e Modelo Reconhecidos (`opencode debug agents`)** |
| **17** | **`test-lead`** | QA (Líder) | `openrouter/anthropic/claude-opus-4.6` | `openrouter` | `openrouter/openai/gpt-4.1` | `openrouter` / `copilot` | `model: inherit` (`pro`) | Líder de auditoria independente: analisa riscos sistêmicos e emite veredito de release gate. | **Agente e Modelo Reconhecidos (`opencode debug agents`)** |
| **18** | **`frontend-test-engineer`** | QA | `openrouter/anthropic/claude-sonnet-4.5` | `openrouter` | `openrouter/google/gemini-3-flash-preview` | `openrouter` | `model: inherit` | Validação de componentes, formulários, 4 estados de UI, teclado e acessibilidade. | **Agente e Modelo Reconhecidos (`opencode debug agents`)** |
| **19** | **`backend-api-tester`** | QA | `openrouter/anthropic/claude-sonnet-4.5` | `openrouter` | `openrouter/deepseek/deepseek-chat-v3-0324` | `openrouter` | `model: inherit` | Testes de contrato OpenAPI, limites, RBAC, idempotência e respostas `RFC 7807`. | **Agente e Modelo Reconhecidos (`opencode debug agents`)** |
| **20** | **`integration-e2e-engineer`** | QA | `openrouter/anthropic/claude-sonnet-4.5` | `openrouter` | `openrouter/google/gemini-3-flash-preview` | `openrouter` | `model: inherit` | Testes de jornadas ponta a ponta (cadastro, login, busca, ficha, agendamento e protocolo). | **Agente e Modelo Reconhecidos (`opencode debug agents`)** |
| **21** | **`database-test-engineer`** | QA | `openrouter/anthropic/claude-sonnet-4.6` | `openrouter` | `openrouter/deepseek/deepseek-r1-0528` | `openrouter` | `model: inherit` | Testes de constraints SQL, transações, rollback, concorrência e exclusão lógica. | **Agente e Modelo Reconhecidos (`opencode debug agents`)** |
| **22** | **`security-tester`** | QA | `openrouter/anthropic/claude-opus-4.6` | `openrouter` | `openrouter/deepseek/deepseek-r1-0528` | `openrouter` | `model: inherit` (`pro`) | Auditoria AppSec ofensiva/defensiva controlada (IDOR/BOLA, XSS, SQLi, upload, headers). | **Agente e Modelo Reconhecidos (`opencode debug agents`)** |
| **23** | **`performance-engineer`** | QA | `openrouter/deepseek/deepseek-r1-0528` | `openrouter` | `openrouter/anthropic/claude-sonnet-4.5` | `openrouter` | `model: inherit` | Análise matemática de métricas `p50`/`p95`/`p99` (`RNF-04`), Web Vitals e gargalos. | **Agente e Modelo Reconhecidos (`opencode debug agents`)** |

---

## 3. Avaliação Técnica da Integração Comunitária `antigravity-oauth` (Etapa 8)

Conforme exigido na **Etapa 8**, foi avaliada a integração comunitária `antigravity-oauth` (`https://hermes-agent.nousresearch.com/marketplace/antigravity-oauth` / pacotes comunitários `hermes-antigravity-oauth`):

1. **Origem e Natureza:**
   - Trata-se de um **plugin comunitário (terceiros)**, não mantido oficialmente pela equipe do Google Antigravity.
2. **Como Funciona o Fluxo de Autenticação e Recursos:**
   - O plugin tenta reutilizar a sessão OAuth da conta Google Antigravity (via binário `agy` ou um proxy local, tipicamente na porta `8999`) para rotear chamadas de inferência do Hermes Agent através da cota da assinatura do Antigravity.
3. **Compatibilidade e Riscos Identificados neste Mac:**
   - **Ausência do CLI `agy`:** Nesta máquina está instalado o `Antigravity IDE.app`, mas o binário standalone `agy` CLI não está instalado em `/usr/local/bin` ou `~/.gemini/antigravity-cli/`.
   - **Acesso a Credenciais e Termos de Serviço:** Plugins de ponte OAuth interceptam tokens de sessão locais da sua conta Google/Antigravity e podem conflitar com limites de rate-limit ou políticas de uso da conta.
   - **Desnecessidade Atual:** O seu Hermes Agent **já possui autenticação oficial ativa e verificada** em dois provedores nativos (`nous: logged in` e `copilot: logged in`), e o OpenCode possui `OpenRouter` e `GitHub Copilot` (`stored`).
4. **Decisão Aplicada (Segurança Supervisionada):**
   - **NÃO instalamos o plugin comunitário `antigravity-oauth` nem conectamos contas.** Caso você deseje instalá-lo futuramente, será necessária sua autorização explícita.

