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

O Figma é a fonte oficial de aparência. Esta pasta guarda **cópias datadas** das 30 telas (45 frames no total: 15 telas do cidadão em versões mobile e web, 5 telas do servidor, 6 telas administrativas e 4 telas transversais), para que a documentação continue legível quando:

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
| **Última exportação oficial** | `01/11/2026` |
| **Responsável pela exportação** | Luiz Gustavo |
| **Versão do arquivo Figma** | `v1.0` (`2416288953332883055`) |
| **Telas exportadas** | **30 de 30 telas** (45 frames + 1 capa) |
| **Formato** | PNG 1× organizado por perfil + PDF consolidado ([`sosp-prototipo-2026-11-01.pdf`](sosp-prototipo-2026-11-01.pdf)) |

> **Status:** exportação oficial **concluída**. Todos os PNGs, o [`manifest.json`](manifest.json) com hashes `sha256` e o PDF consolidado ([`sosp-prototipo-2026-11-01.pdf`](sosp-prototipo-2026-11-01.pdf)) estão gerados e versionados nesta pasta.

**Exportação por nó:** com os `node-id` das 30 telas (45 frames) preenchidos no [índice](../README.md), a exportação foi consolidada por perfil (`Cidadão/Mobile`, `Cidadão/Web`, `Servidor`, `Administrador` e `Transversais`), acompanhada do arquivo de capa [`capa-sosp.png`](capa-sosp.png).

---

## 3. Como exportar

### 3.1 Pré-requisitos

1. Acesso ao arquivo [Figma `SOSP`](https://www.figma.com/design/P8Pf9aZiagXQulJpP2guqz/SOSP?node-id=0-1) com permissão de visualização.
2. O [índice de telas](../README.md) aberto para conferir número, nome e node-id.
3. A pasta `docs/design/exports/` disponível no repositório local.

### 3.2 Exportação manual (recomendada para a apresentação)

1. No Figma, selecione o frame da tela.
2. No painel direito, em **Export**, escolha **PNG** e escala **1×**.
3. Clique em **Export <nome>** e salve na respectiva pasta por perfil (`Cidadão/Mobile/`, `Cidadão/Web/`, `Servidor/`, `Administrador/` ou `Transversais/`).
4. Mantenha o nome do frame conforme a [§4](#4-nomenclatura-dos-arquivos).
5. Repita para as 30 telas (45 frames).
6. Gere o PDF consolidado: una os PNGs em um PDF na ordem do índice.
7. Preencha a tabela da [§7](#7-como-atualizar) com data, responsável e versão.

### 3.3 Exportação por lote (quando os node-ids estiverem preenchidos)

Com os IDs no índice, a exportação pode ser feita por script usando a API do Figma ou uma ferramenta de automação. O script deve:

1. Ler a tabela do índice e extrair `#`, `Tela`, `Node ID` e plataforma/perfil.
2. Exportar cada nó em PNG 1×.
3. Salvar o arquivo no padrão da [§4](#4-nomenclatura-dos-arquivos).
4. Falhar se algum `node-id` estiver vazio ou inválido.
5. Gerar um `manifest.json` com data, versão e hash de cada arquivo.

**Exemplo de manifesto:**

```json
{
  "exportedAt": "2026-11-01T21:38:00-03:00",
  "figmaFile": "P8Pf9aZiagXQulJpP2guqz",
  "figmaVersion": "v1.0 (2416288953332883055)",
  "screens": [
    {
      "id": "04",
      "name": "04 · Busca",
      "platform": "cidadão-mobile",
      "nodeId": "8:459",
      "file": "Cidadão/Mobile/04 · Busca.png",
      "sha256": "..."
    }
  ]
}
```

### 3.4 PDF consolidado

| Requisito | Regra |
|---|---|
| Ordem | A mesma do [índice](../README.md): Cidadão Mobile (`01`–`15`), Cidadão Web (`W01`–`W15`), Servidor (`16`–`20`), Administrador (`21`–`26`) e Transversais (`27`–`30`) |
| Capa | Título, versão, data, link do Figma e aviso "acesso somente visualização" |
| Rodapé | `SOSP · <tela> · <data>` em todas as páginas |
| Formato | Página dimensionada para cada frame com rodapé informativo |
| Tamanho | ≤ 25 MB; se passar, comprimir as imagens sem perder legibilidade |
| Nome | `sosp-prototipo-<AAAA-MM-DD>.pdf` |

---

## 4. Nomenclatura dos arquivos

Os arquivos exportados preservam a organização por perfil e o título oficial do frame no Figma:

- **Cidadão Mobile (`Cidadão/Mobile/`):** `<numero> · <Nome da Tela>.png` (ex.: `01 · Login Gov.br.png`)
- **Cidadão Web (`Cidadão/Web/`):** `<numero> · <Nome da Tela> · Web.png` (ex.: `01 · Login Gov.br · Web.png`)
- **Servidor (`Servidor/`) e Administrador (`Administrador/`):** `Tela · <Nome da Tela>.png` (ex.: `Tela · Dashboard do Servidor.png`, `Tela · Órgãos.png`)
- **Transversais (`Transversais/`):** `<numero> · <Nome da Tela>.png` (ex.: `27 · Erro Gov.br.png`)
- **Capa na raiz de `exports/`:** `capa-sosp.png`

**Regras**

1. O número e o título seguem exatamente os frames do [índice](../README.md).
2. Não inclua data no nome dos PNGs; a data fica no [`manifest.json`](manifest.json) e na tabela da [§7](#7-como-atualizar).
3. Não use sufixos informais como `final`, `v2`, `novo` ou `corrigido` no nome. Versão é histórico no Git.
4. Um arquivo por frame (45 frames para as 30 telas lógicas + 1 capa).

**Exemplos reais na pasta**

| Tela | Arquivo |
|---|---|
| 01 · Login Gov.br (Mobile) | `Cidadão/Mobile/01 · Login Gov.br.png` |
| W04 · Busca de serviços (Web) | `Cidadão/Web/04 · Busca de serviços · Web.png` |
| 16 · Dashboard do Servidor | `Servidor/Tela · Dashboard do Servidor.png` |
| 21 · Órgãos | `Administrador/Tela · Órgãos.png` |
| 27 · Erro Gov.br | `Transversais/27 · Erro Gov.br.png` |

---

## 5. Estrutura de pastas

```text
docs/design/exports/
├── README.md
├── capa-sosp.png                 # Capa oficial do SOSP no Figma (Node ID 5:445)
├── manifest.json                 # Manifesto com nodeId e hash SHA-256 de todas as telas
├── sosp-prototipo-2026-11-01.pdf # PDF consolidado (Capa + 45 frames com rodapé)
├── Cidadão/
│   ├── Mobile/                   # 15 telas mobile do cidadão (01 a 15 — 390px)
│   │   ├── 01 · Login Gov.br.png
│   │   ├── ...
│   │   └── 15 · Perfil.png
│   └── Web/                      # 15 telas web do cidadão (01 · Web a 15 · Web — 1440px)
│       ├── 01 · Login Gov.br · Web.png
│       ├── ...
│       └── 15 · Acompanhamento · Web.png
├── Servidor/                     # 5 telas do servidor (16 a 20 — 1440px)
│   ├── Tela · Dashboard do Servidor.png
│   ├── ...
│   └── Tela · Relatórios Gerenciais.png
├── Administrador/                # 6 telas administrativas (21 a 26 — 1440px)
│   ├── Tela · Órgãos.png
│   ├── ...
│   └── Tela · Relatórios e Auditoria.png
└── Transversais/                 # 4 telas transversais (27 a 30 — 1440px)
    ├── 27 · Erro Gov.br.png
    ├── ...
    └── 30 · Visualização de PDFs.png
```

**Regra:** não crie subpastas por versão (`v1/`, `v2/`). A versão vive no Git e no CHANGELOG; a pasta reflete o estado atual. Para comparar versões, use o histórico do repositório.

---

## 6. Checklist de exportação

Antes de considerar a exportação concluída:

- [x] As 30 telas foram exportadas (45 frames: 15 mobile do cidadão + 15 web do cidadão + 5 servidor + 6 administrativas + 4 transversais).
- [x] Cada arquivo está organizado em sua respectiva pasta por perfil (`Cidadão/Mobile`, `Cidadão/Web`, `Servidor`, `Administrador`, `Transversais`).
- [x] Nenhum arquivo está corrompido ou em branco.
- [x] A ordem do PDF consolidado ([`sosp-prototipo-2026-11-01.pdf`](sosp-prototipo-2026-11-01.pdf)) é a do índice.
- [x] A capa do PDF tem versão, data e link do Figma.
- [x] O rodapé de cada página identifica a tela, o `Node ID` e a data.
- [x] O [`manifest.json`](manifest.json) foi gerado e confere com os arquivos.
- [x] O tamanho total é ≤ 25 MB por PDF (`4,0 MB`) e ≤ 5 MB por PNG.
- [x] Nenhum dado pessoal real aparece nas telas (usar massa fictícia).
- [x] A tabela da [§7](#7-como-atualizar) foi preenchida.
- [x] O link do Figma no [Pilar 0](../../README.md) e no [índice](../README.md) continua válido.

---

## 7. Como atualizar

### 7.1 Registro de exportações

| Data | Responsável | Versão do Figma | Telas | Formato | Observação |
|---|---|---|---|---|---|
| 01/11/2026 | Luiz Gustavo | `v1.0` (`2416288953332883055`) | 30/30 (45 frames) | PNG + PDF | Exportação completa concluída (`manifest.json` + `sosp-prototipo-2026-11-01.pdf`) |

**Regra:** toda exportação gera uma linha nesta tabela. A linha mais recente é a versão de referência da apresentação.

### 7.2 Passo a passo

1. Exporte as telas alteradas (não é necessário reexportar o que não mudou, mas o PDF consolidado deve ser regenerado).
2. Substitua os arquivos na pasta correspondente (`Cidadão/Mobile/`, `Cidadão/Web/`, `Servidor/`, `Administrador/` ou `Transversais/`).
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
| Mudança de `node-id` | Se um frame for recriado no Figma, o ID antigo deixa de existir | Atualizar a tabela do [índice](../README.md) na mesma entrega |
| Fonte pode não estar disponível | Texto do PNG pode renderizar diferente | Exportar com as fontes carregadas; conferir visualmente |
| Imagens grandes | PDF acima de 25 MB | Comprimir PNGs e limitar a 1× |
| Conteúdo desatualizado | Documento mente sobre o estado atual | Data e versão no manifesto; revisão mensal |
| Dados pessoais | Vazamento em captura de tela | Usar somente massa fictícia; revisar antes de commitar |
| Link expira ou muda | Avaliador não abre o Figma | PDF/PNG desta pasta como cópia datada |

**Regra de privacidade:** nenhuma captura pode conter CPF, e-mail, telefone ou endereço de pessoa real. A massa de demonstração é fictícia e está documentada no [Pilar 5 §1.6](../../05-engineering-devops.md#16-massa-de-demonstração).

**Regra de acessibilidade:** o PDF consolidado precisa ter texto alternativo ou uma versão HTML acessível. Uma imagem de tela não é acessível por si só; o índice e o Pilar 2 são a referência textual.

---

*Esta pasta é cópia, não fonte. Alterou o Figma? Exporte de novo, atualize o manifesto e registre a data.*
