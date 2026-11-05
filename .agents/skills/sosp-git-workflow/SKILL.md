---
name: sosp-git-workflow
description: >-
  Use this skill when the user asks to start a new task, create a branch, format
  a commit message, or open/generate a Pull Request in the SOSP repository.
  Enforces the ADR-004 paired [FE]/[BE] branch naming convention, Conventional
  Commits, and the 14-item PR checklist from Pillar 5.
---

# SOSP Git Workflow (`ADR-004` + `Pilar 5`)

Use esta skill sempre que o usuário pedir para iniciar uma task (`[FE] [RFXXX]` ou `[BE] [RFXXX]`), criar uma branch, fazer um commit ou preparar um Pull Request.

## Passo 1: Consultar a Tabela Oficial das 28 Tasks Pareadas (`ADR-004`)

Consulte [`docs/adr/ADR-004-git-flow-simplificado.md#3-convenção-de-tasks-pareadas-fe-e-be-e-nomenclatura-de-branches`](../../../docs/adr/ADR-004-git-flow-simplificado.md) para obter o nome exato da task e da branch:

| RF | Branch Front-end (`Luiz Gustavo`) | Branch Back-end (`Arthur Franco`) |
|---|---|---|
| **RF001** | `feat/fe/rf001-cadastro-cidadao` | `feat/be/rf001-cadastro-cidadao` |
| **RF002** | `feat/fe/rf002-autenticacao-login` | `feat/be/rf002-autenticacao-rbac` |
| **RF003** | `feat/fe/rf003-gerenciar-orgaos` | `feat/be/rf003-gerenciar-orgaos` |
| **RF004** | `feat/fe/rf004-gerenciar-unidades` | `feat/be/rf004-gerenciar-unidades` |
| **RF005** | `feat/fe/rf005-catalogo-servicos` | `feat/be/rf005-catalogo-servicos` |
| **RF006** | `feat/fe/rf006-busca-ficha-servico` | `feat/be/rf006-busca-ficha-servico` |
| **RF007** | `feat/fe/rf007-guia-checklist` | `feat/be/rf007-guia-checklist-pdf` |
| **RF008** | `feat/fe/rf008-agendamento-atendimento` | `feat/be/rf008-agendamento-slots` |
| **RF009** | `feat/fe/rf009-acompanhar-protocolo` | `feat/be/rf009-acompanhar-protocolo` |
| **RF010** | `feat/fe/rf010-avaliacao-comentario` | `feat/be/rf010-avaliacao-comentario` |
| **RF011** | `feat/fe/rf011-faq-duvidas` | `feat/be/rf011-faq-duvidas` |
| **RF012** | `feat/fe/rf012-usuarios-internos` | `feat/be/rf012-usuarios-internos` |
| **RF013** | `feat/fe/rf013-notificacoes` | `feat/be/rf013-notificacoes` |
| **RF014** | `feat/fe/rf014-relatorios-gerenciais` | `feat/be/rf014-relatorios-gerenciais` |

Para tarefas de infraestrutura, documentação ou correções:
- `<tipo>/<fe|be|infra|docs>/<rfxxx>-<slug>` (onde `<tipo>` ∈ `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`).

## Passo 2: Criar a Branch a partir da `develop`

1. Verifique o status atual do Git (`git status` e `git branch --show-current`).
2. Atualize a `develop` e crie a branch correspondente:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b <nome-da-branch>
   ```

## Passo 3: Formatar Mensagens de Commit (Conventional Commits)

Todo commit deve seguir o formato:
```text
<tipo>(<camada>/<rfxxx>): <descrição curta no imperativo em português>

[corpo opcional explicando o que mudou e por quê]

Refs: RF-XX, UC-XX
```
Exemplos:
- `feat(fe/rf001): implementa formulário de cadastro do cidadão com autopreenchimento ViaCEP`
- `feat(be/rf008): adiciona cálculo de slots de 30min e protocolo AAAAMMDD-XXXX`
- `docs(adr): documenta convenção de branches [FE] e [BE]`

## Passo 4: Preparar Pull Request (`develop` ← `feat/...`)

1. O título do Pull Request deve ser **exatamente o nome do card**:
   - Ex.: `[FE] [RF001] Cadastro Cidadão Manual (Essencial)`
   - Ex.: `[BE] [RF001] Cadastro Cidadão Manual, Hash Argon2id e CEP/IBGE (Essencial)`
2. Preencha a descrição do PR usando o template [`.github/pull_request_template.md`](../../../.github/pull_request_template.md), marcando os itens aplicáveis do checklist de 14 pontos de [`docs/05-engineering-devops.md`](../../../docs/05-engineering-devops.md).

