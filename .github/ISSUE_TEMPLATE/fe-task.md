---
name: "🎨 Task de Front-end ([FE] [RFXXX])"
about: "Criação de card de Front-end (Next.js 15 / UI / UX) seguindo o padrão ADR-004"
title: "[FE] [RFXXX] <Título do Requisito> (Essencial | Importante | Desejável)"
labels: ["frontend", "portal"]
assignees: []
---

## 1. Identificação da Task (`ADR-004`)

- **Responsável Principal:** Luiz Gustavo (Front-end / UI-UX / QA)
- **Requisito Funcional (`RF`):** `RF-XX` ([`docs/01-product-specs.md`](../../docs/01-product-specs.md))
- **Caso de Uso (`UC`):** `UC-XX` ([`docs/use-cases/README.md`](../../docs/use-cases/README.md))
- **Branch Oficial:** `feat/fe/rfxxx-<slug>`

## 2. Telas e Frames do Figma (`docs/design/README.md`)

- **Número(s) da(s) Tela(s) (`01`–`30` / `W01`–`W15`):** 
- **Node ID(s) no Figma (`P8Pf9aZiagXQulJpP2guqz`):** 
- **Exports PNG de Referência (`docs/design/exports/`):** 
- **Divergências aplicáveis (`D1–D13`):** 

## 3. Endpoints Consumidos (`docs/api/openapi.yaml`)

- `GET / POST / PATCH / PUT /api/v1/...`

## 4. Critérios de Aceite e Checklist `[FE]`

- [ ] Todos os campos, máscaras e mensagens de erro literais do `RF` implementados
- [ ] Divergências `D1–D13` resolvidas a favor do requisito
- [ ] Os 4 estados de interface (`loading`, `empty`, `error`, `success`) implementados
- [ ] Layout responsivo validado em `390 px` (Mobile) e `1440 px` (Desktop) com tokens `.sosp-`
- [ ] Acessibilidade `WCAG 2.1 AA` validada (teclado, foco, `<label>`, `axe-core`)
- [ ] Testes automatizados da tela/fluxo passando

