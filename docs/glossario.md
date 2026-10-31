# Glossário — SOSP

> **Projeto:** SOSP — Sistema de Orientação para Serviços Públicos
> **Versão:** 1.1.0 · **Data:** 30/10/2026 · **Status:** Em revisão
> **Autores:** Equipe de Engenharia de Software — CESMAC
> **Documentos irmãos:** [Índice](README.md) · [Pilar 1](01-product-specs.md) · [Pilar 2](02-design-ux.md) · [Pilar 3](03-architecture.md) · [Pilar 4](04-data-api.md) · [Pilar 5](05-engineering-devops.md)

---

## Sumário

1. [Produto e domínio](#1-produto-e-domínio)
2. [Requisitos e rastreabilidade](#2-requisitos-e-rastreabilidade)
3. [Arquitetura e operação](#3-arquitetura-e-operação)
4. [Segurança, privacidade e identidade](#4-segurança-privacidade-e-identidade)
5. [Processo e engenharia](#5-processo-e-engenharia)
6. [Banco de dados e Supabase](#6-banco-de-dados-e-supabase)
7. [Siglas](#7-siglas)

---

## 1. Produto e domínio

| Termo | Definição |
|---|---|
| **SOSP** | Sistema de Orientação para Serviços Públicos. Ponto de entrada único que traduz a necessidade do cidadão em um serviço público concreto, com ficha orientativa, agendamento e protocolo. |
| **Ficha orientativa** | Página que reúne os oito blocos de orientação de um serviço: o que é, quem tem direito, o que levar, como fazer, onde fazer, quando, quanto custa e quanto demora. É o núcleo do RF-06. |
| **Protocolo** | Identificador no formato `AAAAMMDD-XXXX` gerado no agendamento ou na abertura de dúvida. É a chave que o cidadão usa para acompanhar o pedido sem ligar para a unidade. |
| **Slot** | Bloco de 30 minutos dentro do horário de funcionamento de uma unidade, usado para reservar um atendimento presencial. Feriados, dias sem atendimento e lotação não geram slots. |
| **Unidade** | Local físico de atendimento de um órgão, com endereço, horários, limite diário, acessibilidade e coordenadas opcionais. |
| **Órgão** | Pessoa jurídica de direito público (municipal, estadual ou federal) responsável por um ou mais serviços. |
| **Catálogo** | Conjunto versionado de serviços publicados, com documentos, etapas, custo, prazo, canal e vínculos com órgãos e unidades. |
| **Serviço** | Unidade de orientação do catálogo: "Emitir Carteira de Identidade", "Agendar vacinação", etc. Não se confunde com o órgão que o presta. |
| **Checklist** | Lista de documentos e etapas que o cidadão marca no guia passo a passo; o progresso é salvo por CPF e por serviço. |
| **Dúvida** | Protocolo aberto a partir do FAQ quando as três respostas sugeridas não resolvem a necessidade do cidadão. |

---

## 2. Requisitos e rastreabilidade

| Sigla | Significado | Onde vive |
|---|---|---|
| **RF** | Requisito funcional. Descreve o que o sistema faz (RF-01 a RF-14). | [Pilar 1 §4](01-product-specs.md#4-requisitos-funcionais) |
| **RNF** | Requisito não funcional. Descreve qualidade, restrição ou meta verificável (RNF-01 a RNF-12). | [Pilar 1 §5](01-product-specs.md#5-requisitos-não-funcionais) |
| **RN** | Regra de negócio. Condição que o sistema deve sempre respeitar (RN-01 a RN-40). | [Pilar 1 §4.3](01-product-specs.md#43-regras-de-negócio) |
| **RS** | Requisito de segurança. Controle verificável derivado do modelo de ameaças (RS-01 a RS-05). | [Pilar 1 §6](01-product-specs.md#6-segurança-e-privacidade) |
| **CA** | Critério de aceite. Condição binária que prova que um requisito está pronto (CA-01 a CA-21). | [Pilar 1 §3](01-product-specs.md#catálogo-consolidado-de-critérios-de-aceite) |
| **UC** | Caso de uso. Objetivo de um ator, com fluxo principal, alternativos e exceções (UC-01 a UC-17). | [Casos de uso](use-cases/README.md) |
| **US** | User story. Necessidade contada na perspectiva de um perfil (US-01 a US-21). | [Pilar 1 §3](01-product-specs.md#3-user-stories-e-critérios-de-aceite) |
| **ADR** | Architecture Decision Record. Documento curto com contexto, decisão, consequências, alternativas e critérios de verificação. | [`docs/adr/`](adr/) |
| **MVP** | Minimum Viable Product. Menor escopo que entrega a jornada completa de orientação e agendamento com qualidade. No SOSP, exclui RF-10, RF-13 (central), SMS, WhatsApp e app nativo. | [Pilar 1 §1.5](01-product-specs.md#15-mvp--roadmap-v20) |
| **D** | Divergência identificada entre requisito, protótipo e arquitetura, com dono e critério de encerramento (D1 a D13). | [Pilar 1 §7](01-product-specs.md#7-matriz-de-divergências) |
| **DoR** | Definition of Ready. Critérios que uma história precisa cumprir antes de entrar em desenvolvimento. | [Pilar 6](06-project-management.md) |
| **DoD** | Definition of Done. Critérios que provam que um requisito está pronto. | [Pilar 1 §9](01-product-specs.md#9-definição-de-pronto) |

---

## 3. Arquitetura e operação

| Termo | Definição |
|---|---|
| **Monólito modular** | Aplicação implantada como um conjunto pequeno de deployáveis, mas organizada internamente em módulos de domínio com fronteiras verificadas. No SOSP: API Django, back-office e portal Next.js. |
| **Monorepo** | Um único repositório Git com `backend/`, `portal/`, `docs/`, `scripts/` e `deploy/`. Permite um PR que altera contrato, back e front de forma coordenada. |
| **Feature flag** | Chave de configuração que liga ou desliga uma funcionalidade sem novo deploy. No SOSP, é avaliada no servidor; rota desligada responde `404`. |
| **Expand/contract** | Padrão de migração em duas fases: primeiro expande o schema de forma compatível com o código antigo; depois, em release posterior, contrai (remove) o que não é mais usado. |
| **DLQ** | Dead Letter Queue. Fila para onde vão mensagens que falharam após todas as tentativas; exige alerta e reprocessamento manual. |
| **Worker** | Processo Celery que consome filas e executa tarefas fora do ciclo de requisição (PDF, e-mail, exportação, lembretes). |
| **Broker** | Redis usado como intermediário entre a API e os workers. |
| **S3 / MinIO** | API de object storage. MinIO é usado localmente; S3 (ou Supabase Storage) em produção. Arquivos são servidos por URL assinada. |
| **URL assinada** | URL temporária que concede acesso a um objeto privado por tempo limitado (5 minutos no SOSP). |
| **SLI** | Service Level Indicator. Métrica que mede o nível de serviço, por exemplo, percentual de requisições `2xx` ou latência. |
| **SLO** | Service Level Objective. Meta para um SLI, por exemplo, disponibilidade ≥ 99,0% em horário comercial. |
| **p95 / p99** | Percentis de latência. p95 = 95% das requisições terminam em até aquele tempo; p99 = 99%. O p99 é o limite que dispara alerta. |
| **RUM** | Real User Monitoring. Coleta de métricas de navegadores reais (carregamento, interação, erros) para complementar a monitoração sintética. |
| **RPO** | Recovery Point Objective. Perda máxima de dados aceitável, em tempo. No SOSP: ≤ 24 h (RNF-07). |
| **RTO** | Recovery Time Objective. Tempo máximo aceitável para restaurar o serviço. No SOSP: ≤ 4 h (RNF-07). |
| **C4** | Modelo de diagramas de arquitetura em quatro níveis: contexto, containers, componentes e código. |
| **Pooler** | Serviço de multiplexação de conexões PostgreSQL (Supavisor, no Supabase). O SOSP usa Session pooler por padrão e Transaction pooler quando há muitas conexões curtas. |

---

## 4. Segurança, privacidade e identidade

| Termo | Definição |
|---|---|
| **Gov.br** | Plataforma de autenticação do governo federal via OIDC. No SOSP, a integração com o Gov.br está prevista para a v2.0. No MVP, o cidadão cria conta manualmente e autentica com CPF + senha (Argon2id). O botão "Entrar com Gov.br" existe na interface e exibe modal de implementação futura quando clicado. Ver [ADR-003](adr/ADR-003-autenticacao-govbr-rbac.md). |
| **OIDC** | OpenID Connect. Camada de identidade sobre OAuth 2.0 usada para autenticar o cidadão no Gov.br com Authorization Code + PKCE. |
| **OAuth 2.0** | Protocolo de autorização usado na base do OIDC. |
| **RBAC** | Role-Based Access Control. Controle de acesso por papel (Cidadão, Servidor, Servidor autorizado, Administrador, Super Administrador). |
| **LGPD** | Lei Geral de Proteção de Dados (Lei 13.709/2018). Orienta finalidade, consentimento, minimização, retenção e direitos do titular. |
| **PII** | Personally Identifiable Information. Dado que identifica ou pode identificar uma pessoa; nunca entra em log de busca. |
| **RLS** | Row Level Security do PostgreSQL. No SOSP, é defesa em profundidade: a Data API do Supabase fica desabilitada e o Django é a única porta de escrita. |
| **CSRF** | Cross-Site Request Forgery. Ataque mitigado por token `X-CSRFToken` e cookie `SameSite`. |
| **HMAC** | Hash-based Message Authentication Code. Usado para autenticar o webhook do provedor de e-mail. |
| **ClamAV** | Antivírus open source usado na verificação de anexos (RS-04). |
| **Argon2id** | Algoritmo de hash de senha usado para servidores e administradores. |

---

## 5. Processo e engenharia

| Termo | Definição |
|---|---|
| **Git Flow** | Fluxo de branches com `main` (produção) e `develop` (integração), branches `feat/`, `fix/`, `docs/`, `chore/`, `test/`, `refactor/`, além de `release/*` e `hotfix/*`. Ver [ADR-004](adr/ADR-004-git-flow-simplificado.md). |
| **Contract-first** | Prática de alterar primeiro o contrato OpenAPI e só depois implementar back e front em paralelo, com mock gerado do contrato. |
| **Conventional Commits** | Padrão de mensagem `<tipo>(<escopo>): <descrição>`, com rodapé `Refs:` ou `Closes:`. |
| **Squash merge** | Merge que condensa os commits da branch em um único commit na branch de destino, preservando a mensagem convencional. |
| **Release** | Branch `release/vX.Y.Z` criada de `develop`, estabilizada e mergeada em `main` (com tag) e de volta em `develop`. |
| **Hotfix** | Branch criada de `main` para corrigir incidente urgente e mergeada em `main` e `develop`. |
| **CI/CD** | Integração e entrega contínuas. No SOSP, pipelines separados por caminho (`backend/**`, `portal/**`) e validação do contrato. |
| **Code review** | Revisão obrigatória de PR; PR `full` exige um revisor de back-end e um de front-end. |
| **Sprint** | Ciclo curto de planejamento e entrega, com revisão e retrospectiva. |
| **Kanban** | Método de fluxo contínuo com limite de trabalho em progresso; usado para operação e suporte. |
| **Scrum** | Framework de gestão com papéis, eventos e artefatos; usado como base do processo do SOSP. |
| **Cerimônia** | Evento do processo: planning, daily, review e retrospectiva. |
| **Definition of Ready** | Critérios de entrada de uma história no sprint: valor, critério de aceite, protótipo, contrato e dependências resolvidas. |

---

## 6. Banco de dados e Supabase

| Termo | Definição |
|---|---|
| **Supabase** | Provedor de PostgreSQL gerenciado usado em staging e produção. No SOSP, **somente o banco**: Auth, Data API, Realtime e chaves `anon`/`service_role` não são usados. |
| **PostgreSQL** | Banco relacional open source. O SOSP usa PostgreSQL 17, com `pg_trgm`, `unaccent`, full-text em português e `gen_random_uuid()`. |
| **`pg_trgm`** | Extensão de similaridade de trigramas, usada para tolerar erro de digitação na busca. |
| **`unaccent`** | Extensão que remove acentos na busca textual, para que "certidão" e "certidao" produzam o mesmo lexema. |
| **Schema `public`** | Schema onde as 34 tabelas da aplicação vivem. A alternativa `sosp` foi considerada, mas não adotada para manter compatibilidade com ferramentas e com o Django. |
| **Session pooler** | Modo de conexão do Supavisor na porta 5432, recomendado para API e workers; permite `CONN_MAX_AGE > 0`. |
| **Transaction pooler** | Modo de conexão do Supavisor na porta 6543, para muitas conexões curtas; exige `DISABLE_SERVER_SIDE_CURSORS = True` e `CONN_MAX_AGE = 0`. |
| **Conexão direta** | Conexão com `db.<ref>.supabase.co:5432`, usada por migrações, `pg_dump` e restore. |
| **`pg_dump`** | Utilitário de backup lógico do PostgreSQL. No SOSP, roda pela conexão direta e gera arquivo `custom` com checksum. |
| **Pausa do projeto** | No plano gratuito do Supabase, o projeto é pausado após inatividade; o checklist de release verifica que ele está ativo. |

---

## 7. Siglas

| Sigla | Significado |
|---|---|
| **API** | Application Programming Interface |
| **BaaS** | Backend as a Service |
| **CEP** | Código de Endereçamento Postal |
| **CPF** | Cadastro de Pessoas Físicas |
| **CSS** | Cascading Style Sheets |
| **CSV** | Comma-Separated Values |
| **DRF** | Django REST Framework |
| **E2E** | End-to-end |
| **FAQ** | Frequently Asked Questions |
| **HTMX** | Biblioteca de interação HTML |
| **IBGE** | Instituto Brasileiro de Geografia e Estatística |
| **JSON** | JavaScript Object Notation |
| **OIDC** | OpenID Connect |
| **PDF** | Portable Document Format |
| **PNG** | Portable Network Graphics |
| **REST** | Representational State Transfer |
| **SMS** | Short Message Service |
| **SSR** | Server-Side Rendering |
| **TLS** | Transport Layer Security |
| **UI / UX** | User Interface / User Experience |
| **VAPID** | Voluntary Application Server Identification (Web Push) |
| **WCAG** | Web Content Accessibility Guidelines |

---

**Anterior:** [Índice](README.md) · **Próximo:** [Pilar 1 — Visão de Produto e Requisitos](01-product-specs.md)
