# Design — Índice das 45 Telas

> **Projeto:** SOSP — Sistema de Orientação para Serviços Públicos
> **Versão:** 1.1.0 · **Data:** 31/10/2026 · **Status:** Em revisão
> **Autores:** Equipe de Engenharia de Software — CESMAC
> **Protótipo oficial:** [Figma `SOSP`](https://www.figma.com/design/P8Pf9aZiagXQulJpP2guqz/SOSP?node-id=0-1) · **Acesso somente visualização**
> **Documentos irmãos:** [Pilar 0](../README.md) · [Pilar 1](../01-product-specs.md) · [Pilar 2](../02-design-ux.md) · [Casos de uso](../use-cases/README.md)

---

## Sumário

1. [Por que este índice existe](#1-por-que-este-índice-existe)
2. [Como usar](#2-como-usar)
3. [Legenda](#3-legenda)
4. [Telas mobile — 30](#4-telas-mobile--30)
5. [Telas web — 15](#5-telas-web--15)
6. [Rastreabilidade tela → RF → UC](#6-rastreabilidade-tela--rf--uc)
7. [Regras de nomenclatura no Figma](#7-regras-de-nomenclatura-no-figma)
8. [Governança do índice](#8-governança-do-índice)
9. [Exportações](#9-exportações)

---

## 1. Por que este índice existe

O Figma é a **fonte oficial de aparência** do SOSP. Ele tem 45 telas: 30 mobile, que definem o comportamento principal no celular, e 15 web, que cobrem a experiência desktop do cidadão e o back-office.

Um arquivo Figma sem índice é uma coleção de frames. O índice faz três coisas que o arquivo sozinho não faz:

1. **Liga cada tela a um requisito e a um caso de uso.** Sem isso, não se sabe se uma tela órfã pode ser apagada ou se falta uma tela para um RF.
2. **Dá um nome estável ao nó.** O `node-id` muda quando o frame é recriado; o número da tela (`04`) e o nome (`Busca e resultados`) permanecem.
3. **Separa o que é MVP do que é v2.0.** Avaliação e notificações por push aparecem no protótipo, mas estão fora do escopo e só existem com flag.

**Relação com os outros artefatos**

| Artefato | Papel | O que vale em conflito |
|---|---|---|
| [Pilar 1](../01-product-specs.md) | Comportamento, regra e escopo | **Vale o requisito** |
| [Pilar 2](../02-design-ux.md) | Princípios, tokens, componentes e estados | Vale para decisão de design |
| **Figma** | Aparência, hierarquia, espaçamento e conteúdo de tela | Vale para aparência |
| [`Prototipo/`](../../Prototipo/) | Implementação HTML do recorte RF-06 | Não é fonte; é artefato derivado |
| [`DesignSystem/`](../../DesignSystem/index.html) | Catálogo vivo de tokens e componentes | Vale para componente e token |

**Regra:** o índice não substitui o Figma. Ele diz **onde** cada tela está e **por que** existe. A aparência continua sendo lida no arquivo.

---

## 2. Como usar

### 2.1 Para implementar uma tela

1. Localize a tela pelo número ou pelo RF na [§6](#6-rastreabilidade-tela--rf--uc).
2. Abra o nó no Figma pelo link da coluna **Node ID**.
3. Leia o UC correspondente em [Casos de uso](../use-cases/README.md) para o comportamento.
4. Leia o [Pilar 2 §4](../02-design-ux.md#4-matriz-de-estados-de-interface) para os estados de interface.
5. Confira os tokens no [Design System](../../DesignSystem/index.html); não invente cor, espaçamento ou tipografia.

### 2.2 Para revisar design

1. Compare a tela com o RF e o CA, não com o gosto pessoal.
2. Verifique os quatro estados: vazio, loading, erro e sucesso.
3. Verifique acessibilidade: contraste, foco visível, rótulo, ordem de leitura e alvo de toque.
4. Se a tela divergir do requisito, abra ou atualize uma entrada na [matriz de divergências](../01-product-specs.md#7-matriz-de-divergências).

### 2.3 Para atualizar o índice

1. Crie ou renomeie o frame no Figma seguindo a [§7](#7-regras-de-nomenclatura-no-figma).
2. Copie o `node-id` do frame (formato `123:456`).
3. Atualize a linha correspondente neste arquivo.
4. Se a tela for nova, vincule a um RF e a um UC. Tela sem RF é tela órfã: ou o requisito está incompleto, ou a tela não deveria existir.
5. Atualize o [CHANGELOG](../../CHANGELOG.md) se a mudança afetar escopo ou entrega.

---

## 3. Legenda

| Campo | Significado |
|---|---|
| **#** | Número estável da tela. Mobile usa `01`–`30`; web usa `W01`–`W15` |
| **Tela** | Nome funcional, em português, sem jargão de ferramenta |
| **RF** | Requisito funcional principal; `—` quando é tela de apoio |
| **UC** | Caso de uso correspondente; `—` quando é estado ou variação |
| **Status** | `Pronta`, `Em ajuste`, `Pendente` ou `v2.0` |
| **Node ID** | Identificador do frame no Figma; `<preencher>` até a exportação oficial |

**Status**

| Status | O que significa | Ação |
|---|---|---|
| **Pronta** | Tela completa, com estados e conteúdo de exemplo | Pode ser implementada |
| **Em ajuste** | Existe, mas tem divergência aberta (D1–D13) | Implementar somente após a decisão |
| **Pendente** | Ainda não desenhada | Não implementar; cobrar design |
| **v2.0** | Fora do MVP; existe como referência | Implementar apenas com flag ligada |

---

## 4. Telas mobile — 30

A referência de comportamento é **390 px**. A versão mobile é a que o cidadão usa na rua, com rede instável; toda tela precisa tolerar latência, perda de conexão e retomada.

| # | Tela | RF | UC | Status | Node ID |
|---|---|---|---|---|---|
| 01 | Login — CPF + senha e Gov.br (futuro v2.0) | RF-02 | UC-02 | Pronta | `<preencher>` |
| 02 | Cadastro manual do cidadão | RF-01 | UC-01 | Pronta | `<preencher>` |
| 03 | Home e atalhos por categoria | RF-06 | UC-06 | Pronta | `<preencher>` |
| 04 | Busca e resultados | RF-06 | UC-06 | Em ajuste (D2, D3, D9) | `<preencher>` |
| 05 | Ficha do serviço | RF-06 | UC-07 | Em ajuste (D1, D4, D5, D7) | `<preencher>` |
| 06 | Guia passo a passo | RF-07 | UC-08 | Pronta | `<preencher>` |
| 07 | Checklist e PDF | RF-07 | UC-08 | Pronta | `<preencher>` |
| 08 | Agendamento — unidade e data | RF-08 | UC-09 | Pronta | `<preencher>` |
| 09 | Agendamento — horários | RF-08 | UC-09 | Pronta | `<preencher>` |
| 10 | Agendamento confirmado e protocolo | RF-08, RF-09 | UC-09, UC-11 | Pronta | `<preencher>` |
| 11 | Meus pedidos | RF-09 | UC-11 | Pronta | `<preencher>` |
| 12 | Protocolo — linha do tempo e anexos | RF-09 | UC-11, UC-12 | Pronta | `<preencher>` |
| 13 | FAQ e dúvidas | RF-11 | UC-14 | Pronta | `<preencher>` |
| 14 | Perfil do cidadão | RF-01 | UC-01 | Pronta | `<preencher>` |
| 15 | Anexar documento | RF-09 | UC-12 | Pronta | `<preencher>` |
| 16 | Confirmação de e-mail | RF-01 | UC-01 | Pronta | `<preencher>` |
| 17 | Recuperar senha (servidor) | RF-02 | UC-02 | Pendente | `<preencher>` |
| 18 | Ajuda e acessibilidade | — | — | Pendente | `<preencher>` |
| 19 | Busca sem resultado | RF-06 | UC-06 | Em ajuste (D9) | `<preencher>` |
| 20 | Estado de erro e offline | — | — | Pendente | `<preencher>` |
| 21 | Sobre o órgão responsável | RF-03 | UC-03 | Pendente | `<preencher>` |
| 22 | Mapa e unidade de atendimento | RF-04, RF-06 | UC-07 | Em ajuste (D4) | `<preencher>` |
| 23 | Avaliação do atendimento | RF-10 | UC-13 | v2.0 | `<preencher>` |
| 24 | Remarcar agendamento | RF-08 | UC-10 | Pronta | `<preencher>` |
| 25 | Cancelar agendamento | RF-08 | UC-10 | Pronta | `<preencher>` |
| 26 | Categorias de serviço | RF-06 | UC-06 | Pronta | `<preencher>` |
| 27 | Filtros de busca | RF-06 | UC-06 | Em ajuste (D3) | `<preencher>` |
| 28 | Detalhe do documento exigido | RF-05, RF-06 | UC-07 | Pendente | `<preencher>` |
| 29 | Cadastro concluído | RF-01 | UC-01 | Pronta | `<preencher>` |
| 30 | Onboarding acessível | — | — | Pendente | `<preencher>` |

**Observações mobile**

- As telas 04, 05, 19, 22 e 27 têm divergência aberta com o requisito; a decisão está na [matriz D1–D13](../01-product-specs.md#7-matriz-de-divergências). Implementar a versão do requisito, não a do frame, até a divergência ser encerrada.
- As telas 23 (avaliação) e 17 (recuperação de senha interna) não fazem parte da jornada pública do MVP. A 23 só existe com `FEATURE_REVIEWS_ENABLED=true`; a 17 é back-office, não portal do cidadão.
- As telas 18, 20, 21, 28 e 30 são telas de apoio. Se o tempo apertar, elas são as primeiras candidatas a corte — mas os estados de erro e vazio das telas críticas continuam obrigatórios (Pilar 2 §4).

---

## 5. Telas web — 15

A referência de comportamento é **1280 px**, com grid de 12 colunas e largura máxima de 1200 px. As versões web não são "a tela mobile esticada": elas reorganizam a informação para leitura em tela grande e para operação densa no back-office.

| # | Tela | RF | UC | Status | Node ID |
|---|---|---|---|---|---|
| W01 | Home | RF-06 | UC-06 | Pronta | `<preencher>` |
| W02 | Busca e resultados | RF-06 | UC-06 | Em ajuste (D2, D3, D9) | `<preencher>` |
| W03 | Ficha do serviço | RF-06 | UC-07 | Em ajuste (D1, D4, D5, D7) | `<preencher>` |
| W04 | Guia e checklist | RF-07 | UC-08 | Pronta | `<preencher>` |
| W05 | Agendamento | RF-08 | UC-09, UC-10 | Pronta | `<preencher>` |
| W06 | Protocolo e acompanhamento | RF-09 | UC-11, UC-12 | Pronta | `<preencher>` |
| W07 | Meus pedidos | RF-09 | UC-11 | Pronta | `<preencher>` |
| W08 | Login e cadastro | RF-01, RF-02 | UC-01, UC-02 | Pronta | `<preencher>` |
| W09 | FAQ e ajuda | RF-11 | UC-14 | Pronta | `<preencher>` |
| W10 | Perfil do cidadão | RF-01 | UC-01 | Pronta | `<preencher>` |
| W11 | Back-office — dashboard | RF-14 | UC-17 | Pronta | `<preencher>` |
| W12 | Back-office — catálogo de serviços | RF-05 | UC-05 | Pronta | `<preencher>` |
| W13 | Back-office — órgãos e unidades | RF-03, RF-04 | UC-03, UC-04 | Pronta | `<preencher>` |
| W14 | Back-office — usuários internos | RF-12 | UC-15 | Pronta | `<preencher>` |
| W15 | Back-office — relatórios | RF-14 | UC-17 | Em ajuste (D13) | `<preencher>` |

**Observações web**

- O back-office é operado em desktop; não há versão mobile prevista para W11–W15. O Django Admin pode ser usado em tablet, mas não é requisito.
- W15 entrega os relatórios do MVP. O painel de avaliações fica oculto por `FEATURE_REVIEWS_ENABLED` até o RF-10 entrar no escopo (D13).
- W02 e W03 usam paginação explícita de 10 itens, conforme RN-05; a rolagem contínua do frame mobile não vale para web.

---

## 6. Rastreabilidade tela → RF → UC

### 6.1 Por requisito

| RF | Telas mobile | Telas web | UC |
|---|---|---|---|
| RF-01 | 02, 14, 16, 29 | W08, W10 | UC-01 |
| RF-02 | 01, 17 | W08 | UC-02 |
| RF-03 | 21 | W13 | UC-03 |
| RF-04 | 22 | W13 | UC-04 |
| RF-05 | 28 | W12 | UC-05 |
| RF-06 | 03, 04, 19, 22, 26, 27 | W01, W02, W03 | UC-06, UC-07 |
| RF-07 | 06, 07 | W04 | UC-08 |
| RF-08 | 08, 09, 10, 24, 25 | W05 | UC-09, UC-10 |
| RF-09 | 10, 11, 12, 15 | W06, W07 | UC-11, UC-12 |
| RF-10 | 23 | — | UC-13 |
| RF-11 | 13 | W09 | UC-14 |
| RF-12 | — | W14 | UC-15 |
| RF-13 | — | — | UC-16 |
| RF-14 | — | W11, W15 | UC-17 |

**Cobertura:** todos os RFs do MVP têm ao menos uma tela ou uma decisão explícita de que o RF é de back-office/API. RF-13 não tem tela no MVP porque push e preferências ficam para a v2.0; a tela de preferências só existe quando `FEATURE_PUSH_ENABLED=true`.

### 6.2 Por caso de uso

| UC | Telas |
|---|---|
| UC-01 | 02, 14, 16, 29, W08, W10 |
| UC-02 | 01, 17, W08 |
| UC-03 | 21, W13 |
| UC-04 | 22, W13 |
| UC-05 | 28, W12 |
| UC-06 | 03, 04, 19, 26, 27, W01, W02 |
| UC-07 | 05, 22, 28, W03 |
| UC-08 | 06, 07, W04 |
| UC-09 | 08, 09, 10, W05 |
| UC-10 | 24, 25, W05 |
| UC-11 | 10, 11, 12, W06, W07 |
| UC-12 | 12, 15, W06 |
| UC-13 | 23 |
| UC-14 | 13, W09 |
| UC-15 | W14 |
| UC-16 | — |
| UC-17 | W11, W15 |

### 6.3 Telas sem requisito

As telas 18 (Ajuda e acessibilidade), 20 (Erro e offline) e 30 (Onboarding acessível) são **transversais**: não pertencem a um RF específico, mas sustentam RNF-01, RNF-02 e RNF-06. Elas não são escopo independente; entram como estado ou apoio das telas críticas.

---

## 7. Regras de nomenclatura no Figma

### 7.1 Nome do frame

```text
<numero> · <nome funcional> · <plataforma>
```

Exemplos:

```text
04 · Busca e resultados · Mobile
04 · Busca e resultados · Web
W12 · Catálogo de serviços · Web
```

**Regras**

1. O número é o mesmo deste índice. Não renumere uma tela existente; crie a próxima.
2. O nome funcional é em português e descreve o objetivo, não o layout (`Ficha do serviço`, não `Card branco com texto`).
3. A plataforma é `Mobile` ou `Web`.
4. Não use prefixos de status no nome (`v2`, `final`, `novo`). Status é campo deste índice, não do frame.
5. Variantes de estado (`vazio`, `erro`, `loading`) são **variantes do componente ou frames filhos**, não telas numeradas. A exceção é a tela 19, que é um estado de página inteira.

### 7.2 Organização das páginas no Figma

| Página | Conteúdo |
|---|---|
| `00 · Capa e índice` | Contexto, versão, links e legenda |
| `01 · Mobile` | Telas 01–30 |
| `02 · Web` | Telas W01–W10 |
| `03 · Back-office` | Telas W11–W15 |
| `04 · Componentes` | Componentes e variantes do Design System |
| `05 · Tokens` | Cores, tipografia, espaçamento, raios e sombras |
| `06 · Fluxos` | Fluxogramas das jornadas críticas |
| `07 · Arquivadas` | Telas antigas, preservadas para histórico |

### 7.3 Anotações de acessibilidade

Toda tela crítica deve ter, no frame ou em uma nota adjacente:

- Ordem de foco e pontos de parada de teclado.
- Rótulo acessível de ícones e botões.
- Contraste mínimo de 4,5:1 para texto e 3:1 para componente.
- Alvo de toque mínimo de 44 × 44 px no mobile.
- Texto alternativo de imagens e mapas.

**Regra:** anotação de acessibilidade não é opcional. Uma tela sem anotação não está `Pronta`.

---

## 8. Governança do índice

| Evento | Ação | Responsável | Prazo |
|---|---|---|---|
| Nova tela | Adicionar linha, vincular RF/UC e preencher node-id | Design | Na mesma entrega |
| Tela removida | Marcar como `Arquivada` e mover o frame para `07 · Arquivadas` | Design | Na mesma entrega |
| Mudança de requisito | Revisar RF/UC da tela e abrir divergência se necessário | PO + Design | Até a review |
| Mudança de node-id | Atualizar a linha e registrar no CHANGELOG | Design | Na mesma entrega |
| Tela sem RF | Abrir divergência ou remover | PO | Até a review |
| Exportação | Atualizar `exports/` e a data | Design | Por release |

**Checklist de consistência (mensal)**

- [ ] 45 telas listadas: 30 mobile + 15 web.
- [ ] Toda tela `Pronta` tem node-id preenchido.
- [ ] Toda tela tem RF/UC ou justificativa de transversalidade.
- [ ] Nenhuma tela `v2.0` está no fluxo do MVP.
- [ ] As divergências D1–D13 continuam refletidas no status.
- [ ] Os links deste arquivo abrem o arquivo correto.
- [ ] A exportação mais recente está em [`exports/`](exports/README.md).

---

## 9. Exportações

As exportações ficam em [`exports/`](exports/README.md), com PNG por tela e um PDF consolidado. Elas existem por três motivos:

1. **Continuidade:** o Figma pode mudar de permissão, de owner ou de conteúdo.
2. **Avaliação:** o professor precisa abrir o artefato sem depender de conta.
3. **Evidência:** a versão apresentada fica datada.

**Regra:** a exportação é uma **cópia datada**, não a fonte. Se o Figma e o PNG divergirem, vale o Figma para aparência e o requisito para comportamento. A data e o responsável pela exportação ficam registrados em [`exports/README.md`](exports/README.md).

---

*Índice derivado do [Pilar 1](../01-product-specs.md) e do [Pilar 2](../02-design-ux.md). Tela nova sem RF é sinal de requisito faltando — não de design sobrando.*
