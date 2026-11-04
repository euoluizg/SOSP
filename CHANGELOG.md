# Changelog

Todas as mudanças relevantes deste repositório são documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/), e este projeto adere ao [Versionamento Semântico (SemVer)](https://semver.org/lang/pt-BR/).

---

## [1.1.0] — 2026-11-01

### Adicionado

- **Pilar 0 (`docs/README.md`):** Índice geral da documentação, hierarquia de fontes de verdade, equipe (`Mozart Melo`, `Arthur Franco` e `Luiz Gustavo`) e guia de leitura por perfil.
- **Pilar 1 (`docs/01-product-specs.md`):** Especificação completa de produto (RF-01 a RF-14, RNF-01 a RNF-12, RN-01 a RN-40, RS-01 a RS-05, CA-01 a CA-21, matriz LGPD, ameaças STRIDE e matriz de divergências D1–D13).
- **Documento formal de requisitos (`docs/Documento_de_Requisitos_Modelo_RF_v10.pdf`):** Especificação acadêmica oficial do CESMAC com casos de uso, matriz de avaliação de risco, matriz de rastreabilidade e contagem por Pontos de Função.
- **Pilar 2 (`docs/02-design-ux.md`) e Índice de Telas (`docs/design/README.md`):** Mapeamento das 30 telas do sistema (45 frames no Figma: 15 do cidadão em versões mobile `390 px` e web `1440 px`, 5 do servidor, 6 administrativas e 4 transversais) com todos os `Node IDs` preenchidos, tokens e inventário de 17 famílias de componentes base (40 itens detalhados).
- **Exportações oficiais do Figma (`docs/design/exports/`):** 45 frames em PNG organizados por perfil (`Cidadão/Mobile`, `Cidadão/Web`, `Servidor`, `Administrador`, `Transversais`), capa oficial (`capa-sosp.png`), manifesto SHA-256 (`manifest.json`) e PDF consolidado de 46 páginas (`sosp-prototipo-2026-11-01.pdf`).
- **Pilar 3 (`docs/03-architecture.md`) e ADRs (`docs/adr/ADR-001` a `ADR-008`):** Arquitetura de monólito modular (`Django 5` + `Next.js 15`), autenticação local (`Argon2id`) com Gov.br OIDC planejado para a v2.0, Git Flow simplificado com tasks pareadas `[FE]` e `[BE]` por requisito, filas Redis/Celery com DLQ, armazenamento S3/MinIO, feature flags e PostgreSQL 17 no Supabase.
- **Pilar 4 (`docs/04-data-api.md`), Contrato REST (`docs/api/openapi.yaml`) e DDL (`docs/database/schema.sql`):** Modelo físico com 34 tabelas em `camelCase`, contrato OpenAPI 3.0.3 sob `/api/v1` e tratamento de erros no padrão `RFC 7807`.
- **Pilar 5 (`docs/05-engineering-devops.md`), `CONTRIBUTING.md`, `.env.example` e `.github/CODEOWNERS`:** Padrões de engenharia, convenção de branches/tasks (`[FE]` / `[BE]`), pirâmide de testes, CI/CD, observabilidade, backup/restore e feature flags.
- **Pilar 6 (`docs/06-project-management.md`), Casos de Uso (`docs/use-cases/README.md`), Roteiro da Demo (`docs/demo-7-minutos.md`) e Glossário (`docs/glossario.md`):** Gestão ágil (Scrum + Kanban), cronograma em marcos (M0 a M9), matriz de riscos (R-01 a R-16), UC-01 a UC-17 detalhados e roteiro de apresentação de 7 minutos.

### Alterado

- Alinhamento integral do MVP para **cadastro manual (RF-01)**, **autenticação local por CPF e senha com modal informativo para o botão Gov.br (RF-02 / ADR-003)** e **agendamento presencial 100% realizado dentro do SOSP (RF-08)**.

