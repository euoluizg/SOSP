# Guia de Contribuição (CONTRIBUTING)

> **Projeto:** SOSP — Sistema de Orientação para Serviços Públicos
> **Referência completa:** [Pilar 5 — Engenharia, DevOps e Operação](docs/05-engineering-devops.md) e [ADR-004 — Git Flow Simplificado](docs/adr/ADR-004-git-flow-simplificado.md)

Este documento resume o fluxo de trabalho diário para desenvolvimento no monorepo do **SOSP**.

---

## 1. Fluxo de Branches (Git Flow Simplificado)

| Branch | Origem | Destino | Regra |
|---|---|---|---|
| `main` | — | — | Produção; recebe apenas merge de `release/*` e `hotfix/*` |
| `develop` | `main` | — | Integração contínua e homologação (staging) |
| `feat/<fe\|be>/rfxxx-<slug>` | `develop` | `develop` | Implementação de requisito funcional por camada |
| `fix/<fe\|be>/rfxxx-<slug>` | `develop` | `develop` | Correção de defeito |
| `docs/<descrição>` | `develop` | `develop` | Atualização de documentação ou contrato |
| `release/vX.Y.Z` | `develop` | `main` e `develop` | Fechamento de versão e changelog |
| `hotfix/<descrição>` | `main` | `main` e `develop` | Correção crítica em produção |

**Regras inegociáveis:**
1. Nunca faça commit direto ou `git push --force` em `main` ou `develop`.
2. Todo Pull Request exige CI verde e revisão antes do merge.

---

## 2. Padrão de Tasks (`[FE]` / `[BE]`), Issues e Pull Requests

Cada Requisito Funcional (`RF001` a `RF014`) é dividido em duas tasks pareadas para permitir trabalho paralelo sem conflitos entre Front-end (`portal/`) e Back-end (`backend/`):

- **Formato do Título (Card no Board / Issue / Pull Request):**
  ```text
  [<FE|BE>] [<RFXXX>] <Descrição da entrega na camada> (<Prioridade>)
  ```
  *Exemplos:*
  - `[FE] [RF001] Cadastro Cidadão Manual (Essencial)` — Responsável: `Luiz Gustavo`
  - `[BE] [RF001] Cadastro Cidadão Manual, Hash Argon2id e CEP/IBGE (Essencial)` — Responsável: `Arthur Franco`

- **Formato da Branch no Git (minúsculas, sem espaços, colchetes ou acentos):**
  ```text
  feat/fe/rf001-cadastro-cidadao
  feat/be/rf001-cadastro-cidadao
  ```

> A tabela completa com as **28 tasks pareadas** (`RF001` a `RF014`) está em [ADR-004](docs/adr/ADR-004-git-flow-simplificado.md).

---

## 3. Conventional Commits

As mensagens de commit seguem o formato:

```text
<tipo>(<camada/escopo>): <descrição curta no imperativo>
```

**Exemplos:**
- `feat(fe/rf001): implementa formulário de cadastro manual e máscara de CPF`
- `feat(be/rf001): adiciona hash Argon2id e integração com ViaCEP/IBGE`
- `fix(be/rf008): impede colisão de agendamento no mesmo slot`
- `docs(openapi): atualiza schema de erro RFC 7807`

---

## 4. Checklist antes de abrir um Pull Request

- [ ] A branch parte de `develop` e segue o padrão `feat/<fe|be>/rfxxx-<slug>`.
- [ ] O título do PR segue o padrão `[<FE|BE>] [<RFXXX>] <Descrição> (<Prioridade>)`.
- [ ] Se houve mudança de rota ou payload, o contrato [`docs/api/openapi.yaml`](docs/api/openapi.yaml) foi atualizado.
- [ ] Se houve mudança de banco, o [`docs/database/schema.sql`](docs/database/schema.sql) e a migração correspondente foram atualizados (respeitando `camelCase` sem aspas — [ADR-002](docs/adr/ADR-002-postgresql-camelcase.md)).
- [ ] Os testes automatizados e linters (`ruff` / `eslint`) passam localmente.
- [ ] Nenhum segredo (`.env`) ou dado pessoal real foi incluído no commit.
- [ ] O [`CHANGELOG.md`](CHANGELOG.md) foi atualizado quando aplicável.

