# Exportações do Protótipo

> **Projeto:** SOSP — Sistema de Orientação para Serviços Públicos
> **Versão:** 1.1.0 · **Data:** 31/10/2026 · **Status:** Em revisão
> **Protótipo oficial:** [Figma `SOSP`](https://www.figma.com/design/P8Pf9aZiagXQulJpP2guqz/SOSP?node-id=0-1) · **Acesso somente visualização**
> **Índice de telas:** [docs/design/README.md](../README.md)

---

## Sumário

1. [Para que serve esta pasta](#1-para-que-serve-esta-pasta)
2. [Estado atual](#2-estado-atual)
3. [Como exportar](#3-como-exportar)
4. [Nomenclatura dos arquivos](#4-nomenclatura-dos-arquivos)
5. [Estrutura de pastas](#5-estrutura-de-pastas)
6. [Checklist de exportação](#6-checklist-de-exportação)
7. [Como atualizar](#7-como-atualizar)
8. [Limitações e cuidados](#8-limitações-e-cuidados)

---

## 1. Para que serve esta pasta

O Figma é a fonte oficial de aparência. Esta pasta guarda **cópias datadas** das 45 telas, para que a documentação continue legível quando:

- o arquivo Figma estiver sem permissão de acesso;
- o link mudar de owner ou de plano;
- o conteúdo for alterado depois da apresentação;
- o avaliador precisar abrir o artefato sem conta Figma;
- for necessário comparar a versão apresentada com a versão atual.

**O que esta pasta não é**

| Não é | Por quê |
|---|---|
| Fonte de requisito | Comportamento vem do [Pilar 1](../../01-product-specs.md) |
| Fonte de design | Aparência vem do Figma; a exportação é cópia |
| Substituto do índice | O índice diz o que é cada tela; a exportação mostra como ela é |
| Local de trabalho | Não edite PNG/PDF à mão; corrija no Figma e exporte de novo |

---

## 2. Estado atual

| Campo | Valor |
|---|---|
| **Última exportação oficial** | `<preencher>` |
| **Responsável pela exportação** | `<preencher>` |
| **Versão do arquivo Figma** | `<preencher>` (nome ou histórico do Figma) |
| **Data prevista para a próxima exportação** | 31/10/2026 |
| **Telas exportadas** | 0 de 45 |
| **Formato** | PNG 1× para leitura + PDF consolidado para impressão |

> **Status:** a pasta está criada e documentada; os arquivos serão gerados na exportação oficial. Enquanto a coluna **Node ID** do [índice](../README.md) estiver `<preencher>`, a exportação por nó não pode ser automatizada.

**Por que ainda não exportado:** os `node-id` das 45 telas são uma decisão pendente (`<preencher>`). Exportar sem o ID estável produz arquivos com nomes frágeis e dificulta a atualização. A exportação manual pelo Figma (seleção de frame → Export) continua possível e deve seguir a nomenclatura da [§4](#4-nomenclatura-dos-arquivos).

---

## 3. Como exportar

### 3.1 Pré-requisitos

1. Acesso ao arquivo [Figma `SOSP`](https://www.figma.com/design/P8Pf9aZiagXQulJpP2guqz/SOSP?node-id=0-1) com permissão de visualização.
2. O [índice de telas](../README.md) aberto para conferir número, nome e node-id.
3. A pasta `docs/design/exports/` disponível no repositório local.

### 3.2 Exportação manual (recomendada para a apresentação)

1. No Figma, selecione o frame da tela.
2. No painel direito, em **Export**, escolha **PNG** e escala **1×**.
3. Clique em **Export <nome>** e salve em `docs/design/exports/mobile/` ou `docs/design/exports/web/`.
4. Renomeie o arquivo conforme a [§4](#4-nomenclatura-dos-arquivos).
5. Repita para as 45 telas.
6. Gere o PDF consolidado: selecione todos os frames de uma plataforma e exporte em **PDF**, ou una os PNGs em um PDF na ordem do índice.
7. Preencha a tabela da [§7](#7-como-atualizar) com data, responsável e versão.

### 3.3 Exportação por lote (quando os node-ids estiverem preenchidos)

Com os IDs no índice, a exportação pode ser feita por script usando a API do Figma ou uma ferramenta de automação. O script deve:

1. Ler a tabela do índice e extrair `#`, `Tela`, `Node ID` e plataforma.
2. Exportar cada nó em PNG 1×.
3. Nomear o arquivo com o padrão da [§4](#4-nomenclatura-dos-arquivos).
4. Falhar se algum `node-id` estiver vazio ou inválido.
5. Gerar um `manifest.json` com data, versão e hash de cada arquivo.

**Exemplo de manifesto:**

```json
{
  "exportedAt": "2026-10-31T18:00:00-03:00",
  "figmaFile": "P8Pf9aZiagXQulJpP2guqz",
  "figmaVersion": "<preencher>",
  "screens": [
    {
      "id": "04",
      "name": "Busca e resultados",
      "platform": "mobile",
      "nodeId": "<preencher>",
      "file": "mobile/04-busca-e-resultados.png",
      "sha256": "<preencher>"
    }
  ]
}
```

### 3.4 PDF consolidado

| Requisito | Regra |
|---|---|
| Ordem | A mesma do [índice](../README.md): mobile 01–30, depois web W01–W15 |
| Capa | Título, versão, data, link do Figma e aviso "acesso somente visualização" |
| Rodapé | `SOSP · <tela> · <data>` em todas as páginas |
| Formato | A4 paisagem para web, A4 retrato para mobile, ou página única por tela |
| Tamanho | ≤ 25 MB; se passar, comprimir as imagens sem perder legibilidade |
| Nome | `sosp-prototipo-<AAAA-MM-DD>.pdf` |

---

## 4. Nomenclatura dos arquivos

```text
<numero>-<nome-em-kebab-case>.png
```

**Regras**

1. O número é o do índice: `01`–`30` para mobile, `W01`–`W15` para web.
2. O nome é em minúsculas, sem acentos, com hífens no lugar de espaços.
3. Não inclua data no nome do arquivo; a data fica no manifesto e na tabela da [§7](#7-como-atualizar).
4. Não use `final`, `v2`, `novo` ou `corrigido` no nome. Versão é histórico, não nome.
5. Um arquivo por tela. Variantes de estado não são exportadas como tela separada, exceto a tela 19 (busca sem resultado).

**Exemplos**

| Tela | Arquivo |
|---|---|
| 01 · Login e boas-vindas | `mobile/01-login-e-boas-vindas.png` |
| 04 · Busca e resultados | `mobile/04-busca-e-resultados.png` |
| 10 · Agendamento confirmado e protocolo | `mobile/10-agendamento-confirmado-e-protocolo.png` |
| W12 · Catálogo de serviços | `web/W12-catalogo-de-servicos.png` |
| W15 · Relatórios | `web/W15-relatorios.png` |

---

## 5. Estrutura de pastas

```text
docs/design/exports/
├── README.md
├── manifest.json                 # gerado na exportação
├── sosp-prototipo-2026-10-31.pdf # consolidado (nome com data)
├── mobile/
│   ├── 01-login-e-boas-vindas.png
│   ├── 02-cadastro-do-cidadao.png
│   ├── ...
│   └── 30-onboarding-acessivel.png
└── web/
    ├── W01-home.png
    ├── W02-busca-e-resultados.png
    ├── ...
    └── W15-relatorios.png
```

**Regra:** não crie subpastas por versão (`v1/`, `v2/`). A versão vive no Git e no CHANGELOG; a pasta reflete o estado atual. Para comparar versões, use o histórico do repositório.

---

## 6. Checklist de exportação

Antes de considerar a exportação concluída:

- [ ] As 45 telas foram exportadas: 30 mobile + 15 web.
- [ ] Cada arquivo segue a nomenclatura da [§4](#4-nomenclatura-dos-arquivos).
- [ ] Nenhum arquivo está corrompido ou em branco.
- [ ] A ordem do PDF consolidado é a do índice.
- [ ] A capa do PDF tem versão, data e link do Figma.
- [ ] O rodapé de cada página identifica a tela e a data.
- [ ] O `manifest.json` foi gerado e confere com os arquivos.
- [ ] O tamanho total é ≤ 25 MB por PDF e ≤ 5 MB por PNG.
- [ ] Nenhum dado pessoal real aparece nas telas (usar massa fictícia).
- [ ] A tabela da [§7](#7-como-atualizar) foi preenchida.
- [ ] O [CHANGELOG](../../../CHANGELOG.md) registra a exportação, se ela acompanhou uma release.
- [ ] O link do Figma no [Pilar 0](../../README.md) e no [índice](../README.md) continua válido.

---

## 7. Como atualizar

### 7.1 Registro de exportações

| Data | Responsável | Versão do Figma | Telas | Formato | Observação |
|---|---|---|---|---|---|
| `<preencher>` | `<preencher>` | `<preencher>` | 0/45 | PNG + PDF | Pasta criada; exportação pendente |

**Regra:** toda exportação gera uma linha nesta tabela. A linha mais recente é a versão de referência da apresentação.

### 7.2 Passo a passo

1. Exporte as telas alteradas (não é necessário reexportar o que não mudou, mas o PDF consolidado deve ser regenerado).
2. Substitua os arquivos em `mobile/` ou `web/`.
3. Atualize o `manifest.json` com a nova data, versão e hash.
4. Atualize a tabela da [§7.1](#71-registro-de-exportações).
5. Rode a validação de links e de imagens quebradas.
6. Se a mudança afetar o índice (tela nova, removida ou renomeada), atualize o [índice](../README.md) na mesma PR.
7. Registre no [CHANGELOG](../../../CHANGELOG.md) quando a exportação acompanhar uma release.

---

## 8. Limitações e cuidados

| Limitação | Consequência | Mitigação |
|---|---|---|
| O Figma é somente visualização | Não é possível editar o arquivo original | Corrigir no arquivo de trabalho e solicitar a atualização do link oficial |
| `node-id` pendente | Exportação por script não é possível | Exportação manual pelo Figma até o índice ser preenchido |
| Fonte pode não estar disponível | Texto do PNG pode renderizar diferente | Exportar com as fontes carregadas; conferir visualmente |
| Imagens grandes | PDF acima de 25 MB | Comprimir PNGs e limitar a 1× |
| Conteúdo desatualizado | Documento mente sobre o estado atual | Data e versão no manifesto; revisão mensal |
| Dados pessoais | Vazamento em captura de tela | Usar somente massa fictícia; revisar antes de commitar |
| Link expira ou muda | Avaliador não abre o Figma | PDF/PNG desta pasta como cópia datada |

**Regra de privacidade:** nenhuma captura pode conter CPF, e-mail, telefone ou endereço de pessoa real. A massa de demonstração é fictícia e está documentada no [Pilar 5 §1.6](../../05-engineering-devops.md#16-massa-de-demonstração).

**Regra de acessibilidade:** o PDF consolidado precisa ter texto alternativo ou uma versão HTML acessível. Uma imagem de tela não é acessível por si só; o índice e o Pilar 2 são a referência textual.

---

*Esta pasta é cópia, não fonte. Alterou o Figma? Exporte de novo, atualize o manifesto e registre a data.*
