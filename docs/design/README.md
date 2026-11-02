# Design — Índice das 30 Telas

> **Projeto:** SOSP — Sistema de Orientação para Serviços Públicos
> **Versão:** 1.1.0 · **Data:** 31/10/2026 · **Status:** Em revisão
> **Autores:** Arthur Franco e Luiz Gustavo — CESMAC
> **Protótipo oficial:** [Figma `SOSP`](https://www.figma.com/design/P8Pf9aZiagXQulJpP2guqz/SOSP?node-id=0-1) · **Acesso somente visualização**
> **Documentos irmãos:** [Pilar 0](../README.md) · [Pilar 1](../01-product-specs.md) · [Pilar 2](../02-design-ux.md) · [Casos de uso](../use-cases/README.md)

---

## Sumário

1. [Por que este índice existe](#1-por-que-este-índice-existe)
2. [Como usar](#2-como-usar)
3. [Legenda](#3-legenda)
4. [Telas do Cidadão — 15 (Web + Mobile)](#4-telas-do-cidadão--15-web--mobile)
5. [Telas do Servidor, Administrativas e Transversais — 15 (Web)](#5-telas-do-servidor-administrativas-e-transversais--15-web)
6. [Rastreabilidade tela → RF → UC](#6-rastreabilidade-tela--rf--uc)
7. [Regras de nomenclatura no Figma](#7-regras-de-nomenclatura-no-figma)
8. [Governança do índice](#8-governança-do-índice)
9. [Exportações](#9-exportações)

---

## 1. Por que este índice existe

O Figma é a **fonte oficial de aparência** do SOSP. O sistema possui **30 telas no total** (totalizando 45 frames no Figma), divididas em:

- **15 telas do Cidadão (`01`–`15`):** web (`1440 px`) com suporte responsivo para celulares (`390 px`), representadas no Figma tanto na versão mobile quanto na versão web (`W01`–`W15`);
- **5 telas do Servidor (`16`–`20`):** web (`1440 px`), voltadas para a rotina de atendimento;
- **6 telas Administrativas (`21`–`26`):** web (`1440 px`), voltadas para a governança da plataforma;
- **4 telas Transversais (`27`–`30`):** web (`1440 px`), cobrindo estados que protegem a jornada (erro Gov.br, sessão expirada, confirmações críticas e visualização de PDFs).

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
| **#** | Número estável da tela (`01`–`30`). As 15 telas do cidadão (`01`–`15`) possuem frame Mobile e frame Web (`W01`–`W15`) |
| **Tela** | Nome funcional, em português, sem jargão de ferramenta |
| **RF** | Requisito funcional principal; `—` quando é tela de apoio |
| **UC** | Caso de uso correspondente; `—` quando é estado ou variação |
| **Status** | `Pronta`, `Em ajuste`, `Pendente` ou `v2.0` |
| **Node ID** | Identificador oficial do frame no Figma (`P8Pf9aZiagXQulJpP2guqz`) |

**Status**

| Status | O que significa | Ação |
|---|---|---|
| **Pronta** | Tela completa, com estados e conteúdo de exemplo | Pode ser implementada |
| **Em ajuste** | Existe, mas tem divergência aberta (D1–D13) | Implementar somente após a decisão |
| **Pendente** | Ainda não desenhada | Não implementar; cobrar design |
| **v2.0** | Fora do MVP; existe como referência | Implementar apenas com flag ligada |

---

## 4. Telas do Cidadão — 15 (Web + Mobile)

As **15 telas do cidadão (`01`–`15`)** são **web (`1440 px`) com suporte responsivo para celulares (`390 px`)**. No Figma (`02 · Telas`, ID `5:5`), cada uma dessas 15 telas possui dois frames: a visualização mobile (`01`–`15`) e a visualização desktop (`01 · Web`–`15 · Web`, referenciadas como `W01`–`W15`).

| # | Tela do Cidadão | RF | UC | Status | Node ID (Mobile `390px`) | Node ID (Web `1440px`) |
|---|---|---|---|---|---|---|
| 01 / W01 | Login Gov.br (e CPF + senha) | RF-02 | UC-02 | Em ajuste (D6, D10) | `8:172` | `7:11658` |
| 02 / W02 | Cadastro / Criar conta | RF-01 | UC-01 | Em ajuste (D10) | `8:217` | `7:11756` |
| 03 / W03 | Home do Cidadão | RF-06 | UC-06 | Pronta | `8:292` | `7:11882` |
| 04 / W04 | Busca de serviços | RF-06 | UC-06 | Em ajuste (D2, D3, D9) | `8:459` | `7:12065` |
| 05 / W05 | Ficha do serviço | RF-06 | UC-07 | Em ajuste (D1, D4, D5, D7, D8) | `8:571` | `7:12265` |
| 06 / W06 | Variação do serviço | RF-06 | UC-06, UC-07 | Pronta | `7:105` | `7:12421` |
| 07 / W07 | Guia e checklist | RF-07 | UC-08 | Pronta | `7:194` | `7:12582` |
| 08 / W08 | Alerta PCD / Idoso | RF-07 | UC-08 | Pronta | `7:310` | `7:12760` |
| 09 / W09 | Agendamento | RF-08 | UC-09, UC-10 | Em ajuste (D6) | `7:389` | `7:12912` |
| 10 / W10 | Meus pedidos / Confirmação | RF-08, RF-09 | UC-09, UC-11 | Pronta | `7:572` | `7:13141` |
| 11 / W11 | Anexar documento | RF-09 | UC-12 | Pronta | `7:741` | `7:13404` |
| 12 / W12 | Avaliação | RF-10 | UC-13 | v2.0 | `7:818` | `7:13545` |
| 13 / W13 | FAQ / Assistente | RF-11 | UC-14 | Pronta | `7:896` | `7:13720` |
| 14 / W14 | Preferências | RF-13 | UC-16 | v2.0 | `7:986` | `7:13889` |
| 15 / W15 | Perfil (`01–15`) / Acompanhamento (`Web`) | RF-01, RF-09 | UC-01, UC-11 | Pronta | `7:1098` | `7:14044` |

**Observações — Telas do Cidadão (`01`–`15`)**

- As telas `01`, `02`, `04`, `05` e `09` têm divergência aberta com o requisito; a decisão está na [matriz D1–D13](../01-product-specs.md#7-matriz-de-divergências). Implementar a versão do requisito, não a do frame, até a divergência ser encerrada.
- As telas `12` (Avaliação) e `14` (Preferências) pertencem ao escopo da v2.0 (`FEATURE_REVIEWS_ENABLED` e `FEATURE_PUSH_ENABLED`).

---

## 5. Telas do Servidor, Administrativas e Transversais — 15 (Web)

As demais **15 telas (`16`–`30`)** completam as **30 telas do sistema** e são operadas em interface web desktop (`1440 × 1081 px`), divididas em três grupos:

### 5.1 Telas do Servidor — 5 (`16`–`20`)

| # | Tela (Frame no Figma) | RF | UC | Status | Node ID (`1440px`) |
|---|---|---|---|---|---|
| 16 | 16 · Dashboard do Servidor | RF-14 | UC-17 | Pronta | `7:1269` |
| 17 | 17 · Gerenciar Agendamentos | RF-08 | UC-09, UC-10 | Pronta | `7:1742` |
| 18 | 18 · Atender Protocolos | RF-09 | UC-11, UC-12 | Pronta | `7:2177` |
| 19 | 19 · Catálogo de Serviços | RF-05 | UC-05 | Pronta | `7:2538` |
| 20 | 20 · Relatórios Gerenciais | RF-14 | UC-17 | Em ajuste (D13) | `7:2981` |

### 5.2 Telas Administrativas — 6 (`21`–`26`)

| # | Tela (Frame no Figma) | RF | UC | Status | Node ID (`1440px`) |
|---|---|---|---|---|---|
| 21 | 21 · Órgãos | RF-03 | UC-03 | Pronta | `7:3322` |
| 22 | 22 · Unidades | RF-04 | UC-04 | Pronta | `7:3821` |
| 23 | 23 · Catálogo Global | RF-05 | UC-05 | Pronta | `7:4300` |
| 24 | 24 · Usuários Internos | RF-12 | UC-15 | Pronta | `7:4780` |
| 25 | 25 · FAQ e Conteúdo | RF-11 | UC-14 | Pronta | `7:6630` |
| 26 | 26 · Relatórios e Auditoria | RF-14 | UC-17 | Em ajuste (D13) | `7:7074` |

### 5.3 Telas Transversais — 4 (`27`–`30`)

| # | Tela (Frame no Figma) | RF | UC | Status | Node ID (`1440px`) |
|---|---|---|---|---|---|
| 27 | 27 · Erro Gov.br | RF-02 | UC-02 | Pronta | `7:7578` |
| 28 | 28 · Sessão Expirada | RF-02 | UC-02 | Pronta | `7:7675` |
| 29 | 29 · Confirmações Críticas | RF-01, RF-08 | UC-01, UC-10 | Pronta | `7:7801` |
| 30 | 30 · Visualização de PDFs | RF-07, RF-08, RF-14 | UC-08, UC-09, UC-17 | Pronta | `7:8181` |

**Observações (`16`–`30`)**

- As telas `20` e `26` entregam os relatórios do MVP; o painel de avaliações fica oculto por `FEATURE_REVIEWS_ENABLED` até o RF-10 entrar no escopo (D13).
- As telas `27`–`30` são transversais e sustentam estados críticos da jornada (modal informativo/erro Gov.br, expiração de sessão em 30 minutos, confirmação de ações destrutivas e visualização de comprovantes/guias em PDF).

---

## 6. Rastreabilidade tela → RF → UC

### 6.1 Por requisito

| RF | Telas (`01`–`30`) | Telas Web (`W01`–`W15`) | UC |
|---|---|---|---|
| RF-01 | 02, 15, 29 | W02 | UC-01 |
| RF-02 | 01, 27, 28 | W01 | UC-02 |
| RF-03 | 21 | — | UC-03 |
| RF-04 | 22 | — | UC-04 |
| RF-05 | 19, 23 | — | UC-05 |
| RF-06 | 03, 04, 05, 06 | W03, W04, W05, W06 | UC-06, UC-07 |
| RF-07 | 07, 08, 30 | W07, W08 | UC-08 |
| RF-08 | 09, 17, 29, 30 | W09, W10 | UC-09, UC-10 |
| RF-09 | 10, 11, 18 | W10, W11, W15 | UC-11, UC-12 |
| RF-10 | 12 | W12 | UC-13 |
| RF-11 | 13, 25 | W13 | UC-14 |
| RF-12 | 24 | — | UC-15 |
| RF-13 | 14 | W14 | UC-16 |
| RF-14 | 16, 20, 26, 30 | — | UC-17 |

**Cobertura:** todos os RFs têm telas correspondentes no Figma. Os frames `12`/`W12` (RF-10) e `14`/`W14` (RF-13) estão desenhados como referência para a v2.0 e permanecem desabilitados por feature flag no MVP.

### 6.2 Por caso de uso

| UC | Telas |
|---|---|
| UC-01 | 02, 15, 29, W02 |
| UC-02 | 01, 27, 28, W01 |
| UC-03 | 21 |
| UC-04 | 22 |
| UC-05 | 19, 23 |
| UC-06 | 03, 04, 06, W03, W04, W06 |
| UC-07 | 05, 06, W05, W06 |
| UC-08 | 07, 08, 30, W07, W08 |
| UC-09 | 09, 17, 30, W09, W10 |
| UC-10 | 09, 17, 29, W09 |
| UC-11 | 10, 18, W10, W15 |
| UC-12 | 11, 18, W11, W15 |
| UC-13 | 12, W12 |
| UC-14 | 13, 25, W13 |
| UC-15 | 24 |
| UC-16 | 14, W14 |
| UC-17 | 16, 20, 26, 30 |

### 6.3 Frames de apoio e Design System no Figma

Além das 30 telas numeradas (45 frames), o arquivo do Figma contém os seguintes frames estruturais:

| Página / Seção | Frame | Node ID |
|---|---|---|
| `00 · Visão geral` (`0:1`) | Capa / SOSP — Design System e Telas | `5:445` |
| `01 · Design System` (`5:4`) | Masters / Componentes | `5:137` |
| `01 · Design System` (`5:4`) | Fundamentos / SOSP | `5:231` |
| `01 · Design System` (`5:4`) | Componentes / SOSP | `5:314` |
| `02 · Telas` (`5:5`) | Abertura da galeria | `8:144` |
| `02 · Telas` (`5:5`) | Abertura · Cidadão Web | `7:11624` |

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

| Página | Node ID | Conteúdo |
|---|---|---|
| `00 · Visão geral` | `0:1` | Capa (`5:445`), contexto, versão e apresentação do SOSP |
| `01 · Design System` | `5:4` | Masters (`5:137`), Fundamentos (`5:231`) e Componentes (`5:314`) |
| `02 · Telas` | `5:5` | Telas `01`–`30` (Cidadão, Servidor, Governança e Estados) e `01 · Web`–`15 · Web` (`W01`–`W15`) |

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

- [ ] 30 telas listadas (15 do cidadão web+mobile, 5 do servidor, 6 administrativas e 4 transversais — totalizando 45 frames no Figma).
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
