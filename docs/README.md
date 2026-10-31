# Pilar 0 — Índice da Documentação

> **Projeto:** SOSP — Sistema de Orientação para Serviços Públicos
> **Versão:** 1.1.0 · **Data:** 30/10/2026 · **Status:** Em revisão
> **Autores:** Equipe de Engenharia de Software — CESMAC
> **Documentos irmãos:** [Pilar 1](01-product-specs.md) · [Pilar 2](02-design-ux.md) · [Pilar 3](03-architecture.md) · [Pilar 4](04-data-api.md) · [Pilar 5](05-engineering-devops.md)

---

## Sumário

1. [O que é o SOSP](#1-o-que-é-o-sosp)
2. [Índice dos pilares e artefatos](#2-índice-dos-pilares-e-artefatos)
3. [Hierarquia de fontes de verdade](#hierarquia-de-fontes-de-verdade)
4. [Links externos e artefatos visuais](#4-links-externos-e-artefatos-visuais)
5. [Equipe e papéis](#5-equipe-e-papéis)
6. [Como ler esta documentação](#6-como-ler-esta-documentação)
7. [Glossário](#7-glossário)
8. [Versionamento e changelog](#8-versionamento-e-changelog)

---

## 1. O que é o SOSP

O **SOSP — Sistema de Orientação para Serviços Públicos** é um ponto de entrada único que traduz a necessidade do cidadão em um serviço público concreto. A partir de uma busca em linguagem simples, o sistema entrega uma **ficha orientativa** com o que é o serviço, quem tem direito, o que levar, como fazer, onde fazer, quando, quanto custa e quanto demora. Quando o atendimento é presencial, o cidadão agenda um horário, recebe um protocolo e acompanha o andamento sem precisar ligar para a unidade. O back-office mantém órgãos, unidades, catálogo, usuários internos, FAQ e relatórios. A solução é um **monólito modular** com API Django, back-office Django Admin e portal Next.js 15, sobre PostgreSQL, Redis e armazenamento S3/MinIO.

---

## 2. Índice dos pilares e artefatos

| Documento | O que contém | Quando consultar |
|---|---|---|
| [Pilar 1 — Produto e requisitos](01-product-specs.md) | Problema, personas, user stories, RF, RNF, RN, RS, CA, UC, matriz de divergências, rastreabilidade e definição de pronto | Antes de implementar qualquer requisito |
| [Pilar 2 — Design e UX](02-design-ux.md) | Princípios, jornada, navegação, estados, tokens, componentes, acessibilidade, microcopy e governança do Design System | Ao desenhar ou implementar interface |
| [Pilar 3 — Arquitetura](03-architecture.md) | C4, módulos, camadas, portal, integrações, segurança, topologia, ADRs e trade-offs | Ao tomar decisão estrutural ou revisar acoplamento |
| [Pilar 4 — Dados e API](04-data-api.md) | Convenções, ER, catálogo de tabelas, DDL, contrato REST, erros, assíncrono e migrações | Ao criar model, migration, endpoint ou consulta |
| [Pilar 5 — Engenharia, DevOps e operação](05-engineering-devops.md) | Onboarding, segredos, Git, testes, CI/CD, observabilidade, runbook, backup, postmortem e flags | No dia a dia de desenvolvimento e operação |
| [Pilar 6 — Gestão do projeto](06-project-management.md) | Stakeholders, cronograma, riscos, metodologia, cerimônias e Definition of Ready | Ao planejar sprint, release ou apresentação |
| [Casos de uso detalhados](use-cases/README.md) | UC-01 a UC-17 com atores, fluxos, exceções, pós-condições e RN relacionadas | Ao implementar ou testar um fluxo completo |
| [Índice de telas](design/README.md) | 45 telas do Figma (30 mobile + 15 web), RF relacionado, âncoras e links por frame | Ao localizar ou revisar uma tela |
| [Exportações do design](design/exports/README.md) | Instruções e registro das exportações PNG/PDF do protótipo | Quando o Figma estiver indisponível |
| [Roteiro da demonstração](demo-7-minutos.md) | Roteiro ensaiado de 7 minutos para a apresentação | Antes de demonstrar o sistema |
| [Glossário](glossario.md) | Definição dos termos e siglas usados na documentação | Quando um termo não estiver claro |
| [ADR-001](adr/ADR-001-monolito-modular-django-nextjs.md) | Monólito modular Django + portal Next.js | Antes de propor microsserviços ou SPA pura |
| [ADR-002](adr/ADR-002-postgresql-camelcase.md) | PostgreSQL 17 e convenção `camelCase` sem aspas | Antes de criar tabela, coluna ou query |
| [ADR-003](adr/ADR-003-autenticacao-govbr-rbac.md) | Autenticação local CPF+senha (MVP) e Gov.br OIDC (v2.0), login interno e RBAC | Antes de alterar autenticação ou permissão |
| [ADR-004](adr/ADR-004-git-flow-simplificado.md) | Git Flow simplificado (`main` + `develop`) em monorepo | Antes de criar branch ou release |
| [ADR-005](adr/ADR-005-processamento-assincrono-dlq.md) | Fila Redis, workers, PDF e DLQ | Antes de criar tarefa assíncrona |
| [ADR-006](adr/ADR-006-armazenamento-s3-url-assinada.md) | S3/MinIO com URL assinada | Antes de armazenar ou servir arquivo |
| [ADR-007](adr/ADR-007-feature-flags.md) | Feature flags para RF-10, RF-13 e painel de avaliações | Antes de ligar funcionalidade fora do MVP |
| [ADR-008](adr/ADR-008-supabase-postgresql-gerenciado.md) | Supabase como PostgreSQL gerenciado em São Paulo | Antes de configurar staging, produção ou backup |
| [`openapi.yaml`](api/openapi.yaml) | Contrato REST versionado em `/api/v1` | Ao criar ou consumir endpoint |
| [`schema.sql`](database/schema.sql) | DDL PostgreSQL 17 com 34 tabelas | Ao validar o modelo físico |
| [CHANGELOG](../CHANGELOG.md) | Histórico de versões no formato Keep a Changelog | Ao preparar release |
| [CONTRIBUTING](../CONTRIBUTING.md) | Resumo prático do fluxo Git e de PR | No primeiro commit |

---

## Hierarquia de fontes de verdade

Quando dois artefatos divergirem, a precedência é a abaixo. A ordem vale para **conflito de conteúdo**, não para substituir a revisão humana: uma divergência identificada deve ser registrada na [matriz de divergências do Pilar 1](01-product-specs.md#7-matriz-de-divergências).

| Ordem | Fonte | O que prevalece | Exemplo de conflito |
|---|---|---|---|
| 1 | **Requisito** — [Pilar 1](01-product-specs.md) | Comportamento, regra de negócio, critério de aceite e escopo | O RF-06 exige 10 resultados por página; o Figma mostra rolagem contínua. Vale o requisito. |
| 2 | **ADR** — [`adr/`](adr/) | Decisão arquitetural e tecnológica, com contexto e trade-offs | O ADR-003 define autenticação local CPF+senha (MVP) e Gov.br OIDC como futuro; um protótipo com Gov.br direto não reflete a decisão. |
| 3 | **Contrato** — [`openapi.yaml`](api/openapi.yaml) e [`schema.sql`](database/schema.sql) | Forma do dado, nomes de campos, status HTTP e constraints | O portal espera `protocolNumber`; o contrato define o nome e o tipo. |
| 4 | **Arquitetura** — [Pilar 3](03-architecture.md) | Fronteiras, fluxos, topologia e responsabilidades | O Pilar 3 diz que o portal não acessa o banco; uma implementação que acessa está errada. |
| 5 | **Figma** — [protótipo oficial](https://www.figma.com/design/P8Pf9aZiagXQulJpP2guqz/SOSP?node-id=0-1) | Aparência, hierarquia visual, espaçamento e conteúdo de tela | O Figma mostra um botão a mais; se o requisito não o prevê, ele não entra. |
| 6 | **Protótipo HTML** — [`Prototipo/`](../Prototipo/) | Referência técnica de implementação do recorte RF-06 | O HTML é derivado; não é fonte de requisito nem de design. |

**Regras de aplicação**

1. **Comportamento** vem do requisito; **aparência** vem do Figma. Os dois não são intercambiáveis.
2. Um ADR só é superado por outro ADR que o substitua explicitamente, ou por uma decisão registrada no Pilar 1 com aprovação de Produto e Arquitetura.
3. O contrato OpenAPI e o `schema.sql` são executáveis: em caso de dúvida, o que passa na validação do CI prevalece sobre a prosa.
4. O protótipo HTML (`Prototipo/rf006_busca.html` e `rf006_ficha.html`) é um artefato técnico derivado do recorte RF-06. Ele não substitui o Figma nem o requisito.
5. Toda divergência deve ter ID, dono e critério de encerramento verificável, conforme o [Pilar 1 §7](01-product-specs.md#7-matriz-de-divergências).

---

## 4. Links externos e artefatos visuais

| Artefato | Link | Observação |
|---|---|---|
| Protótipo oficial no Figma | <https://www.figma.com/design/P8Pf9aZiagXQulJpP2guqz/SOSP?node-id=0-1> | **Acesso somente visualização**; não requer conta paga |
| Índice das 45 telas | [docs/design/README.md](design/README.md) | 30 telas mobile + 15 versões web do cidadão |
| Protótipo HTML do RF-06 | [`Prototipo/`](../Prototipo/) | Artefato técnico derivado; abrir `rf006_busca.html` e `rf006_ficha.html` |
| Design System | [`DesignSystem/index.html`](../DesignSystem/index.html) | Catálogo vivo de tokens e componentes |
| Exportações do protótipo | [`docs/design/exports/`](design/exports/) | PNG/PDF com data de exportação |
| Repositório | `https://github.com/<org>/sosp` | `<preencher>` com a URL definitiva |

**Por que exportar:** o arquivo do Figma pode mudar de permissão, de owner ou de conteúdo. As exportações em [`docs/design/exports/`](design/exports/) garantem que a documentação continue legível na apresentação e na avaliação. O link do Figma continua sendo a fonte oficial de aparência; a exportação é uma cópia datada.

---

## 5. Equipe e papéis

| Nome | Papel | Responsabilidades principais |
|---|---|---|
| `<preencher>` | Product Owner (PO) | Prioriza o backlog, valida requisitos, decide escopo do MVP e aprova divergências |
| `<preencher>` | Tech Lead | Arquitetura, ADRs, revisão de contrato e de migração, mentoria e decisões técnicas |
| `<preencher>` | Back-end | API Django, workers, schema, migrações, testes de integração e segurança |
| `<preencher>` | Front-end | Portal Next.js, acessibilidade, design system, testes E2E e performance |
| `<preencher>` | Design | Figma, fluxos, protótipos, tokens, microcopy e validação de usabilidade |
| `<preencher>` | QA | Plano de testes, casos de uso, critérios de aceite, regressão e evidências |
| `<preencher>` | DevOps / plantão | CI/CD, ambientes, observabilidade, backup, runbook e resposta a incidentes |

**Regra de decisão:** requisito e escopo são decididos pelo PO; arquitetura e tecnologia pelo Tech Lead com o time; contrato OpenAPI exige revisão de um dev de back-end e um de front-end; migração de banco exige revisão de back-end e Tech Lead.

---

## 6. Como ler esta documentação

### 6.1 Novo desenvolvedor

1. Este README, seções 1 a 3.
2. [Pilar 1 §1 a §4](01-product-specs.md#1-executive-summary-e-escopo) para entender o problema e os requisitos.
3. [Pilar 3](03-architecture.md) para entender as fronteiras e o fluxo de uma requisição.
4. [Pilar 4](04-data-api.md) para entender o schema e o contrato.
5. [Pilar 5 §1 a §5](05-engineering-devops.md#1-onboarding) para subir o ambiente e seguir o Git Flow.
6. [CONTRIBUTING](../CONTRIBUTING.md) e [ADR-004](adr/ADR-004-git-flow-simplificado.md) antes do primeiro PR.
7. [Casos de uso](use-cases/README.md) do UC que vai implementar.

### 6.2 Designer

1. [Pilar 2](02-design-ux.md) inteiro.
2. [Índice de telas](design/README.md) e o [Figma oficial](https://www.figma.com/design/P8Pf9aZiagXQulJpP2guqz/SOSP?node-id=0-1).
3. [Pilar 1 §2 e §3](01-product-specs.md#2-personas) para personas e histórias.
4. [Design System](../DesignSystem/index.html) para tokens e componentes.
5. [Pilar 1 §7](01-product-specs.md#7-matriz-de-divergências) para as divergências de design em aberto.

### 6.3 Professor ou avaliador

1. [Pilar 1 §1](01-product-specs.md#1-executive-summary-e-escopo) para o problema e a proposta de valor.
2. [Roteiro da demonstração](demo-7-minutos.md).
3. [Pilar 2](02-design-ux.md) e [Pilar 3](03-architecture.md) para design e arquitetura.
4. [Pilar 4](04-data-api.md) e [Pilar 5](05-engineering-devops.md) para engenharia e operação.
5. [ADRs](adr/) para as decisões e trade-offs.
6. [Pilar 6](06-project-management.md) para cronograma, riscos e metodologia.

### 6.4 QA

1. [Pilar 1 §3, §4, §8 e §9](01-product-specs.md#3-user-stories-e-critérios-de-aceite).
2. [Casos de uso](use-cases/README.md) e [critérios de aceite](01-product-specs.md#catálogo-consolidado-de-critérios-de-aceite).
3. [Pilar 4 §6](04-data-api.md#6-contrato-de-api) para o contrato e os erros.
4. [Pilar 5 §4](05-engineering-devops.md#4-estratégia-de-testes) para a estratégia de testes.
5. [Pilar 5 §5.8](05-engineering-devops.md#58-checklist-de-release) para o checklist de release.

### 6.5 Product Owner

1. [Pilar 1](01-product-specs.md) inteiro.
2. [Pilar 6](06-project-management.md) para cronograma, riscos e cerimônias.
3. [CHANGELOG](../CHANGELOG.md) e [Pilar 5 §10](05-engineering-devops.md#10-feature-flags-e-ambientes) para escopo entregue e flags.

---

## 7. Glossário

O glossário completo está em [`docs/glossario.md`](glossario.md). Os termos mais usados no dia a dia:

| Termo | Definição curta |
|---|---|
| **SOSP** | Sistema de Orientação para Serviços Públicos |
| **Ficha orientativa** | Página com os oito blocos de orientação de um serviço (o que é, quem tem direito, o que levar, como fazer, onde, quando, quanto custa e quanto demora) |
| **Protocolo** | Identificador `AAAAMMDD-XXXX` que o cidadão usa para acompanhar um pedido |
| **Slot** | Horário de 30 minutos disponível para agendamento em uma unidade |
| **RF / RNF / RN / RS** | Requisito funcional, requisito não funcional, regra de negócio e requisito de segurança |
| **CA / UC / US** | Critério de aceite, caso de uso e user story |
| **ADR** | Architecture Decision Record: registro de uma decisão arquitetural |
| **MVP** | Minimum Viable Product: menor escopo que entrega a jornada completa |
| **Feature flag** | Chave que liga ou desliga uma funcionalidade sem novo deploy |
| **DLQ** | Dead Letter Queue: fila de mensagens que falharam definitivamente |
| **Git Flow** | Fluxo com `main` (produção) e `develop` (integração), branches por tipo e release |
| **Supabase** | Provedor do PostgreSQL gerenciado; no SOSP, não é usado como BaaS |

---

## 8. Versionamento e changelog

A documentação segue **SemVer** (`MAJOR.MINOR.PATCH`) e o histórico fica no [`CHANGELOG.md`](../CHANGELOG.md), no formato *Keep a Changelog*.

| Mudança | Incremento | Exemplo |
|---|---|---|
| Correção de texto, link ou tabela sem mudar decisão | `PATCH` | `1.1.1` |
| Novo requisito, ADR, seção ou artefato compatível | `MINOR` | `1.1.0` → `1.2.0` |
| Mudança que quebra contrato, remove requisito ou altera arquitetura | `MAJOR` | `2.0.0` |

**Regra:** todo PR que altera documento em `docs/`, `openapi.yaml` ou `schema.sql` atualiza a versão no cabeçalho e registra a entrada no changelog. O Pilar 5 §3.3 e o template de PR cobram essa evidência.

---

**Próximo:** [Pilar 1 — Visão de Produto e Requisitos](01-product-specs.md)
