# Casos de Uso — UC-01 a UC-17

> **Projeto:** SOSP — Sistema de Orientação para Serviços Públicos
> **Versão:** 1.1.0 · **Data:** 31/10/2026 · **Status:** Em revisão
> **Autores:** Arthur Franco e Luiz Gustavo — CESMAC
> **Documentos irmãos:** [Pilar 1](../01-product-specs.md) · [Pilar 2](../02-design-ux.md) · [Pilar 3](../03-architecture.md) · [Pilar 4](../04-data-api.md) · [Pilar 5](../05-engineering-devops.md)

---

## Sumário

1. [Como ler este documento](#1-como-ler-este-documento)
2. [Atores](#2-atores)
3. [Diagrama de casos de uso](#3-diagrama-de-casos-de-uso)
4. [Convenções de fluxo](#4-convenções-de-fluxo)
5. [UC-01 a UC-05 — Conta e catálogo](#5-uc-01-a-uc-05--conta-e-catálogo)
6. [UC-06 a UC-08 — Orientação](#6-uc-06-a-uc-08--orientação)
7. [UC-09 a UC-12 — Agendamento e protocolo](#7-uc-09-a-uc-12--agendamento-e-protocolo)
8. [UC-13 a UC-17 — Qualidade, gestão e relatórios](#8-uc-13-a-uc-17--qualidade-gestão-e-relatórios)
9. [Matriz de rastreabilidade](#9-matriz-de-rastreabilidade)
10. [Casos de uso e feature flags](#10-casos-de-uso-e-feature-flags)

---

## 1. Como ler este documento

O caso de uso descreve **o objetivo de um ator**, não a tela. A tela é consequência: o mesmo UC pode ser executado em mobile, web ou back-office sem mudar o fluxo.

Cada caso de uso tem:

| Campo | O que informa |
|---|---|
| **Ator principal** | Quem inicia e recebe o resultado |
| **Atores secundários** | Quem participa sem iniciar (Gov.br, sistema, outro perfil) |
| **Requisito / histórias** | A origem do UC no [Pilar 1](../01-product-specs.md) |
| **Telas** | O número da tela no [índice do Figma](../design/README.md); `Back-office` quando não há tela pública |
| **Pré-condições** | O que precisa ser verdade antes do gatilho |
| **Gatilho** | O evento que inicia o fluxo |
| **Fluxo principal** | O caminho de sucesso, numerado |
| **Fluxos alternativos** | Variações legítimas que ainda terminam em sucesso |
| **Exceções** | Falhas que interrompem o fluxo e exigem tratamento |
| **Pós-condições** | O que é verdade quando o UC termina |
| **Regras e critérios** | As RN e os CA verificáveis |

**Regra de precedência:** se este documento divergir do [Pilar 1](../01-product-specs.md), vale o requisito. Se divergir do [OpenAPI](../api/openapi.yaml), vale o contrato. Este documento explica o **porquê** e a **ordem**; o contrato define a **forma**.

**Nomenclatura de atores:** "Servidor autorizado" é o servidor com a permissão `catalog.manage`. "Servidor" sem qualificador é o perfil operacional padrão. O Administrador acumula as permissões de ambos.

---

## 2. Atores

| Ator | Tipo | Descrição | Como se autentica |
|---|---|---|---|
| **Cidadão** | Primário | Pessoa física que busca orientação, agenda, acompanha protocolo e avalia | CPF e senha local |
| **Servidor** | Primário | Servidor público que opera protocolos e relatórios do seu órgão | CPF e senha local |
| **Servidor autorizado** | Primário (especialização) | Servidor com permissão explícita para publicar e versionar serviços | CPF e senha local + RBAC |
| **Administrador** | Primário | Mantém órgãos, unidades, usuários internos e parâmetros | CPF e senha local + RBAC |
| **Gov.br (v2.0)** | Secundário | Provedor de identidade do cidadão; entrega `sub`, CPF, nome e data de nascimento | OIDC |
| **Sistema** | Secundário | Workers, scheduler e regras automáticas (protocolo, PDF, notificação, expurgo) | Interno |

**Fora do escopo de atores:** a Ouvidoria é um canal externo citado na mensagem de busca vazia; o SOSP não gerencia seus protocolos. O órgão responsável recebe o protocolo, mas não opera o SOSP no MVP.

---

## 3. Diagrama de casos de uso

```mermaid
flowchart LR
    C([Cidadão])
    S([Servidor])
    SA([Servidor autorizado])
    A([Administrador])
    G([Gov.br (v2.0)])
    SIS([Sistema])

    subgraph Casos["Casos de uso do SOSP"]
        U01(UC-01<br/>Criar conta)
        U02(UC-02<br/>Autenticar (CPF+senha))
        U03(UC-03<br/>Gerenciar órgãos)
        U04(UC-04<br/>Gerenciar unidades)
        U05(UC-05<br/>Publicar e versionar serviço)
        U06(UC-06<br/>Buscar serviços)
        U07(UC-07<br/>Consultar ficha)
        U08(UC-08<br/>Seguir guia e gerar PDF)
        U09(UC-09<br/>Agendar atendimento)
        U10(UC-10<br/>Remarcar ou cancelar)
        U11(UC-11<br/>Acompanhar protocolo)
        U12(UC-12<br/>Anexar documento)
        U13(UC-13<br/>Avaliar atendimento)
        U14(UC-14<br/>Consultar FAQ e abrir dúvida)
        U15(UC-15<br/>Gerenciar usuários internos)
        U16(UC-16<br/>Notificar cidadão)
        U17(UC-17<br/>Gerar relatórios)
    end

    C --> U01
    C --> U02
    C --> U06
    C --> U07
    C --> U08
    C --> U09
    C --> U10
    C --> U11
    C --> U12
    C --> U13
    C --> U14

    S --> U02
    S --> U11
    S --> U17
    SA --> U05
    A --> U02
    A --> U03
    A --> U04
    A --> U05
    A --> U14
    A --> U15
    A --> U17

    SIS -.-> U09
    SIS -.-> U11
    SIS --> U16
    SIS -.-> U17
```

**Leitura do diagrama**

- Linha cheia: associação primária (o ator inicia ou recebe o resultado).
- Linha pontilhada: participação secundária (identidade, automação ou geração assíncrona).
- UC-13 e UC-16 estão fora do MVP e só existem com a flag ligada ([§10](#10-casos-de-uso-e-feature-flags)).

---

## 4. Convenções de fluxo

| Convenção | Aplicação |
|---|---|
| **A\\*** | Fluxo alternativo: caminho legítimo, termina em sucesso ou em sucesso parcial |
| **E\\*** | Exceção: falha técnica ou de negócio que impede a conclusão |
| **RN** | Regra de negócio do [Pilar 1 §4.3](../01-product-specs.md#43-regras-de-negócio) |
| **CA** | Critério de aceite do [Pilar 1 §3.5](../01-product-specs.md#catálogo-consolidado-de-critérios-de-aceite) |
| **Tela** | Número do [índice de telas](../design/README.md); a versão mobile é a referência de comportamento |
| **Contrato** | Operação do [OpenAPI](../api/openapi.yaml); nenhum UC inventa endpoint |

**Regra de autorização:** todo UC de back-office valida permissão no servidor, não apenas no menu. Um servidor sem `catalog.manage` recebe `403` mesmo que a rota exista. Um cidadão só acessa o próprio protocolo; protocolo de terceiro responde `404`, não `403` (não revela existência).

---

## 5. UC-01 a UC-05 — Conta e catálogo

### UC-01 · Criar conta manual do cidadão

| Atributo | Descrição |
|---|---|
| **Ator principal** | Cidadão (não autenticado) |
| **Pré-condições** | — |
| **Pós-condições** | Conta ativa com hash Argon2id + salt; e-mail de confirmação enviado |
| **Gatilho** | Cidadão escolhe "Criar conta" na tela de login |

**Fluxo principal**

1. Cidadão preenche CPF (validado por dígito verificador), nome completo, data de nascimento, e-mail, celular, gênero, PCD (e descrição se aplicável), nome da mãe e nome do pai (opcional).
2. Cidadão define senha (mín. 8 caracteres, 1 maiúscula, 1 número, 1 especial) e confirma.
3. Cidadão informa CEP; sistema consulta ViaCEP.
4. ViaCEP retorna logradouro, bairro, município e UF.
5. Cidadão informa número, complemento (opcional) e foto/avatar (opcional).
6. Sistema valida todos os campos: CPF único, e-mail único, idade ≥ 12, senha atende requisitos.
7. Sistema aplica hash Argon2id + salt na senha e persiste a conta.
8. Sistema envia e-mail de confirmação.
9. Sistema exibe "Cadastro realizado com sucesso" e redireciona ao login.

**Fluxos alternativos**

| ID | Situação | Comportamento |
|---|---|---|
| A1 | CEP não encontrado | Sistema libera digitação manual de logradouro, bairro, município e UF. Cidadão seleciona município e UF da lista do IBGE. |
| A2 | CPF já cadastrado | Sistema exibe "CPF já cadastrado" e oferece link para recuperação de senha. |
| A3 | E-mail já cadastrado | Sistema exibe "E-mail já cadastrado em outra conta." |
| A4 | Cancelamento | Sistema pergunta "Todas as alterações serão perdidas. Deseja realmente cancelar?" |
| A5 | Idade < 12 anos | Sistema exibe "É necessário ter 12 anos ou mais para se cadastrar." |
| A6 | Senha inválida | Sistema exibe as regras: mínimo 8 caracteres, 1 maiúscula, 1 número, 1 caractere especial. |

**Regras de negócio:** RN-26 (CPF único), RN-27 (CEP/endereço).
**Critérios de aceite:** CA-16.
**Contrato:** `POST /auth/register`, `GET /address/zip-code/{zipCode}`, `GET /locations/states`, `GET /locations/cities?state={uf}`

---

### UC-02 · Autenticar com CPF + senha e recuperar acesso

| Atributo | Descrição |
|---|---|
| **Ator principal** | Cidadão, Servidor, Administrador |
| **Pré-condições** | Conta ativa (criada via RF-01 ou RF-12) |
| **Pós-condições** | Sessão ativa com token seguro e expiração de 30 min de inatividade |
| **Gatilho** | Usuário acessa tela de login e informa CPF e senha |

**Fluxo principal — login**

1. Usuário informa CPF e senha.
2. Sistema consulta conta pelo CPF.
3. Sistema verifica bloqueio: se houver 5 tentativas falhas nos últimos 5 minutos, rejeita com mensagem de bloqueio.
4. Sistema recupera o hash Argon2id + salt e compara com a senha fornecida.
5. Sistema gera sessão com `SESSION_COOKIE_AGE=1800` (30 min) e `SESSION_IDLE_TIMEOUT_SECONDS=1800`.
6. Sistema registra o acesso em `auditEvent`.
7. Sistema redireciona à ação de origem (ou à home se não houver ação pendente).

**Fluxo principal — Gov.br (implementação futura)**

1. Usuário clica em "Entrar com Gov.br" na tela de login.
2. Sistema exibe modal informativo: "A integração com o Gov.br estará disponível em uma futura atualização (v2.0). Utilize seu CPF e senha para entrar."
3. Usuário clica em "Entendi, quero usar CPF e senha" e o modal é fechado.
4. Usuário permanece na tela de login com foco no formulário CPF + senha.

**Fluxo alternativo — recuperação de senha**

| ID | Situação | Comportamento |
|---|---|---|
| A1 | 5 tentativas erradas | Bloqueio de 5 minutos; exibe "CPF ou senha inválidos. Você tem X tentativa(s) restante(s)." |
| A2 | Sessão expirada | Redireciona ao login preservando o retorno via parâmetro `next` |
| A3 | Senha temporária (servidor) | Exige troca no primeiro acesso |
| A4 | Recuperação de senha | Usuário informa CPF e e-mail; sistema envia código de 6 dígitos válido por 15 min; usuário redefine a senha |
| A5 | Código expirado | Exibe "Código expirado. Solicite um novo." |
| A6 | E-mail não confere | Exibe "E-mail não encontrado para este CPF." sem revelar se o CPF existe |

**Regras de negócio:** RN-28 (sessão 30 min), RN-29 (bloqueio 5 tentativas), RN-30 (código 6 dígitos, 15 min).
**Critérios de aceite:** CA-16.
**Contrato:** `POST /auth/login`, `POST /auth/logout`, `POST /auth/recover-password`, `POST /auth/reset-password`

---

### UC-03 · Gerenciar órgãos

| Campo | Valor |
|---|---|
| **Ator principal** | Administrador |
| **Requisito** | RF-03 |
| **Histórias** | US-16 |
| **Telas** | Back-office |
| **Prioridade** | Essencial · Must |
| **Contrato** | `GET /agencies` + Django Admin |

**Pré-condições** — Sessão de administrador ativa com permissão de gestão de catálogo.

**Gatilho** — Necessidade de criar, editar, inativar ou consultar um órgão.

**Fluxo principal**

1. O administrador abre "Órgãos" no back-office.
2. O sistema lista os órgãos com nome, sigla, esfera, status e quantidade de unidades.
3. O administrador cria ou edita um órgão e informa nome, sigla, esfera, descrição e status.
4. O sistema valida a sigla única por esfera e grava a alteração.
5. O sistema registra `auditEvent` com antes e depois e exibe confirmação.

**Fluxos alternativos**

| ID | Condição | Comportamento |
|---|---|---|
| A1 | Inativação com unidades ativas | Exibe o impacto e exige confirmação; as unidades permanecem, mas não recebem novos agendamentos |
| A2 | Reativação | Restaura o órgão e suas unidades ao catálogo, sem republicar serviços automaticamente |
| A3 | Consulta filtrada | Permite filtrar por esfera, status e termo |

**Exceções**

| ID | Falha | Comportamento |
|---|---|---|
| E1 | Sigla duplicada na mesma esfera | Bloqueia com "Já existe um órgão com esta sigla nesta esfera." (RN-31) |
| E2 | Exclusão física solicitada | Bloqueia; a operação é sempre lógica (RN-40) |
| E3 | Sessão expirada | Preserva o formulário e redireciona ao login |

**Pós-condições** — Órgão criado, atualizado ou inativado, com auditoria e reflexo imediato no catálogo.

**Regras aplicáveis:** RN-31, RN-39, RN-40 · **Critérios:** CA-17.

---

### UC-04 · Gerenciar unidades de atendimento

| Campo | Valor |
|---|---|
| **Ator principal** | Administrador |
| **Requisito** | RF-04 |
| **Histórias** | US-16 |
| **Telas** | Back-office |
| **Prioridade** | Essencial · Must |
| **Contrato** | `GET /units` + Django Admin |

**Pré-condições** — Órgão ativo cadastrado (UC-03) e sessão de administrador.

**Gatilho** — Necessidade de cadastrar um local, corrigir endereço, horário ou capacidade.

**Fluxo principal**

1. O administrador abre "Unidades" e seleciona o órgão.
2. O sistema lista as unidades com nome, município, horário e status.
3. O administrador informa nome, endereço (CEP com ViaCEP), telefone, e-mail, horário por dia, limite diário, acessibilidade, atendimento preferencial e coordenadas.
4. O sistema valida unicidade por órgão + município e consistência de horário e coordenadas.
5. O sistema grava, registra auditoria e exibe confirmação.

**Fluxos alternativos**

| ID | Condição | Comportamento |
|---|---|---|
| A1 | CEP não encontrado | Libera endereço manual com Município/UF do IBGE |
| A2 | Dia sem atendimento | Horário vazio representa fechado e não gera slots |
| A3 | Sem latitude/longitude | A unidade é válida; o bloco de mapa não aparece na ficha (RN-10) |

**Exceções**

| ID | Falha | Comportamento |
|---|---|---|
| E1 | Nome duplicado no mesmo órgão e município | Bloqueia com "Já existe uma unidade com este nome neste município." (RN-32) |
| E2 | Limite diário ≤ 0 | Bloqueia com "Informe um limite maior que zero." |
| E3 | Coordenada fora do intervalo | Bloqueia com "Coordenada inválida." |
| E4 | Inativação com agendamentos futuros | Exige confirmação e mantém os agendamentos existentes; bloqueia novos |

**Pós-condições** — Unidade disponível (ou indisponível) para agendamento, com horários e capacidade refletidos no cálculo de slots.

**Regras aplicáveis:** RN-19, RN-32, RN-39, RN-40 · **Critérios:** CA-17.

---

### UC-05 · Publicar e versionar serviço

| Campo | Valor |
|---|---|
| **Ator principal** | Administrador, Servidor autorizado |
| **Requisito** | RF-05 |
| **Histórias** | US-17 |
| **Telas** | Back-office |
| **Prioridade** | Essencial · Must |
| **Contrato** | `GET /services/{serviceId}`, `GET /services/{serviceId}/steps`, `GET /services/{serviceId}/documents` + Django Admin |

**Pré-condições**

1. Órgão e ao menos uma unidade ativa cadastrados.
2. Usuário com permissão `catalog.manage` (RN-35).

**Gatilho** — Necessidade de publicar um serviço novo ou corrigir um serviço existente.

**Fluxo principal**

1. O usuário cria um serviço em rascunho e informa nome, categoria, descrição, público elegível, órgãos, pré-requisitos, custo, prazo, canal e link externo.
2. O usuário cadastra ao menos um documento obrigatório e ao menos uma etapa ordenada.
3. O sistema valida os oito blocos da ficha e a consistência do canal com o link externo.
4. O usuário solicita a publicação.
5. O sistema cria uma nova versão imutável, publica o serviço e o torna visível na busca.
6. O sistema registra `auditEvent` e exibe o número da versão publicada.

**Fluxos alternativos**

| ID | Condição | Comportamento |
|---|---|---|
| A1 | Serviço já publicado | A edição gera nova versão; a anterior permanece consultável no histórico |
| A2 | Publicação programada | Permite data futura; o serviço só entra na busca na data |
| A3 | Despublicação | Move para Inativo, remove da busca e mantém protocolos e links diretos com aviso de indisponibilidade |
| A4 | Duplicação | Cria um rascunho a partir de um serviço existente, sem herdar o histórico |

**Exceções**

| ID | Falha | Comportamento |
|---|---|---|
| E1 | Falta de documento obrigatório | Bloqueia com "Inclua ao menos um documento obrigatório." (RN-33) |
| E2 | Falta de etapa | Bloqueia com "Inclua ao menos uma etapa." |
| E3 | Canal online/híbrido sem link `https://` | Bloqueia com "Informe um link https:// válido." |
| E4 | Usuário sem `catalog.manage` | Responde `403` e registra a tentativa |
| E5 | Falha ao gravar a versão | Mantém o rascunho intacto e não altera a versão publicada |

**Pós-condições**

- Serviço publicado, com versão imutável e oito blocos completos.
- Histórico de versões disponível para auditoria.
- Busca e ficha refletem a nova versão após invalidação de cache.

**Regras aplicáveis:** RN-07, RN-33, RN-34, RN-35, RN-39, RN-40 · **Critérios:** CA-17.

---

## 6. UC-06 a UC-08 — Orientação

### UC-06 · Buscar serviços

| Campo | Valor |
|---|---|
| **Ator principal** | Cidadão |
| **Requisito** | RF-06 |
| **Histórias** | US-01, US-02, US-03 |
| **Telas** | 04 |
| **Prioridade** | Essencial · Must |
| **Contrato** | `GET /services`, `GET /categories` |

**Pré-condições** — Ao menos um serviço ativo e publicado. Não exige autenticação.

**Gatilho** — O cidadão digita um termo na busca ou seleciona uma categoria na home.

**Fluxo principal**

1. O cidadão informa o termo em linguagem simples e, opcionalmente, filtros de categoria, órgão, canal e município.
2. O sistema normaliza acentos e caixa, consulta o índice full-text e aplica os filtros por interseção.
3. O sistema ordena por relevância, retorna 10 itens por página e informa o total.
4. O sistema exibe cards com nome, órgão, canal, custo, prazo e total de resultados.
5. O cidadão refina os filtros ou abre um serviço (UC-07).
6. O sistema registra termo, filtros, contagem e data, sem dados pessoais.

**Fluxos alternativos**

| ID | Condição | Comportamento |
|---|---|---|
| A1 | Termo vazio | Lista todos os serviços ativos por popularidade |
| A2 | Filtros combinados | Persistem na URL; recarregar ou compartilhar preserva o estado |
| A3 | Paginação | Web exibe 10 cards com contador; mobile carrega em blocos de 10 |
| A4 | Busca por categoria na home | Executa a mesma consulta com o filtro de categoria pré-aplicado |

**Exceções**

| ID | Falha | Comportamento |
|---|---|---|
| E1 | Nenhum resultado | Exibe "Nenhum serviço encontrado. Tente outro termo ou categoria.", sugestões de categoria, caminho para a Ouvidoria e "Limpar filtros" quando houver filtros (RN-13) |
| E2 | Filtro inválido | Retorna `400` com o campo e o valor recusado |
| E3 | Serviço inativo aberto por link direto | Retorna `404` com orientação de voltar à busca (RN-06) |
| E4 | Índice de busca indisponível | Degrada para busca por `ILIKE`/`pg_trgm` e registra alerta; não exibe erro ao cidadão |

**Pós-condições** — Lista de serviços exibida e consulta registrada para o RF-14, sem identificador pessoal.

**Regras aplicáveis:** RN-01 a RN-05, RN-12, RN-13 · **Critérios:** CA-01 a CA-05, CA-10.

---

### UC-07 · Consultar ficha orientativa

| Campo | Valor |
|---|---|
| **Ator principal** | Cidadão |
| **Requisito** | RF-06 |
| **Histórias** | US-04 |
| **Telas** | 05 |
| **Prioridade** | Essencial · Must |
| **Contrato** | `GET /services/{serviceId}` |

**Pré-condições** — Serviço ativo, publicado e com os oito blocos completos.

**Gatilho** — O cidadão seleciona um card na busca, um atalho da home ou um link direto.

**Fluxo principal**

1. O sistema carrega o serviço e as unidades vinculadas.
2. O sistema monta os oito blocos: o que é, quem tem direito, o que levar, como fazer, onde fazer, quando, quanto custa e quanto demora.
3. O sistema exibe as ações disponíveis: Ver passo a passo, Agendar e, se o RF-10 estiver habilitado e houver protocolo concluído, Avaliar.
4. O sistema sinaliza documentos obrigatórios e opcionais e o atendimento preferencial quando aplicável.
5. O sistema exibe o mapa somente se a unidade tiver latitude e longitude.
6. O cidadão escolhe uma ação e o sistema preserva o serviço como origem.

**Fluxos alternativos**

| ID | Condição | Comportamento |
|---|---|---|
| A1 | Serviço sem unidade presencial | Exibe apenas o canal online e o link externo |
| A2 | Múltiplas unidades | Lista todas, com endereço, horário e acessibilidade; o mapa mostra a selecionada |
| A3 | Cidadão não autenticado escolhe Agendar | Redireciona ao Gov.br e retorna à ficha com a intenção preservada (D6) |
| A4 | Serviço com avaliações habilitadas | Exibe média e contagem somente com a flag do RF-10 ligada (RN-11) |

**Exceções**

| ID | Falha | Comportamento |
|---|---|---|
| E1 | Serviço inativo ou inexistente | `404` com "Este serviço não está mais disponível." e link para a busca |
| E2 | Bloco obrigatório ausente | Não publica; em produção, registra incidente e oculta a ficha em vez de exibir conteúdo incompleto |
| E3 | Unidade removida após a publicação | Exibe o serviço sem o bloco "Onde fazer" e sinaliza "Consulte a unidade pelo canal oficial" |

**Pós-condições** — Cidadão informado e com caminho para o guia ou o agendamento; a origem é registrada para o retorno pós-login.

**Regras aplicáveis:** RN-06 a RN-11 · **Critérios:** CA-06 a CA-09.

---

### UC-08 · Seguir guia e gerar PDF

| Campo | Valor |
|---|---|
| **Ator principal** | Cidadão |
| **Requisito** | RF-07 |
| **Histórias** | US-05, US-06, US-07 |
| **Telas** | 06, 07 |
| **Prioridade** | Essencial · Must |
| **Contrato** | `GET /services/{serviceId}/guidance`, `PUT /services/{serviceId}/guidance/checklist`, `POST /services/{serviceId}/guidance/pdf`, `GET /guidance/pdf/{jobId}` |

**Pré-condições** — Serviço ativo com etapas e documentos cadastrados.

**Gatilho** — O cidadão escolhe "Ver passo a passo" na ficha.

**Fluxo principal**

1. O sistema lista as etapas numeradas, com título, descrição e tempo estimado.
2. O sistema lista os documentos com caixa de marcação e diferencia obrigatórios de opcionais.
3. O cidadão marca os documentos já separados.
4. O sistema salva o progresso por CPF e serviço; se o cidadão não estiver autenticado, o progresso fica apenas na sessão.
5. O cidadão solicita o PDF.
6. O sistema enfileira a geração, responde `202` com `jobId` e o portal acompanha o status.
7. O sistema disponibiliza o PDF com nome, serviço, checklist e data/hora.
8. Se o cidadão for PCD ou 60+ e a unidade tiver atendimento preferencial, o sistema exibe o alerta antes da geração.

**Fluxos alternativos**

| ID | Condição | Comportamento |
|---|---|---|
| A1 | Cidadão autenticado retoma o guia | Progresso restaurado do servidor |
| A2 | Cidadão não autenticado gera PDF | PDF permitido; o checklist não é persistido entre sessões |
| A3 | Alerta de prioridade | Exibido apenas quando RN-17 é verdadeira, com texto informativo e sem exigir comprovação no SOSP |
| A4 | Download repetido | O PDF é regenerado ou servido do cache pelo `jobId` dentro da validade |

**Exceções**

| ID | Falha | Comportamento |
|---|---|---|
| E1 | PDF não fica pronto em 5 s | O job continua; o portal mostra "Ainda estamos preparando seu PDF" e permite tentar novamente |
| E2 | Falha definitiva na geração | Job vai para a DLQ, o cidadão recebe "Não foi possível gerar o PDF agora" e o checklist permanece disponível |
| E3 | Serviço despublicado durante a geração | O job é cancelado e o cidadão é orientado a voltar à busca |
| E4 | Progresso de outro CPF | O servidor ignora o `citizenId` do corpo e usa o da sessão; nunca confia no cliente |

**Pós-condições** — Checklist salvo (quando autenticado) e PDF disponível para download; `auditEvent` registra a geração.

**Regras aplicáveis:** RN-14 a RN-17 · **Critérios:** CA-11, CA-15.

---

## 7. UC-09 a UC-12 — Agendamento e protocolo

### UC-09 · Agendar atendimento

| Campo | Valor |
|---|---|
| **Ator principal** | Cidadão |
| **Atores secundários** | Sistema (cálculo de slots e protocolo) |
| **Requisito** | RF-08 |
| **Histórias** | US-08, US-09 |
| **Telas** | 08, 09, 10 |
| **Prioridade** | Importante · Should |
| **Contrato** | `GET /units/{unitId}/slots`, `POST /appointments` |

**Pré-condições**

1. Cidadão autenticado com perfil completo (UC-01).
2. Serviço ativo com canal presencial ou híbrido.
3. Unidade ativa, com horário no dia e vagas disponíveis.

**Gatilho** — O cidadão escolhe "Agendar" na ficha ou em "Meus pedidos".

**Fluxo principal**

1. O cidadão seleciona serviço, unidade e data.
2. O sistema calcula slots de 30 minutos dentro do horário de funcionamento, descontando feriados, dias sem atendimento, bloqueios e lotação.
3. O sistema exibe apenas slots livres, com data, hora e unidade.
4. O cidadão escolhe o slot e confirma.
5. O sistema envia `POST /appointments` com `Idempotency-Key`, valida a disponibilidade em transação e grava o agendamento.
6. O sistema gera o protocolo `AAAAMMDD-XXXX` com sequência diária e o comprovante em PDF.
7. O sistema envia e-mail de confirmação e exibe o protocolo com link para o acompanhamento.

**Fluxos alternativos**

| ID | Condição | Comportamento |
|---|---|---|
| A1 | Cidadão quer remarcar antes de confirmar | Volta ao passo 1 sem criar agendamento |
| A2 | Serviço híbrido | Permite escolher presencial ou online; online redireciona ao link externo e não gera protocolo presencial |
| A3 | Reenvio da mesma requisição | `Idempotency-Key` devolve o mesmo agendamento, sem duplicar |
| A4 | Cidadão sem perfil completo | Redireciona ao UC-01 e retoma o agendamento após concluir |

**Exceções**

| ID | Falha | Comportamento |
|---|---|---|
| E1 | Slot lotado entre a exibição e a confirmação | Retorna `409`, recarrega os slots e informa "Este horário acabou de ser preenchido. Escolha outro." |
| E2 | Agendamento duplicado para o mesmo serviço | Bloqueia com "Você já tem um agendamento ativo para este serviço." (RN-21) |
| E3 | Data passada | Bloqueia com "Não é possível agendar em data passada." |
| E4 | Unidade fechada no dia | Não oferece slots; se a data for forçada, retorna `422` |
| E5 | Falha ao gerar o PDF do comprovante | O agendamento é preservado; o comprovante é regenerado de forma assíncrona |
| E6 | Falha no envio do e-mail | O agendamento é preservado; o envio vai para retry e depois para a DLQ |

**Pós-condições**

- Agendamento ativo, protocolo emitido e comprovante disponível.
- E-mail de confirmação enfileirado.
- Slot marcado como ocupado na mesma transação.

**Regras aplicáveis:** RN-18 a RN-22 · **Critérios:** CA-12, CA-13.

---

### UC-10 · Remarcar ou cancelar agendamento

| Campo | Valor |
|---|---|
| **Ator principal** | Cidadão |
| **Requisito** | RF-08 |
| **Histórias** | US-10 |
| **Telas** | 10 |
| **Prioridade** | Importante · Should |
| **Contrato** | `GET /appointments/{appointmentId}`, `PATCH /appointments/{appointmentId}` |

**Pré-condições**

1. Agendamento ativo do próprio cidadão.
2. Ação solicitada até 24 horas antes do horário marcado.

**Gatilho** — O cidadão abre o agendamento em "Meus pedidos" e escolhe remarcar ou cancelar.

**Fluxo principal**

1. O sistema exibe os dados do agendamento e as ações permitidas conforme o prazo.
2. O cidadão escolhe "Remarcar" ou "Cancelar".
3. Em remarcar, o sistema mostra novos slots e o cidadão escolhe um; em cancelar, o sistema pede confirmação.
4. O sistema valida o prazo e a disponibilidade em transação, atualiza o agendamento e libera o slot anterior.
5. O sistema registra `auditEvent`, envia e-mail e exibe a confirmação.

**Fluxos alternativos**

| ID | Condição | Comportamento |
|---|---|---|
| A1 | Remarcação para o mesmo slot | Bloqueia com "Escolha um horário diferente do atual." |
| A2 | Cancelamento com motivo | Permite informar motivo opcional; o motivo entra na linha do tempo |
| A3 | Agendamento já concluído | Ações desabilitadas com explicação |

**Exceções**

| ID | Falha | Comportamento |
|---|---|---|
| E1 | Prazo de 24 h vencido | Bloqueia e orienta contatar a unidade (RN-22) |
| E2 | Novo slot lotado | Retorna `409` e recarrega as opções |
| E3 | Agendamento de terceiro | Responde `404`; não revela a existência |
| E4 | Falha no e-mail | A alteração é preservada; o envio entra em retry |

**Pós-condições** — Agendamento remarcado ou cancelado, slot anterior liberado e linha do tempo atualizada.

**Regras aplicáveis:** RN-21, RN-22, RN-23 · **Critérios:** CA-12.

---

### UC-11 · Acompanhar protocolo

| Campo | Valor |
|---|---|
| **Ator principal** | Cidadão, Servidor |
| **Atores secundários** | Sistema (transições automáticas) |
| **Requisito** | RF-09 |
| **Histórias** | US-11 |
| **Telas** | 10 |
| **Prioridade** | Importante · Should |
| **Contrato** | `GET /protocols`, `GET /protocols/{protocolNumber}`, `PATCH /protocols/{protocolNumber}` (servidor) |

**Pré-condições**

1. Protocolo existente e vinculado ao cidadão autenticado, ou ao órgão do servidor.
2. Sessão válida.

**Gatilho** — O cidadão abre "Meus pedidos" ou o servidor abre a fila do órgão.

**Fluxo principal — cidadão**

1. O cidadão acessa "Meus pedidos" e vê a lista de protocolos com status e data.
2. O cidadão seleciona um protocolo.
3. O sistema exibe a linha do tempo com data, hora, responsável e observação, além do comprovante e dos anexos.
4. O sistema mostra a próxima ação esperada (aguardar, anexar documento, comparecer, avaliar).

**Fluxo principal — servidor**

1. O servidor abre a fila do seu órgão e filtra por status, serviço e período.
2. O servidor seleciona o protocolo e altera o status conforme a máquina de estados.
3. O sistema exige observação nas transições que a política define, grava a linha do tempo e notifica o cidadão por e-mail.

**Fluxos alternativos**

| ID | Condição | Comportamento |
|---|---|---|
| A1 | Protocolo aguardando documento | Exibe o botão "Anexar documento" (UC-12) e o prazo |
| A2 | Protocolo concluído | Exibe o botão "Avaliar" somente com o RF-10 habilitado |
| A3 | Servidor de outro órgão | Não vê o protocolo na fila; acesso direto responde `404` |

**Exceções**

| ID | Falha | Comportamento |
|---|---|---|
| E1 | Protocolo de terceiro | `404` para o cidadão; `403` para servidor de outro órgão, com auditoria |
| E2 | Transição inválida | Bloqueia com "Transição não permitida a partir do estado atual." (RN-24) |
| E3 | Protocolo cancelado | Linha do tempo permanece visível; ações desabilitadas |
| E4 | Falha ao notificar | A transição é preservada; o e-mail entra em retry e depois na DLQ |

**Pós-condições** — Cidadão informado; servidor com a fila atualizada; toda transição auditada.

**Regras aplicáveis:** RN-23, RN-24, RN-39 · **Critérios:** CA-14.

---

### UC-12 · Anexar documento ao protocolo

| Campo | Valor |
|---|---|
| **Ator principal** | Cidadão |
| **Requisito** | RF-09 |
| **Histórias** | US-12 |
| **Telas** | 10 |
| **Prioridade** | Importante · Should |
| **Contrato** | `POST /protocols/{protocolNumber}/documents` |

**Pré-condições**

1. Protocolo do próprio cidadão no estado "Aguardando documento".
2. Sessão válida e solicitação de documento registrada pelo servidor.

**Gatilho** — O cidadão abre o protocolo e escolhe "Anexar documento".

**Fluxo principal**

1. O sistema informa qual documento foi solicitado, o formato aceito e o limite de 10 MB.
2. O cidadão seleciona o arquivo.
3. O sistema valida extensão real, tamanho e assinatura do arquivo, e envia ao antivírus.
4. O sistema grava o anexo em bucket privado, com URL assinada de curta duração.
5. O sistema move o protocolo para "Em análise (retorno)", registra a linha do tempo e notifica o servidor.
6. O sistema exibe "Documento enviado. Seu pedido voltou para análise."

**Fluxos alternativos**

| ID | Condição | Comportamento |
|---|---|---|
| A1 | Múltiplos arquivos permitidos | Aceita até o limite definido na solicitação, com lista e remoção antes de confirmar |
| A2 | Reenvio do mesmo documento | Substitui a versão anterior, mantendo o histórico no `auditEvent` |
| A3 | Cidadão cancela antes de enviar | Nenhum arquivo é gravado |

**Exceções**

| ID | Falha | Comportamento |
|---|---|---|
| E1 | Formato não aceito | Bloqueia com "Envie um arquivo jpg, png ou pdf." (RN-25) |
| E2 | Arquivo acima de 10 MB | Bloqueia com "O arquivo deve ter no máximo 10 MB." |
| E3 | Antivírus detecta ameaça | Rejeita, apaga o objeto e registra incidente de segurança |
| E4 | Protocolo em estado incompatível | Bloqueia com "Este pedido não está aguardando documento." |
| E5 | Falha no storage | Mantém o protocolo no estado anterior e orienta tentar novamente |

**Pós-condições** — Anexo privado vinculado ao protocolo, estado atualizado e servidor notificado.

**Regras aplicáveis:** RN-23, RN-25, RS-04 · **Critérios:** CA-14.

---

## 8. UC-13 a UC-17 — Qualidade, gestão e relatórios

### UC-13 · Avaliar atendimento (v2.0)

| Campo | Valor |
|---|---|
| **Ator principal** | Cidadão |
| **Requisito** | RF-10 |
| **Histórias** | US-20 |
| **Telas** | 05 (v2.0) |
| **Prioridade** | Desejável · Could |
| **Contrato** | `POST /protocols/{protocolNumber}/review` |

> **Fora do MVP.** O endpoint existe no contrato marcado com `x-feature-flag: FEATURE_REVIEWS_ENABLED`. Sem a flag, a rota responde `404` e o botão não é renderizado.

**Pré-condições**

1. `FEATURE_REVIEWS_ENABLED=true`.
2. Protocolo do próprio cidadão no estado "Concluído".
3. Nenhuma avaliação anterior para o mesmo protocolo.

**Gatilho** — O cidadão escolhe "Avaliar" na ficha ou no protocolo concluído.

**Fluxo principal**

1. O sistema exibe o formulário com nota de 1 a 5 e comentário opcional de até 500 caracteres.
2. O cidadão informa a nota e, se quiser, o comentário.
3. O sistema valida a elegibilidade e a unicidade, grava a avaliação e atualiza a média do serviço.
4. O sistema exibe "Avaliação enviada. Obrigado por contribuir."

**Fluxos alternativos**

| ID | Condição | Comportamento |
|---|---|---|
| A1 | Comentário vazio | Permite; a nota é suficiente |
| A2 | Cidadão quer editar | Permite edição por 24 horas, com auditoria |
| A3 | Média exibida na ficha | Só aparece com a flag ligada (RN-11) |

**Exceções**

| ID | Falha | Comportamento |
|---|---|---|
| E1 | Protocolo não concluído | Bloqueia com "Você só pode avaliar um atendimento concluído." |
| E2 | Avaliação duplicada | Bloqueia com "Este atendimento já foi avaliado." (RN-37) |
| E3 | Flag desligada | `404` e botão ausente; nenhum dado é coletado |

**Pós-condições** — Avaliação registrada, média recalculada e relatório de avaliações disponível para o gestor.

**Regras aplicáveis:** RN-11, RN-37 · **Critérios:** CA-19.

---

### UC-14 · Consultar FAQ e abrir dúvida

| Campo | Valor |
|---|---|
| **Ator principal** | Cidadão |
| **Atores secundários** | Administrador (mantém o FAQ) |
| **Requisito** | RF-11 |
| **Histórias** | US-21 |
| **Telas** | 13 |
| **Prioridade** | Importante · Should |
| **Contrato** | `GET /services/{serviceId}/faq`, `POST /questions` |

**Pré-condições** — Serviço ativo com FAQ cadastrado ou categoria com perguntas vinculadas.

**Gatilho** — O cidadão escolhe "Dúvidas frequentes" na ficha, na home ou no rodapé.

**Fluxo principal**

1. O sistema lista as perguntas frequentes do serviço ou da categoria.
2. O cidadão digita uma dúvida ou seleciona uma pergunta.
3. O sistema busca no FAQ e devolve no máximo 3 resultados por busca.
4. O cidadão lê a resposta.
5. Se não resolver, o cidadão escolhe "Ainda tenho dúvida" e o sistema abre o formulário de pergunta.
6. O sistema registra a pergunta, gera um protocolo de dúvida e informa o prazo de resposta.

**Fluxos alternativos**

| ID | Condição | Comportamento |
|---|---|---|
| A1 | Pergunta sem resposta no FAQ | Exibe "Não encontramos uma resposta. Envie sua dúvida." |
| A2 | Cidadão não autenticado | Permite consultar o FAQ; para abrir dúvida, exige login e retorna ao formulário |
| A3 | Dúvida já respondida | Mostra a resposta e a data, sem abrir novo protocolo |

**Exceções**

| ID | Falha | Comportamento |
|---|---|---|
| E1 | Busca sem resultado | Exibe a saída para a Ouvidoria e o formulário de dúvida |
| E2 | Falha ao registrar a pergunta | Mantém o texto no formulário e orienta tentar novamente |
| E3 | Serviço inativo | FAQ permanece acessível por link direto com aviso; novas dúvidas são bloqueadas |

**Pós-condições** — Dúvida registrada e vinculada ao cidadão, com protocolo e prazo; FAQ atualizado pelo administrador quando a pergunta se repete.

**Regras aplicáveis:** RN-38, RN-39 · **Critérios:** CA-20.

---

### UC-15 · Gerenciar usuários internos

| Campo | Valor |
|---|---|
| **Ator principal** | Administrador |
| **Requisito** | RF-12 |
| **Histórias** | US-18 |
| **Telas** | Back-office |
| **Prioridade** | Essencial · Must |
| **Contrato** | Django Admin (sem rota pública) |

**Pré-condições** — Sessão de administrador com permissão de gestão de usuários.

**Gatilho** — Necessidade de criar, editar, inativar ou redefinir a senha de um usuário interno.

**Fluxo principal**

1. O administrador abre "Usuários internos" e escolhe "Novo".
2. O administrador informa nome, CPF, e-mail, matrícula, órgão, nível (Administrador/Servidor) e a permissão "Gerenciar catálogo de serviços".
3. O sistema valida CPF, e-mail e matrícula únicos e grava o usuário com senha temporária.
4. O sistema envia o convite por e-mail e exige a troca de senha no primeiro acesso.
5. O sistema registra `auditEvent` e exibe o usuário criado.

**Fluxos alternativos**

| ID | Condição | Comportamento |
|---|---|---|
| A1 | Servidor autorizado | Administrador liga a permissão `catalog.manage`; o usuário passa a publicar serviços do seu órgão |
| A2 | Inativação | Bloqueia o login imediatamente, mantém o histórico de auditoria e não apaga registros |
| A3 | Redefinição de senha | Gera senha temporária e exige troca no próximo acesso |

**Exceções**

| ID | Falha | Comportamento |
|---|---|---|
| E1 | CPF, e-mail ou matrícula duplicados | Bloqueia com a mensagem do campo específico |
| E2 | Órgão inativo | Bloqueia com "Selecione um órgão ativo." |
| E3 | Administrador tenta remover o próprio acesso | Bloqueia com "Não é possível remover o próprio acesso de administrador." |
| E4 | Último administrador ativo | Bloqueia a inativação para não deixar o sistema sem administrador |

**Pós-condições** — Usuário criado ou atualizado, com permissões efetivas e auditoria.

**Regras aplicáveis:** RN-35, RN-39, RN-40 · **Critérios:** CA-17.

---

### UC-16 · Notificar cidadão (v2.0)

| Campo | Valor |
|---|---|
| **Ator principal** | Sistema |
| **Requisito** | RF-13 |
| **Histórias** | — |
| **Telas** | — |
| **Prioridade** | Desejável · Could |
| **Contrato** | `GET /notifications/preferences`, `PUT /notifications/preferences`, `POST /webhooks/email` |

> **Fora do MVP.** No MVP, apenas o e-mail transacional de confirmação e lembrete é enviado pelos próprios fluxos de UC-01, UC-09, UC-10 e UC-11. Push, SMS e WhatsApp ficam para a v2.0, com `FEATURE_PUSH_ENABLED=false`.

**Pré-condições**

1. Cidadão com conta ativa e preferência de canal registrada.
2. Evento de notificação disparado por mudança de status, lembrete ou resposta de dúvida.

**Gatilho** — Evento de domínio enfileirado (`appointment.created`, `protocol.status_changed`, `question.answered`).

**Fluxo principal**

1. O worker consome o evento e verifica a preferência do cidadão por tipo e canal.
2. O worker renderiza o template, envia pelo canal habilitado e registra o resultado.
3. O sistema grava o log com status (`sent`, `failed`, `bounced`) e o identificador da mensagem.
4. Em falha transitória, o worker reagenda com backoff exponencial.
5. Em falha definitiva, o evento vai para a DLQ e dispara alerta.

**Fluxos alternativos**

| ID | Condição | Comportamento |
|---|---|---|
| A1 | Cidadão fez opt-out do tipo | Não envia; registra `skipped` |
| A2 | Canal push desabilitado | Usa e-mail se o tipo permitir; caso contrário, registra `skipped` |
| A3 | Lembrete de 24 h | Agendado pelo scheduler e cancelado se o agendamento for remarcado ou cancelado |

**Exceções**

| ID | Falha | Comportamento |
|---|---|---|
| E1 | Provedor de e-mail indisponível | Retry com backoff; após 5 tentativas, DLQ e alerta |
| E2 | Token de push inválido | Remove a inscrição, registra o motivo e não repete |
| E3 | Preferência ausente | Aplica o padrão: e-mail para transacionais, sem marketing |

**Pós-condições** — Notificação registrada com status; preferências respeitadas; nenhum envio duplicado para o mesmo evento.

**Regras aplicáveis:** RN-39, RS-02 · **Critérios:** CA-21.

---

### UC-17 · Gerar relatórios gerenciais

| Campo | Valor |
|---|---|
| **Ator principal** | Administrador, Servidor |
| **Atores secundários** | Sistema (geração assíncrona de exportações) |
| **Requisito** | RF-14 |
| **Histórias** | US-19 |
| **Telas** | Back-office |
| **Prioridade** | Importante · Should |
| **Contrato** | `GET /reports/appointments`, `POST /reports/exports` |

**Pré-condições**

1. Sessão interna ativa.
2. Dados de busca, agendamento e protocolo disponíveis no período.

**Gatilho** — O gestor abre "Relatórios" ou solicita uma exportação.

**Fluxo principal**

1. O gestor escolhe o relatório e aplica filtros de período, órgão, serviço e unidade.
2. O sistema valida o escopo do órgão do servidor (RN-36) e consulta os dados agregados.
3. O sistema exibe a tela paginada com gráfico de barras e tabela.
4. O gestor solicita exportação CSV ou PDF.
5. O sistema enfileira a geração, responde `202` com `jobId` e disponibiliza o arquivo por URL assinada.
6. O sistema registra `auditEvent` com filtros, escopo e formato.

**Fluxos alternativos**

| ID | Condição | Comportamento |
|---|---|---|
| A1 | Período sem dados | Exibe estado vazio com "Nenhum dado no período selecionado" e mantém os filtros |
| A2 | Relatório de avaliações | Painel oculto por `FEATURE_REVIEWS_ENABLED` até o RF-10 entrar no escopo (D13) |
| A3 | Exportação grande | Processada em background; o gestor acompanha o status pelo `jobId` |

**Exceções**

| ID | Falha | Comportamento |
|---|---|---|
| E1 | Servidor tenta acessar outro órgão | `403` e auditoria; o filtro de órgão é limitado ao escopo do usuário |
| E2 | Período inválido | `400` com "A data inicial deve ser anterior à final." |
| E3 | Falha na exportação | Job vai para a DLQ; o gestor é avisado e pode tentar novamente |
| E4 | Arquivo expirado | A URL assinada expira; o gestor solicita nova exportação |

**Pós-condições** — Relatório exibido e/ou exportado, com escopo respeitado e auditoria registrada.

**Regras aplicáveis:** RN-36, RN-39 · **Critérios:** CA-18.

---

## 9. Matriz de rastreabilidade

| UC | RF | Histórias | Telas | Endpoints principais | RN | CA |
|---|---|---|---|---|---|---|
| UC-01 | RF-01 | US-13 | 01, 02 | `POST /auth/register`, `/address/zip-code/*`, `/locations/*` | RN-26, RN-27 | CA-16 |
| UC-02 | RF-02 | US-14, US-15 | 01, 02 | `POST /auth/login`, `/auth/logout`, `/auth/recover-password`, `/auth/reset-password` | RN-28, RN-29, RN-30 | CA-16 |
| UC-03 | RF-03 | US-16 | Back-office | `GET /agencies` + Admin | RN-31, RN-39, RN-40 | CA-17 |
| UC-04 | RF-04 | US-16 | Back-office | `GET /units` + Admin | RN-19, RN-32, RN-39, RN-40 | CA-17 |
| UC-05 | RF-05 | US-17 | Back-office | `/services/{serviceId}`, `/steps`, `/documents` + Admin | RN-07, RN-33, RN-34, RN-35, RN-39, RN-40 | CA-17 |
| UC-06 | RF-06 | US-01 a US-03 | 04 | `GET /services`, `GET /categories` | RN-01 a RN-05, RN-12, RN-13 | CA-01 a CA-05, CA-10 |
| UC-07 | RF-06 | US-04 | 05 | `GET /services/{serviceId}` | RN-06 a RN-11 | CA-06 a CA-09 |
| UC-08 | RF-07 | US-05 a US-07 | 06, 07 | `/guidance`, `/guidance/checklist`, `/guidance/pdf`, `/guidance/pdf/{jobId}` | RN-14 a RN-17 | CA-11, CA-15 |
| UC-09 | RF-08 | US-08, US-09 | 08, 09, 10 | `GET /units/{unitId}/slots`, `POST /appointments` | RN-18 a RN-22 | CA-12, CA-13 |
| UC-10 | RF-08 | US-10 | 10 | `GET/PATCH /appointments/{appointmentId}` | RN-21 a RN-23 | CA-12 |
| UC-11 | RF-09 | US-11 | 10 | `GET /protocols`, `GET/PATCH /protocols/{protocolNumber}` | RN-23, RN-24, RN-39 | CA-14 |
| UC-12 | RF-09 | US-12 | 10 | `POST /protocols/{protocolNumber}/documents` | RN-23, RN-25, RS-04 | CA-14 |
| UC-13 | RF-10 | US-20 | 05 (v2.0) | `POST /protocols/{protocolNumber}/review` | RN-11, RN-37 | CA-19 |
| UC-14 | RF-11 | US-21 | 13 | `GET /services/{serviceId}/faq`, `POST /questions` | RN-38, RN-39 | CA-20 |
| UC-15 | RF-12 | US-18 | Back-office | Django Admin | RN-35, RN-39, RN-40 | CA-17 |
| UC-16 | RF-13 | — | — | `/notifications/preferences`, `/webhooks/email` | RN-39, RS-02 | CA-21 |
| UC-17 | RF-14 | US-19 | Back-office | `/reports/appointments`, `/reports/exports` | RN-36, RN-39 | CA-18 |

**Cobertura:** 17 UCs cobrem 14 RFs. RF-10 e RF-13 estão fora do MVP; RF-14 entrega os relatórios do MVP e mantém o painel de avaliações oculto por flag. Nenhum RF do MVP ficou sem UC.

---

## 10. Casos de uso e feature flags

| UC | Flag | Padrão | Efeito quando desligada |
|---|---|---|---|
| UC-13 | `FEATURE_REVIEWS_ENABLED` | `false` | `POST /protocols/{protocolNumber}/review` responde `404`; botão "Avaliar" não renderiza; média não aparece na ficha; painel de avaliações do RF-14 fica oculto |
| UC-16 | `FEATURE_PUSH_ENABLED` | `false` | Push não é enviado; e-mail transacional continua funcionando; preferências de push ficam somente leitura |
| UC-17 | `FEATURE_REPORTS_EXPORT` | `true` | Exportação CSV/PDF desabilitada; a tela paginada continua disponível |

**Regra:** a flag é avaliada no servidor. O portal pode esconder o botão, mas a rota também precisa recusar a operação. Uma flag não é controle de acesso: permissão continua sendo RBAC.

**Como ligar em desenvolvimento:**

```bash
FEATURE_REVIEWS_ENABLED=true
FEATURE_PUSH_ENABLED=false
FEATURE_REPORTS_EXPORT=true
```

**Como validar:** o [Pilar 5 §10](../05-engineering-devops.md#10-feature-flags-e-ambientes) descreve o ciclo de vida da flag; o [Pilar 4 §6](../04-data-api.md#6-contrato-de-api) registra `x-feature-flag` no contrato; o [Pilar 1 §7](../01-product-specs.md#7-matriz-de-divergências) registra D11 e D13.

---

*Este documento é derivado do [Pilar 1](../01-product-specs.md). Alterou o requisito? Atualize o UC, o contrato e o CHANGELOG na mesma PR.*
