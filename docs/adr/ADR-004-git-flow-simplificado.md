# ADR-004 — Git Flow simplificado em monorepo

- **Status:** Aceito
- **Data:** 30/10/2026
- **Decisores:** Equipe de Engenharia de Software — CESMAC
- **Substitui:** decisão implícita de Trunk-Based Development no Pilar 5 §3.1
- **Substituído por:** —

## Contexto

O SOSP é um monorepo com dois deployáveis (`backend/` e `portal/`), documentação viva (`docs/`), contrato OpenAPI e scripts operacionais. O time é pequeno, mas tem frentes de back-end e front-end trabalhando ao mesmo tempo, e a disciplina exige uma demonstração estável no fim do semestre.

O Pilar 5 descrevia Trunk-Based Development com branches de no máximo dois dias e deploy direto da `main`. Esse modelo funciona bem com times maduros, feature flags e deploy contínuo, mas cria dois problemas para o SOSP:

1. **Staging e produção compartilham a mesma branch.** Toda integração vai direto para a `main`, e uma alteração incompleta pode chegar ao ambiente de demonstração.
2. **Tarefas fullstack precisam de coordenação.** Contrato, back e front mudam em ritmos diferentes; sem uma branch de integração, o front fica bloqueado ou o contrato quebra o back.

A equipe adotou **`main` (produção) + `develop` (integração)** e um fluxo derivado do Git Flow, simplificado para o tamanho do projeto. A decisão não altera a arquitetura do monólito modular.

## Decisão

### Branches

| Branch | Origem | Destino | Uso |
|---|---|---|---|
| `main` | — | — | Produção; sempre estável; só recebe merge de `release/*` e `hotfix/*` |
| `develop` | `main` | — | Integração; deploy automático em staging |
| `feat/<área>/<id>-<descrição>` | `develop` | `develop` | Nova funcionalidade |
| `fix/<área>/<id>-<descrição>` | `develop` | `develop` | Correção não urgente |
| `docs/`, `chore/`, `test/`, `refactor/` | `develop` | `develop` | Demais tipos |
| `release/vX.Y.Z` | `develop` | `main` e `develop` | Estabilização da versão |
| `hotfix/<descrição>` | `main` | `main` e `develop` | Correção urgente em produção |

**Proibido:** commit direto e force push em `main` e `develop`; merge sem revisão e sem CI verde.

### Separação por área

| Área | Caminho | Exemplo de branch | Exemplo de commit |
|---|---|---|---|
| `back` | `backend/` | `feat/back/rf06-endpoint-busca` | `feat(back/search): adiciona filtro por município` |
| `front` | `portal/` | `feat/front/rf06-tela-busca` | `feat(front/search): implementa filtro por município` |
| `full` | ambos | `feat/full/rf08-campo-observacao` | `feat(full/scheduling): adiciona observação` |

Etiquetas no GitHub: `area:backend`, `area:frontend`, `area:fullstack`, além de etiquetas por requisito (`RF-06`, `RF-08`…). O campo **Área** do GitHub Projects permite filtrar o quadro por time.

### Contract-first

1. Toda tarefa fullstack nasce como **issue principal** (`area:fullstack`) com três sub-issues: **contrato**, **back** e **front**.
2. O primeiro PR (`feat/back/<id>-contrato`) altera **apenas** `docs/api/openapi.yaml` e é revisado por um dev de cada área.
3. Após o merge do contrato em `develop`, back e front trabalham em paralelo em branches próprias. O front usa mock gerado do OpenAPI (Prism/MSW) até a API estar disponível.
4. A issue principal só fecha quando as três sub-issues estiverem concluídas.
5. **Exceção:** mudanças pequenas (≤ 1–2 dias e ≤ ~400 linhas somando os dois lados) podem usar uma única branch `feat/full/...`, exigindo um revisor de cada área.

```mermaid
flowchart LR
    A[Issue principal area:fullstack] --> B[Sub-issue contrato]
    B --> C[PR feat/back/id-contrato<br/>apenas openapi.yaml]
    C --> D[Merge em develop]
    D --> E[Back em paralelo]
    D --> F[Front em paralelo<br/>mock Prism/MSW]
    E --> G[PR back]
    F --> H[PR front]
    G --> I[Merge em develop]
    H --> I
    I --> J[release/vX.Y.Z]
    J --> K[Merge em main + tag]
    K --> L[Deploy produção]
    I --> M[Deploy staging]
```

### Release e hotfix

- `release/vX.Y.Z` nasce de `develop`, recebe apenas correções de estabilização, changelog e versão. Ao final, merge em `main` (com tag `vX.Y.Z`) e de volta em `develop`.
- `hotfix/*` nasce de `main`, recebe a correção mínima e testes, merge em `main` (com tag de patch) e de volta em `develop`.
- O merge em `develop` dispara staging; o merge em `main` dispara produção.

### CI/CD por caminho

| Evento | Pipeline | O que roda |
|---|---|---|
| PR para `develop` | `backend.yml` se `backend/**` ou `openapi.yaml` mudou | Lint, testes de back, validação do contrato |
| PR para `develop` | `frontend.yml` se `portal/**` ou `openapi.yaml` mudou | Lint, build, validação do contrato |
| Merge em `develop` | Ambos, conforme caminho | Deploy em staging |
| Merge de `release/*` em `main` | Ambos, conforme caminho | Deploy em produção + tag `vX.Y.Z` |

## Consequências positivas

| Consequência | Efeito |
|---|---|
| Staging e produção separados | `develop` pode receber integração sem expor a demonstração |
| Contrato explícito | Back e front não divergem; o mock permite paralelismo |
| Release previsível | Janela de estabilização antes da `main` |
| Hotfix sem bloquear release | Correção urgente nasce da `main` e volta para `develop` |
| Rastreabilidade | Branch, commit e PR carregam área e requisito |

## Consequências negativas e trade-offs

| Trade-off | Custo aceito | Mitigação |
|---|---|---|
| Duas branches principais | Merge de `main` de volta em `develop` pode ser esquecido | Checklist de release + automação de PR |
| Mais cerimônia que trunk-based | Overhead de release e hotfix | Fluxo simplificado, sem `release/*` para patches pequenos |
| Branches de vida mais longa | Risco de conflito | Recomendação de até 2 dias, não regra rígida; rebase frequente |
| Contract-first adiciona uma etapa | PR de contrato antes do código | Exceção para mudanças ≤ 1–2 dias |
| CI por caminho pode pular validação cruzada | Mudança de contrato sem teste de back | `openapi.yaml` dispara os dois pipelines |

## Alternativas descartadas

### Trunk-Based Development puro

Seria mais simples e reduziria o tempo de integração, mas exigiria feature flags maduras, deploy contínuo e disciplina de branches curtas que o time ainda não tem. A `main` deixaria de ser um ponto seguro para a demonstração. Pode ser adotado no futuro, com ADR próprio.

### GitHub Flow (`main` + branches curtas)

É mais simples que o Git Flow, mas não separa staging de produção. Para a disciplina, a `develop` funciona como colchão de integração e como ambiente de homologação.

### Git Flow completo com `release/*` longa e `support/*`

Adiciona branches que o time não usa (versões antigas, suporte a múltiplas releases). O SOSP tem uma versão em produção por vez; `support/*` seria custo sem benefício.

### Monorepo com permissões por diretório e times independentes

Não resolve o problema de contrato e coordenação; apenas esconde o acoplamento. O CODEOWNERS já direciona revisores por caminho.

## Critérios de verificação

| Critério | Como verificar |
|---|---|
| `main` só recebe release/hotfix | Branch protection + histórico de merges |
| `develop` é a base das branches de trabalho | Template de PR e checklist |
| Nenhum commit direto em `main`/`develop` | Branch protection no GitHub |
| PR full tem revisor de cada área | CODEOWNERS + revisão obrigatória |
| Contrato é o primeiro PR de tarefa fullstack | Sub-issues e ordem dos PRs |
| Tag `vX.Y.Z` é criada no merge em `main` | Workflow `backend.yml`, job `tag-release` |
| `develop` e `main` convergem após release | Merge de `main` em `develop` no checklist |

## Referências

- [Pilar 5 §3 — Padrões de código e Git](../05-engineering-devops.md#3-padrões-de-código-e-git)
- [Pilar 5 §5 — CI/CD](../05-engineering-devops.md#5-cicd)
- [CONTRIBUTING.md](../../CONTRIBUTING.md)
- [.github/CODEOWNERS](../../.github/CODEOWNERS)
- [ADR-001 — Monólito modular](ADR-001-monolito-modular-django-nextjs.md)
