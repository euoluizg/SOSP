---
trigger: always_on
description: Regras de Front-end Next.js 15, Design System .sosp-, divergências D1-D13 e WCAG 2.1 AA para o portal SOSP.
---

# Rules de Front-end e UI/UX — Portal SOSP (`Next.js 15`)

> **Escopo:** Diretório `portal/` e artefatos de interface do SOSP.
> **Responsável Principal:** Luiz Gustavo (Front-end, UI/UX Design e QA).

---

## 1. Arquitetura e Consumo de Dados (`ADR-001`)

1. **Zero Acesso Direto ao Banco de Dados:**
   - O `portal/` (`Next.js 15`, React, TypeScript) **jamais** importa clientes de banco de dados (`pg`, `Prisma`, `@supabase/supabase-js`) nem se conecta diretamente ao PostgreSQL/Supabase.
   - Toda leitura e escrita de dados deve passar exclusivamente pela API REST do Django (`/api/v1/...`), respeitando os schemas de [`docs/api/openapi.yaml`](../../docs/api/openapi.yaml).
2. **Tipagem Estrita:**
   - É proibido usar `any` em TypeScript. Todos os payloads de request, response e erros (`ProblemDetails` — `RFC 7807`) devem ser tipados conforme o `openapi.yaml`.

---

## 2. Design System, Tokens e Componentes (`Pilar 2`)

1. **Tokens CSS e Prefixo `.sosp-`:**
   - Utilize sempre os tokens definidos em [`docs/02-design-ux.md#5-design-tokens`](../../docs/02-design-ux.md#5-design-tokens) e classes utilitárias/componentes com prefixo `.sosp-`.
   - Não espalhe cores hexadecimais hardcoded fora das variáveis CSS oficiais (`--sosp-color-primary: #1351B4`, `--sosp-color-primary-dark: #0F2942`, `--sosp-color-success: #1E8E3E`, `--sosp-color-warning: #F9AB00`, `--sosp-color-danger: #D93025`).
2. **Catálogo das 30 Telas (45 Frames no Figma):**
   - Sempre consulte [`docs/design/README.md`](../../docs/design/README.md) e inspecione os PNGs exportados em [`docs/design/exports/`](../../docs/design/exports/) antes de construir ou alterar qualquer página.
   - **Responsividade Obrigatória (`RNF-05`):**
     - **Telas `01` a `15` (Cidadão):** devem ser 100% responsivas, suportando o layout Mobile (`390 px`) e o layout Web Desktop (`1440 px`, frames `W01`–`W15`).
     - **Telas `16` a `20` (Servidor), `21` a `26` (Administrador) e `27` a `30` (Transversais):** foco operacional em Web Desktop (`1440 px`) com suporte responsivo sem quebra de layout.

---

## 3. Regras de Interface, Mensagens Literais e Divergências (`D1–D13`)

Sempre que um frame exportado do Figma divergir do requisito, **aplique a decisão da Matriz de Divergências (`docs/01-product-specs.md §7`)**:

1. **Login (`01 / W01` e `27` — `D6`, `D10`):**
   - Exibir formulário principal de **CPF + Senha** para Cidadão, Servidor e Administrador.
   - O botão `"Entrar com Gov.br"` deve abrir o modal informativo contendo o texto literal:
     `"A integração com o Gov.br estará disponível em uma futura atualização (v2.0). Utilize seu CPF e senha para entrar."` e o botão `"Entendi, quero usar CPF e senha"`.
2. **Cadastro do Cidadão (`02 / W02` — `RF-01`):**
   - Deve conter todos os 19 campos exigidos no `RF-01`, máscaras de `CPF` (`XXX.XXX.XXX-XX`), `CEP` (`XXXXX-XXX`), `Celular` (`(XX)9XXXX-XXXX`), autopreenchimento `ViaCEP` com fallback manual (`IBGE`), campo condicional `"Qual deficiência"` quando `PCD = Sim`, e validação de idade mínima de 12 anos.
   - Ao clicar em `"Cancelar"`, abrir modal de confirmação com a pergunta literal: `"Todas as alterações serão perdidas. Deseja realmente cancelar?"` (`Sim` / `Não`).
3. **Busca de Serviços (`04 / W04` — `D2`, `D3`, `D9`):**
   - Exibir os **4 filtros oficiais (`RN-04`)**: `Categoria`, `Órgão`, `Canal` (`Online`, `Presencial`, `Híbrido`) e `Município`, combináveis por interseção (`AND`) e sincronizados na query string da URL (`RN-03`).
   - Paginação estrita de **10 itens por página** (`RN-05`).
   - Quando a busca não retornar resultados (`RN-13`), exibir a mensagem literal:
     `"Nenhum serviço encontrado. Tente outro termo ou categoria."`
4. **Ficha Orientativa (`05 / W05` — `D1`, `D4`, `D7`, `D8`):**
   - Exibir obrigatoriamente os **8 blocos** (`O que é`, `Quem tem direito`, `O que levar`, `Como fazer`, `Onde fazer`, `Quando`, `Quanto custa`, `Quanto demora`).
   - Diferenciar documentos **Obrigatórios** e **Opcionais** visualmente e por texto (`RN-09`).
   - Renderizar o bloco de **Mapa** apenas quando a unidade possuir `latitude` e `longitude` (`RN-10`).
   - Exibir os **3 botões de ação**: `"Ver Passo-a-Passo"`, `"Agendar"` e `"Avaliar"` (este último visível apenas se `NEXT_PUBLIC_FEATURE_REVIEWS_ENABLED=true`).

---

## 4. Os 4 Estados de Interface e Acessibilidade (`WCAG 2.1 AA` / `RNF-06`)

1. **Matriz de 4 Estados:** Toda página ou componente que consome dados assíncronos deve implementar:
   - `loading` (skeleton/spinner acessível com `aria-busy="true"`);
   - `empty` (estado vazio orientativo com ação de contorno);
   - `error` (mensagem clara associada ao campo via `aria-describedby` ou banner de erro com botão de tentar novamente);
   - `success` (dados carregados ou feedback de confirmação).
2. **Acessibilidade Obrigatória:**
   - Contraste mínimo de `4.5:1` para textos normais;
   - Navegação completa por teclado (`Tab`, `Shift+Tab`, `Enter`, `Escape` para fechar modais) com anel de foco visível (`:focus-visible`);
   - Todo `<input>`, `<select>` e `<textarea>` deve ter `<label htmlFor="...">` explícito;
   - Alvo de toque mínimo de `44 × 44 px` no mobile;
   - Zero violações críticas no `axe-core`.

