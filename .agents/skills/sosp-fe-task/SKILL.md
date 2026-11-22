---
name: sosp-fe-task
description: >-
  Use this skill when the user asks to implement, update, or review a Front-end
  task ([FE] [RFXXX]) or screen (01 to 30 / W01 to W15) in the SOSP Next.js 15
  portal (portal/). Guides the agent through requirement lookup, divergence matrix
  check (D1-D13), Figma visual inspection, OpenAPI typing, 4-state UI implementation,
  and WCAG 2.1 AA validation.
---

# SOSP Front-end Task Workflow (`[FE] [RFXXX]`)

Esta skill define o procedimento passo a passo obrigatório para implementar qualquer task de Front-end (`[FE] [RFXXX]`) no portal `Next.js 15` (`portal/`) do projeto SOSP.

## Passo 1: Identificar o Requisito, Caso de Uso e Telas

1. Localize o `RF` solicitado (`RF-01` a `RF-14`) em [`docs/01-product-specs.md`](../../../docs/01-product-specs.md) e o Caso de Uso correspondente (`UC-01` a `UC-17`) em [`docs/use-cases/README.md`](../../../docs/use-cases/README.md).
2. Extraia:
   - Todos os **campos de formulário**, tipos, limites de caracteres, obrigatoriedade e máscaras (`CPF`, `CEP`, `Celular`, `Data`, `Hora`, `Moeda`);
   - Todas as **mensagens de erro e confirmação literais em português** (ex.: `"Campo(s) obrigatório(s) não preenchido(s)"`, `"As senhas não coincidem."`, `"Nenhum serviço encontrado. Tente outro termo ou categoria."`);
   - Todas as **Regras de Negócio (`RN-01` a `RN-40`)** e **Critérios de Aceite (`CA-01` a `CA-21`)** vinculados ao requisito.

## Passo 2: Verificar a Matriz de Divergências (`D1–D13`)

1. Consulte [`docs/01-product-specs.md#7-matriz-de-divergências`](../../../docs/01-product-specs.md#7-matriz-de-divergências) antes de olhar o layout.
2. Verifique se as telas do requisito possuem divergência mapeada:
   - **Telas `01 / W01` e `27` (`D6`, `D10`):** implementar login local por `CPF + senha` e modal informativo no botão `"Entrar com Gov.br"`.
   - **Tela `02 / W02` (`D10`, `RF-01`):** implementar todos os 19 campos do cadastro manual com autopreenchimento `ViaCEP` + fallback `IBGE` (sem duplicar campo de Data de Nascimento).
   - **Tela `04 / W04` (`D2`, `D3`, `D9`):** exibir os 4 filtros (`Categoria`, `Órgão`, `Canal`, `Município`), paginação de 10 itens por página e mensagem literal de estado vazio.
   - **Tela `05 / W05` (`D1`, `D4`, `D7`, `D8`):** exibir os 8 blocos da ficha, mapa condicional (`RN-10`), badge consistente de canal e os 3 botões (`Ver Passo-a-Passo`, `Agendar`, `Avaliar` sob feature flag).
   - **Telas `20` e `26` (`D13`):** ocultar painel de média de avaliações enquanto `NEXT_PUBLIC_FEATURE_REVIEWS_ENABLED=false`.

## Passo 3: Inspecionar os Frames Exportados do Figma

1. Consulte o índice de telas em [`docs/design/README.md`](../../../docs/design/README.md) e o manifesto [`docs/design/exports/manifest.json`](../../../docs/design/exports/manifest.json) para localizar os arquivos PNG da tela.
2. Use a ferramenta `read_file` para **visualizar diretamente as imagens PNG** em `docs/design/exports/`:
   - Para telas do Cidadão (`01` a `15`), inspecione **ambas** as versões: `Cidadão/Mobile/` (`390 px`) e `Cidadão/Web/` (`1440 px`).
   - Para telas do Servidor (`16` a `20`), Administrador (`21` a `26`) e Transversais (`27` a `30`), inspecione a versão Desktop (`1440 px`).
3. Reproduza a hierarquia visual, espaçamentos e tokens de cor definidos em [`docs/02-design-ux.md`](../../../docs/02-design-ux.md).

## Passo 4: Alinhar Contrato com o `openapi.yaml`

1. Abra [`docs/api/openapi.yaml`](../../../docs/api/openapi.yaml) e localize os endpoints consumidos pela tela.
2. Crie ou atualize as interfaces TypeScript em `portal/src/types/` (ou no módulo da feature) espelhando os nomes em `camelCase` do contrato OpenAPI e o formato de erro `RFC 7807` (`ProblemDetails`).
3. Verifique se o recurso depende de alguma feature flag em [`.env.example`](../../../.env.example) (`NEXT_PUBLIC_FEATURE_*`).

## Passo 5: Implementar Componentes, Páginas e os 4 Estados

1. Construa os componentes e páginas em `portal/` utilizando classes e tokens `.sosp-`.
2. Garanta a implementação explícita dos **4 estados de interface** ([`docs/02-design-ux.md#4-matriz-de-estados-de-interface`](../../../docs/02-design-ux.md#4-matriz-de-estados-de-interface)):
   - `loading` (skeletons com `aria-busy="true"`);
   - `empty` (estado vazio com mensagem literal do requisito);
   - `error` (erros de campo com `aria-invalid="true"` e `aria-describedby`, além de tratamento para `400`, `401`, `403`, `404`, `409`, `422`, `429` e `500`);
   - `success` (estado carregado e feedbacks de confirmação).
3. Valide acessibilidade `WCAG 2.1 AA`: rótulos `<label>`, navegação por teclado (`Tab`, `Enter`, `Escape`), foco visível e contraste mínimo `4.5:1`.

## Passo 6: Verificação e Testes de Front-end

1. Escreva ou atualize os testes unitários/integração (Vitest / Testing Library / Playwright) cobrindo o fluxo principal e os fluxos alternativos/exceções do Caso de Uso.
2. Execute a checagem de tipos, lint e testes no `portal/` antes de concluir a task.

