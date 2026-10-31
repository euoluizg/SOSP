# Pilar 1 — Visão de Produto e Requisitos

> **Projeto:** SOSP — Sistema de Orientação para Serviços Públicos
> **Versão:** 1.1.0 · **Data:** 31/10/2026 · **Status:** Em revisão
> **Autores:** Equipe de Engenharia de Software — CESMAC
> **Documentos irmãos:** [Pilar 2](02-design-ux.md) · [Pilar 3](03-architecture.md) · [Pilar 4](04-data-api.md) · [Pilar 5](05-engineering-devops.md)
> **Documentos complementares:** [Casos de uso](use-cases/README.md) · [Índice de telas](design/README.md) · [Gestão do projeto](06-project-management.md) · [Roteiro da demo](demo-7-minutos.md) · [Glossário](glossario.md)
> **Protótipo oficial:** [Figma `SOSP`](https://www.figma.com/design/P8Pf9aZiagXQulJpP2guqz/SOSP?node-id=0-1) · **Acesso somente visualização**

---

## Sumário

1. [Executive Summary e Escopo](#1-executive-summary-e-escopo)
2. [Personas](#2-personas)
3. [User Stories e Critérios de Aceite](#3-user-stories-e-critérios-de-aceite)
4. [Requisitos Funcionais](#4-requisitos-funcionais)
5. [Requisitos Não-Funcionais](#5-requisitos-não-funcionais)
6. [Segurança e Privacidade](#6-segurança-e-privacidade)
7. [Matriz de Divergências](#7-matriz-de-divergências)
8. [Rastreabilidade](#8-rastreabilidade)
9. [Definição de Pronto](#9-definição-de-pronto)
10. [Artefatos complementares](#10-artefatos-complementares)

---

## 1. Executive Summary e Escopo

### 1.1 O problema

O cidadão conhece a sua necessidade, mas não o nome oficial do serviço público, nem o órgão responsável, nem os documentos exigidos. A informação está dispersa entre portais de secretarias, unidades de atendimento e o balcão presencial, e o vocabulário é técnico. O resultado é previsível:

| Consequência | Efeito medido no atendimento | Custo para o cidadão |
|---|---|---|
| Deslocamento sem os documentos corretos | Retorno à unidade no mesmo dia ou em outro dia | Passagens, dia de trabalho perdido, fila repetida |
| Desconhecimento do canal correto | Fila presencial para um serviço que é 100% online | Ocupação indevida da capacidade da unidade |
| Vocabulário técnico incompatível | Busca por "tirar documento" não encontra "Emitir Carteira de Identidade" | Abandono e procura de terceiros |
| Falta de rastreio do pedido | Cidadão liga para a unidade para saber o andamento | Sobrecarga do atendimento telefônico |

### 1.2 A proposta de valor

O SOSP é um ponto de entrada único que traduz a necessidade do cidadão em um serviço concreto, entrega uma **ficha orientativa** com oito respostas — o que é, quem tem direito, o que levar, como fazer, onde, quando, quanto custa e quanto demora — e conduz ao agendamento e ao acompanhamento por protocolo.

A proposta se sustenta em quatro decisões de produto:

1. **Orientação antes de formulário.** O cidadão não precisa saber o nome do serviço nem criar conta para se orientar. Cadastro é exigido apenas quando há efeito transacional: agendar, anexar documento, avaliar.
2. **Uma ficha, oito perguntas.** A ficha é organizada pelas perguntas que o cidadão faz no balcão, não pela estrutura do banco de dados.
3. **Catálogo como fonte única.** Nenhuma informação é digitada duas vezes: a ficha é montada a partir do catálogo (RF-05) e das unidades (RF-04). Se o dado não existe no catálogo, a ficha não inventa.
4. **Rastro do começo ao fim.** Todo agendamento vira protocolo, todo protocolo tem linha do tempo e toda mudança de status é auditável.

### 1.3 Público e contexto de uso

| Dimensão | Realidade considerada no projeto |
|---|---|
| Perfil etário | População adulta, com parcela relevante de idosos (60+) e público PCD |
| Dispositivo | Uso majoritário em celular (390 px), com desktop relevante em lan houses, bibliotecas e órgãos públicos |
| Conectividade | Rede móvel instável em periferias; a interface precisa tolerar latência e perda de conexão |
| Letramento digital | Variável; vocabulário técnico é barreira real, não detalhe estético |
| Confiança | O cidadão precisa reconhecer a origem institucional (Gov.br, órgão responsável, canal oficial) |
| Acessibilidade | WCAG 2.1 AA e eMAG são requisito, não melhoria incremental |

### 1.4 KPIs de sucesso

Cada KPI tem fórmula, meta, linha de base e instrumento. Sem instrumento, o KPI não entra no painel.

| ID | KPI | Fórmula | Linha de base | Meta (12 meses) | Instrumento |
|---|---|---|---|---|---|
| K1 | Conclusão da descoberta | sessões com ficha aberta ÷ sessões com busca realizada | a medir | ≥ 70% | Analytics de eventos (`search_submitted`, `service_opened`) |
| K2 | Tempo até a ficha | p95 do tempo entre `search_submitted` e `service_opened` | a medir | ≤ 2,5 s (p99 ≤ 3 s) | RUM + Prometheus |
| K3 | Busca sem resultado | buscas com `resultCount = 0` ÷ total de buscas | a medir | ≤ 12% | `searchQueryLog` (RF-14) |
| K4 | Comparecimento | agendamentos com status `completed` ÷ agendamentos confirmados | a medir | ≥ 80% | `schedulingAppointment` + `schedulingProtocol` |
| K5 | Satisfação | média das notas de 1 a 5 | a medir | ≥ 4,2 | `feedbackReview` (RF-10, v2.0) |
| K6 | Conclusão do guia | guias com checklist 100% ÷ guias iniciados | a medir | ≥ 60% | `guidanceProgress` |
| K7 | Autoatendimento | sessões sem abertura de dúvida ÷ sessões totais | a medir | ≥ 60% | `schedulingProtocol` tipo `question` |
| K8 | Cobertura do catálogo | serviços ativos com os 8 blocos completos ÷ serviços ativos | a medir | 100% | Checklist de publicação (RF-05) |

**Regra de leitura:** K2 é um KPI de experiência, não de infraestrutura. Ele é medido no navegador do cidadão (RUM), não no tempo de resposta do servidor. Um p95 de 200 ms no servidor pode produzir 4 s no celular.

### 1.5 MVP × Roadmap v2.0

O MVP entrega o ciclo completo de orientação e agendamento. O que fica para a v2.0 não é o que "não deu tempo", é o que depende de volume ou de maturidade operacional.

| Capacidade | Requisito | MVP | v2.0 | Justificativa |
|---|---|---|---|---|
| Cadastro manual do cidadão | RF-01 | ✅ | — | CPF, dados pessoais, endereço e senha |
| Autenticação local (CPF + senha) | RF-02 | ✅ | — | Login com CPF e senha para cidadãos e servidores |
| Gov.br (OIDC) | RF-02 | — | ✅ | Integração com governo federal; depende de credenciamento institucional |
| Órgãos e unidades | RF-03, RF-04 | ✅ | — | Base do catálogo e do "onde fazer" |
| Catálogo de serviços | RF-05 | ✅ | — | Sem catálogo não há busca nem ficha |
| Busca e ficha orientativa | RF-06 | ✅ | — | Núcleo da proposta de valor |
| Guia passo a passo + checklist + PDF | RF-07 | ✅ | — | Núcleo da orientação |
| Agendamento | RF-08 | ✅ | — | Efeito transacional do sistema |
| Acompanhamento de protocolo | RF-09 | ✅ | — | Reduz ligações e ansiedade |
| FAQ e dúvida | RF-11 | ✅ | — | Desvio de baixo custo para dúvidas |
| Usuários internos | RF-12 | ✅ | — | Operação do back-office |
| Relatórios gerenciais | RF-14 | ✅ | — | Gestão do catálogo e da demanda |
| Avaliação e comentário | RF-10 | — | ✅ | Depende de volume de protocolos concluídos |
| Central de preferências de notificação | RF-13 | — | ✅ | MVP envia e-mail transacional dentro do RF-08/RF-09 |
| Push no navegador | RF-13 | — | ✅ | Exige service worker, opt-in e chave VAPID; entra atrás de `FEATURE_PUSH_ENABLED` |
| SMS e WhatsApp | RF-13 | — | ✅ | Custo por mensagem e contrato com provedor |
| Aplicativo nativo | — | — | ✅ | Web responsivo cobre o MVP; app exige pipeline próprio |
| Busca semântica / embeddings | RF-06 | — | ✅ | Full-text + `pg_trgm` resolve o MVP com custo previsível |
| Integrações federais adicionais | — | — | ✅ | Dependem de acordos institucionais |

**Decisão explícita:** RF-10 e RF-13 são **Desejável/Could** e ficam fora do MVP. A ficha do RF-06 não renderiza o botão "Avaliar" enquanto a funcionalidade estiver desligada por feature flag. Essa decisão está registrada em [D5](#7-matriz-de-divergências) e [D7](#7-matriz-de-divergências). O mecanismo de flags está no [ADR-007](adr/ADR-007-feature-flags.md): o comportamento é avaliado no servidor e declarado no contrato com `x-feature-flag`.

---

## 2. Personas

As personas não são biografias: são recortes de comportamento que mudam requisito. Cada uma declara o que precisa fazer, o que a impede e qual decisão de design ela força.

### 2.1 Persona primária — Cidadão em busca de orientação

| Atributo | Descrição |
|---|---|
| **Nome de referência** | Maria, 38 anos, auxiliar administrativa |
| **Contexto** | Precisa emitir a segunda via de um documento e não sabe qual órgão procura |
| **Dispositivo** | Celular Android intermediário, 4G instável, 390 px |
| **Objetivo** | Descobrir o que levar e onde ir sem sair de casa |
| **Frustração** | Sites com vocabulário técnico, formulários antes da informação, PDFs desatualizados |
| **O que a faz desistir** | Exigir login antes de mostrar a resposta; ficha sem custo, prazo ou endereço |
| **Força de design** | Ficha pública, filtros combináveis, custo e prazo visíveis no card |

### 2.2 Persona primária — Cidadão autenticado

| Atributo | Descrição |
|---|---|
| **Nome de referência** | João, 29 anos, motoboy |
| **Contexto** | Já usou o sistema uma vez e quer remarcar um atendimento |
| **Dispositivo** | Celular, uso em movimento, uma mão |
| **Objetivo** | Resolver tudo em poucos toques, sem digitar dados que o sistema já tem |
| **Frustração** | Repetir CPF e endereço a cada solicitação; não saber se o pedido avançou |
| **Força de design** | "Meus pedidos" como hub, protocolo copiável, CTA fixo ao alcance do polegar |

### 2.3 Persona de acessibilidade — Cidadão PCD ou idoso

| Atributo | Descrição |
|---|---|
| **Nome de referência** | Dona Lúcia, 67 anos, aposentada, baixa visão |
| **Contexto** | Precisa de atendimento presencial e tem direito a prioridade legal |
| **Dispositivo** | Tablet emprestado, fonte ampliada, leitor de tela ativado |
| **Objetivo** | Ser atendida sem enfrentar fila comum e sem depender de terceiros |
| **Frustração** | Texto pequeno, contraste baixo, botão que só muda de cor, formulário que não diz qual campo está errado |
| **Força de design** | Alerta de prioridade na ficha e no guia, contraste AA, foco visível, rótulo associado ao campo, alvo de 44 px |

### 2.4 Persona operacional — Servidor de atendimento

| Atributo | Descrição |
|---|---|
| **Nome de referência** | Carlos, 45 anos, atendente de unidade do DETRAN |
| **Contexto** | Recebe o cidadão, confere documentos e gerencia a agenda do dia |
| **Objetivo** | Confirmar, remarcar ou cancelar atendimentos com motivo registrado |
| **Frustração** | Planilha paralela, cidadão com protocolo errado, retrabalho de digitação |
| **Força de design** | Busca por CPF/protocolo/status, transição de status com observação obrigatória |

### 2.5 Persona operacional — Servidor autorizado

| Atributo | Descrição |
|---|---|
| **Nome de referência** | Renata, 34 anos, técnica da secretaria de saúde |
| **Contexto** | Mantém o catálogo dos serviços da sua secretaria |
| **Objetivo** | Publicar e versionar serviços sem depender do administrador do sistema |
| **Frustração** | Não poder corrigir um prazo errado na própria área |
| **Força de design** | Permissão granular "Gerenciar catálogo de serviços" (RF-12) |

### 2.6 Persona operacional — Administrador

| Atributo | Descrição |
|---|---|
| **Nome de referência** | Paulo, 51 anos, gestor de TI da prefeitura |
| **Contexto** | Responde por usuários, órgãos, unidades e relatórios |
| **Objetivo** | Garantir que o catálogo esteja completo e que o acesso seja auditável |
| **Frustração** | Descobrir serviço sem documento publicado só quando o cidadão reclama |
| **Força de design** | Relatório de lacunas, checklist de publicação, trilha de auditoria |

---

## 3. User Stories e Critérios de Aceite

Formato: *Como [papel], quero [capacidade], para que [benefício]*. Cada história tem critérios em Gherkin, incluindo caminho felizes, erro e estado vazio. As histórias estão agrupadas por épico e rastreadas ao RF.

### Épico A — Descoberta

#### US-01 · Buscar serviço por palavra-chave

**Como** cidadão, **quero** descrever o que preciso com minhas palavras, **para que** o sistema encontre o serviço sem eu saber o nome oficial.

```gherkin
Cenário: Busca com resultado
  Dado que estou na tela de busca
  Quando digito "tirar rg" e envio a busca
  Então vejo a lista de serviços ordenada por relevância
  E cada card exibe nome, órgão, canal, custo e prazo
  E vejo o total de resultados e a paginação com 10 itens por página

Cenário: Busca normaliza acentos e caixa
  Quando digito "certidao de nascimento"
  Então o sistema retorna os mesmos resultados de "Certidão de Nascimento"

Cenário: Busca com termo vazio
  Dado que o campo está vazio
  Quando envio a busca
  Então vejo todos os serviços ativos ordenados por popularidade
```

*Rastreia:* RF-06 · UC-06 · RN-01, RN-02, RN-05 · CA-01, CA-02, CA-03 · Tela 04.

#### US-02 · Refinar a busca com filtros

**Como** cidadão, **quero** combinar filtros de categoria, órgão, canal e município, **para que** eu veja apenas o que é possível para mim.

```gherkin
Cenário: Filtros combinados
  Dado que estou na lista de resultados
  Quando seleciono Categoria "Documentos", Órgão "DETRAN" e Canal "Presencial"
  Então a lista é recalculada mantendo o termo buscado
  E os filtros ativos aparecem como chips removíveis
  E a URL reflete o estado para permitir compartilhamento

Cenário: Filtro sem resultado
  Quando combino filtros que não têm interseção
  Então vejo o estado vazio com a mensagem literal do requisito
  E vejo o botão "Limpar filtros"
```

*Rastreia:* RF-06 · UC-06 · RN-03, RN-04, RN-13 · CA-04, CA-05, CA-10 · Tela 04.

#### US-03 · Entender por que não houve resultado

**Como** cidadão, **quero** receber uma explicação e uma saída quando a busca não encontra nada, **para que** eu não conclua que o serviço não existe.

```gherkin
Cenário: Busca sem resultado
  Quando busco por "passaporte intergaláctico"
  Então vejo o título "Nenhum serviço encontrado. Tente outro termo ou categoria."
  E vejo sugestões de categorias
  E vejo o caminho para falar com a Ouvidoria

Cenário: Registro da lacuna
  Quando a busca não retorna resultados
  Então o termo é registrado em searchQueryLog sem dados pessoais
```

*Rastreia:* RF-06 · UC-06 · RN-12, RN-13 · CA-05 · Tela 04.

#### US-04 · Consultar a ficha orientativa

**Como** cidadão, **quero** ver todas as orientações de um serviço em uma única página, **para que** eu saiba se tenho direito, o que levar e quanto custa antes de me deslocar.

```gherkin
Cenário: Ficha completa
  Dado que selecionei um serviço ativo
  Então vejo os oito blocos: o que é, quem tem direito, documentos, resumo das etapas, onde fazer, horário, prazo e custo
  E vejo a data da última atualização
  E vejo as ações "Ver passo a passo" e "Agendar"

Cenário: Bloco obrigatório ausente
  Dado que o serviço não tem documentos cadastrados
  Quando a ficha é solicitada
  Então o serviço não é publicado e o back-office sinaliza a lacuna
```

*Rastreia:* RF-06 · UC-07 · RN-06 a RN-11 · CA-06 a CA-09 · Tela 05.

### Épico B — Orientação

#### US-05 · Seguir o passo a passo com checklist

**Como** cidadão, **quero** marcar cada documento que já separei, **para que** eu não esqueça nada e possa retomar depois.

```gherkin
Cenário: Progresso persistido
  Dado que estou autenticado e abri o guia de um serviço
  Quando marco o documento "RG" e recarrego a página
  Então o item continua marcado

Cenário: Conclusão do guia
  Quando todos os documentos obrigatórios estão marcados
  Então vejo a confirmação de que estou pronto para o atendimento
  E o evento de conclusão é registrado
```

*Rastreia:* RF-07 · UC-08 · RN-14, RN-15 · CA-11 · Telas 06, 07.

#### US-06 · Gerar o PDF de orientação

**Como** cidadão, **quero** baixar um PDF com o guia e o checklist, **para que** eu leve a orientação impressa ao atendimento.

```gherkin
Cenário: Geração assíncrona
  Quando clico em "Baixar PDF"
  Então vejo o estado de processamento
  E em até 5 segundos recebo o arquivo com nome, serviço, documentos marcados e data/hora

Cenário: Falha na geração
  Quando o worker falha
  Então vejo "Não foi possível gerar o PDF. Tente novamente."
  E a tarefa é reprocessada com backoff
```

*Rastreia:* RF-07 · UC-08 · RN-16 · CA-11 · Tela 07.

#### US-07 · Ser avisado sobre atendimento preferencial

**Como** cidadão PCD ou idoso, **quero** saber se a unidade oferece atendimento preferencial, **para que** eu exerça meu direito sem constrangimento.

```gherkin
Cenário: Alerta de prioridade
  Dado que sou PCD ou tenho 60 anos ou mais
  E a unidade selecionada tem atendimento preferencial
  Quando abro a ficha ou o guia
  Então vejo o alerta de prioridade com a base legal
```

*Rastreia:* RF-07 · RF-04 · UC-08 · RN-17 · CA-15 · Telas 05, 06.

### Épico C — Agendamento e acompanhamento

#### US-08 · Ver horários realmente disponíveis

**Como** cidadão, **quero** ver apenas horários livres, **para que** eu não escolha um horário que será recusado.

```gherkin
Cenário: Slots do dia
  Dado que escolhi serviço, unidade e data
  Então vejo intervalos de 30 minutos dentro do horário de funcionamento
  E não vejo feriados, dias sem atendimento nem slots lotados

Cenário: Data passada
  Quando tento agendar para ontem
  Então o sistema bloqueia com "Não é possível agendar em data passada."
```

*Rastreia:* RF-08 · UC-09 · RN-18, RN-19 · CA-12, CA-13 · Tela 08.

#### US-09 · Agendar e receber protocolo

**Como** cidadão autenticado, **quero** confirmar o atendimento e receber um protocolo, **para que** eu tenha prova do agendamento.

```gherkin
Cenário: Agendamento confirmado
  Dado que estou autenticado e escolhi um slot livre
  Quando confirmo o agendamento
  Então recebo o protocolo no formato AAAAMMDD-XXXX
  E recebo o comprovante em PDF e o aviso por e-mail

Cenário: Agendamento duplicado
  Dado que já tenho agendamento ativo para o mesmo serviço
  Quando tento agendar novamente
  Então vejo "Você já tem um agendamento ativo para este serviço."
```

*Rastreia:* RF-08 · UC-09 · RN-20, RN-21 · CA-12 · Telas 08, 09, 10.

#### US-10 · Remarcar ou cancelar

**Como** cidadão, **quero** remarcar ou cancelar até 24 horas antes, **para que** eu não perca a vaga se minha agenda mudar.

```gherkin
Cenário: Cancelamento dentro do prazo
  Dado que faltam mais de 24 horas para o atendimento
  Quando cancelo com justificativa
  Então o status vira "Cancelado"
  E a vaga é liberada para outro cidadão

Cenário: Cancelamento fora do prazo
  Quando faltam menos de 24 horas
  Então o sistema bloqueia e orienta a contatar a unidade
```

*Rastreia:* RF-08 · UC-10 · RN-22 · CA-12 · Tela 10.

#### US-11 · Acompanhar o protocolo

**Como** cidadão, **quero** ver a linha do tempo do meu pedido, **para que** eu saiba o que está acontecendo sem ligar para a unidade.

```gherkin
Cenário: Linha do tempo
  Dado que abri "Meus pedidos"
  Quando seleciono um protocolo
  Então vejo cada transição com data, hora, responsável e observação
  E vejo o status atual em destaque

Cenário: Protocolo de terceiro
  Quando tento acessar um protocolo que não é meu
  Então recebo 404, sem revelar a existência do registro
```

*Rastreia:* RF-09 · UC-11 · RN-23, RN-24 · CA-14 · Tela 10.

#### US-12 · Anexar documento solicitado

**Como** cidadão, **quero** enviar o documento pedido pelo servidor, **para que** meu pedido volte para análise sem eu ir à unidade.

```gherkin
Cenário: Upload válido
  Dado que o protocolo está em "Aguardando documento"
  Quando envio um PDF de 2 MB
  Então o status volta para "Em análise"
  E o servidor vê o anexo na linha do tempo

Cenário: Arquivo inválido
  Quando envio um .exe de 12 MB
  Então vejo "Formato inválido. Envie jpg, png ou pdf de até 10 MB."
```

*Rastreia:* RF-09 · UC-12 · RS-04 · RN-25 · CA-14 · Tela 10.

### Épico D — Conta e acesso

#### US-13 · Criar conta manualmente

**Como** cidadão, **quero** criar minha conta no SOSP com meus dados pessoais e senha, **para que** eu possa agendar e acompanhar pedidos.

```gherkin
Cenário: Cadastro bem-sucedido com CEP encontrado
  Dado que estou na tela de login
  Quando escolho "Criar conta" e preencho todos os campos obrigatórios
  E informo um CEP válido
  Então o sistema preenche logradouro, bairro, município e UF
  E a conta é criada com sucesso
  E recebo o e-mail de confirmação

Cenário: CEP não encontrado
  Quando informo um CEP inexistente
  Então vejo "Endereço não localizado"
  E posso digitar o endereço manualmente com Município e UF do IBGE

Cenário: CPF duplicado
  Quando informo um CPF já cadastrado
  Então vejo "CPF já cadastrado"

Cenário: Idade insuficiente
  Quando a data de nascimento indica menos de 12 anos
  Então vejo "É necessário ter 12 anos ou mais para se cadastrar."

Cenário: Senha fraca
  Quando a senha não atende aos requisitos mínimos
  Então vejo as regras: mínimo 8 caracteres, 1 maiúscula, 1 número e 1 caractere especial
```

*Rastreia:* RF-01 · UC-01 · RN-26, RN-27 · CA-16 · Telas 01, 02, 14, W08, W10.

#### US-14 · Entrar no sistema

**Como** cidadão, **quero** entrar com meu CPF e senha, **para que** eu acesse meus agendamentos e protocolos.

```gherkin
Cenário: Login bem-sucedido
  Quando informo CPF e senha corretos
  Então entro no sistema e sou redirecionado à ação de origem

Cenário: Senha incorreta
  Quando informo senha errada
  Então vejo "CPF ou senha inválidos"
  E o contador de tentativas é incrementado

Cenário: Bloqueio por tentativas
  Quando excedo 5 tentativas incorretas
  Então vejo "Conta temporariamente bloqueada. Tente novamente em 5 minutos."

Cenário: Sessão expirada
  Dado que fiquei 30 minutos sem uso
  Quando tento agendar
  Então sou convidado a entrar novamente e retorno ao agendamento

Cenário: Gov.br indisponível (futuro)
  Quando clico em "Entrar com Gov.br"
  Então vejo um modal informando "A integração com o Gov.br estará disponível em uma futura atualização (v2.0). Utilize seu CPF e senha para entrar."
  E vejo o botão "Entendi, quero usar CPF e senha" que fecha o modal
```

*Rastreia:* RF-02 · UC-02 · RN-28, RN-29 · CA-16 · Telas 01, 02, W08.

#### US-15 · Recuperar senha

**Como** cidadão ou servidor, **quero** recuperar minha senha por código enviado ao e-mail, **para que** eu recupere o acesso sem depender de administrador.

```gherkin
Cenário: Código válido
  Quando informo CPF e e-mail cadastrado e recebo o código de 6 dígitos
  E defino uma nova senha dentro de 15 minutos
  Então o acesso é liberado

Cenário: Código expirado
  Quando o código tem mais de 15 minutos
  Então vejo "Código expirado. Solicite um novo."

Cenário: E-mail não cadastrado
  Quando informo um e-mail que não consta na conta
  Então vejo "E-mail não encontrado para este CPF."
```

*Rastreia:* RF-02 · UC-02 · RN-30 · CA-16.

### Épico E — Back-office

#### US-16 · Gerenciar órgãos e unidades

**Como** administrador, **quero** manter órgãos e unidades, **para que** o catálogo e a ficha tenham dados confiáveis de origem.

```gherkin
Cenário: Sigla duplicada
  Quando cadastro a sigla "DETRAN" para a esfera Estadual já existente
  Então vejo "Já existe um órgão com esta sigla nesta esfera."

Cenário: Unidade sem horário
  Quando deixo um dia da semana sem horário
  Então a unidade é considerada fechada naquele dia
```

*Rastreia:* RF-03, RF-04 · UC-03, UC-04 · RN-31, RN-32 · CA-17.

#### US-17 · Publicar um serviço

**Como** servidor autorizado, **quero** publicar um serviço com todas as orientações, **para que** o cidadão encontre a informação completa.

```gherkin
Cenário: Publicação bloqueada por lacuna
  Dado que o serviço não tem documento obrigatório nem etapa
  Quando tento publicar
  Então vejo a lista de pendências e o status permanece "Rascunho"

Cenário: Nova versão
  Quando altero o prazo de um serviço publicado
  Então uma nova versão é criada e o histórico é preservado
```

*Rastreia:* RF-05 · UC-05 · RN-33, RN-34 · CA-17.

#### US-18 · Gerenciar usuários internos

**Como** administrador, **quero** criar servidores e conceder a permissão de catálogo, **para que** cada secretaria mantenha seus próprios serviços.

```gherkin
Cenário: Permissão granular
  Quando marco "Gerenciar catálogo de serviços" para um servidor
  Então ele passa a publicar serviços, sem acesso à gestão de usuários

Cenário: Primeiro acesso
  Quando o servidor entra com a senha temporária
  Então a troca de senha é obrigatória
```

*Rastreia:* RF-12 · UC-15 · RN-35 · CA-17.

#### US-19 · Consultar relatórios

**Como** gestor, **quero** ver serviços mais buscados, agendamentos por status, tempo médio e avaliações, **para que** eu corrija lacunas do catálogo.

```gherkin
Cenário: Exportação
  Quando aplico filtro de período e órgão e solicito exportação
  Então recebo CSV ou PDF com os mesmos dados da tela
```

*Rastreia:* RF-14 · UC-17 · RN-36 · CA-18.

#### US-20 · Avaliar o atendimento (v2.0)

**Como** cidadão, **quero** avaliar o atendimento concluído, **para que** eu contribua com a qualidade do serviço.

```gherkin
Cenário: Avaliação única
  Dado que meu protocolo está "Concluído"
  Quando envio nota 5 e comentário
  Então a avaliação é registrada
  E uma segunda tentativa é bloqueada com "Você já avaliou este atendimento."
```

*Rastreia:* RF-10 · UC-13 · RN-37 · CA-19.

#### US-21 · Tirar dúvida pelo FAQ

**Como** cidadão, **quero** consultar perguntas frequentes e, se necessário, abrir uma dúvida, **para que** eu resolva o que a ficha não respondeu.

```gherkin
Cenário: FAQ resolve
  Quando busco "prazo do RG" no FAQ
  Então vejo as 3 perguntas mais relevantes

Cenário: FAQ não resolve
  Quando aceito abrir uma dúvida
  Então um protocolo do tipo "Dúvida" é criado
```

*Rastreia:* RF-11 · UC-14 · RN-38 · CA-20.

### Catálogo consolidado de critérios de aceite

Cada critério é um resultado observável, não uma tarefa. Um mesmo critério pode ser verificado em mais de uma história; a coluna **Histórias** indica onde ele aparece no Gherkin e a coluna **Evidência** indica o tipo de teste que o comprova.

| ID | Critério verificável | RF | Histórias | Evidência |
|---|---|---|---|---|
| CA-01 | Busca por termo retorna serviços ativos ordenados por relevância, com nome, órgão, canal, custo, prazo, total de resultados e paginação de 10 itens | RF-06 | US-01 | Teste de integração + E2E |
| CA-02 | Busca normaliza acentos e caixa: `certidao` e `Certidão` retornam o mesmo conjunto | RF-06 | US-01 | Teste de integração |
| CA-03 | Busca com termo vazio lista todos os serviços ativos por popularidade | RF-06 | US-01 | Teste de integração |
| CA-04 | Filtros de categoria, órgão, canal e município combinam sem perder o termo e refletem o estado na URL | RF-06 | US-02 | Teste de integração + E2E |
| CA-05 | Estado vazio exibe a mensagem literal, sugestões de categoria, caminho para a Ouvidoria e "Limpar filtros" quando há filtros ativos | RF-06 | US-02, US-03 | E2E |
| CA-06 | Ficha de serviço ativo exibe os oito blocos, a data da última atualização e as ações "Ver passo a passo" e "Agendar" | RF-06 | US-04 | E2E |
| CA-07 | Bloco "Onde fazer" exibe unidades e mapa apenas quando há latitude e longitude; sem coordenada, exibe endereço e lista de unidades | RF-06 | US-04 | Teste de componente |
| CA-08 | Serviço inativo não aparece na busca e o acesso direto à ficha retorna 404 | RF-06 | US-04 | Teste de integração |
| CA-09 | Custo e prazo são formatados em PT-BR e exibem "Não informado" quando o dado está ausente | RF-06 | US-04 | Teste de componente |
| CA-10 | Filtro inválido retorna 400 com o campo e o valor recusado | RF-06 | US-02 | Teste de contrato |
| CA-11 | Checklist salva o progresso por CPF, conclui quando todos os documentos obrigatórios estão marcados e o PDF contém nome, serviço, checklist e data/hora em até 5 s | RF-07 | US-05, US-06 | Teste de integração + E2E |
| CA-12 | Agendamento cria protocolo no formato AAAAMMDD-XXXX, bloqueia duplicidade ativa, data passada e overbooking; remarcação ou cancelamento libera a vaga | RF-08 | US-08, US-09, US-10 | Teste de concorrência + E2E |
| CA-13 | Slot lotado entre a exibição e a confirmação retorna 409 e recarrega os slots | RF-08 | US-08 | Teste de concorrência |
| CA-14 | Titular vê a linha do tempo do protocolo com data, hora, responsável e observação; terceiro recebe 404; anexo válido volta o status para "Em análise" | RF-09 | US-11, US-12 | Teste de integração + E2E |
| CA-15 | Alerta de atendimento preferencial aparece para PCD ou 60+ quando a unidade oferece o serviço, com a base legal | RF-07 | US-07 | Teste de componente |
| CA-16 | Cadastro manual com CPF e senha conclui com CEP ou fallback manual; login, logout, sessão de 30 min e recuperação de senha funcionam; CPF duplicado e senha fraca são bloqueados | RF-01, RF-02 | US-13, US-14, US-15 | E2E + teste de integração |
| CA-17 | CRUD de órgãos, unidades, serviços e usuários internos valida duplicidade, campos obrigatórios, versionamento e autorização por perfil | RF-03, RF-04, RF-05, RF-12 | US-16, US-17, US-18 | Teste de integração |
| CA-18 | Relatórios filtram por período e órgão e exportam CSV ou PDF com os mesmos dados da tela; painel de avaliações fica oculto enquanto o RF-10 estiver desligado | RF-14 | US-19 | Teste de integração + E2E |
| CA-19 | Avaliação de protocolo concluído aceita nota de 1 a 5 e comentário de até 500 caracteres; segunda tentativa retorna conflito | RF-10 | US-20 | Teste de integração |
| CA-20 | FAQ retorna as 3 perguntas mais relevantes e, quando não resolve, cria protocolo do tipo "Dúvida" | RF-11 | US-21 | Teste de integração + E2E |
| CA-21 | Preferências de notificação por tipo e canal são salvas e respeitadas no envio; todo envio tem log de status | RF-13 | RF-13 (v2.0) | Teste de integração |

---

## 4. Requisitos Funcionais

### 4.1 Catálogo de requisitos

A prioridade original da disciplina (Essencial / Importante / Desejável) é preservada e mapeada para MoSCoW. O mapeamento é uma decisão de gestão, não uma tradução automática: Essencial → Must, Importante → Should, Desejável → Could. A coluna **Telas no Figma** usa a numeração estável do [índice de telas](design/README.md): `01`–`30` para mobile e `W01`–`W15` para web.

| ID | Requisito | Ator principal | Prioridade original | MoSCoW | Depende de | Telas no Figma | Casos de uso |
|---|---|---|---|---|---|---|---|
| RF-01 | Cadastro do cidadão | Cidadão | Essencial | Must | — | 01, 02, 14, 29, W08, W10 | UC-01 |
| RF-02 | Autenticação e recuperação de acesso | Cidadão, Servidor, Administrador | Essencial | Must | RF-01, RF-12 | 01, 17, W08 | UC-02 |
| RF-03 | Gerenciar órgãos | Administrador | Essencial | Must | — | 21, W13 | UC-03 |
| RF-04 | Gerenciar unidades de atendimento | Administrador | Essencial | Must | RF-03 | 22, W13 | UC-04 |
| RF-05 | Gerenciar catálogo de serviços | Administrador, Servidor autorizado | Essencial | Must | RF-03 | 28, W12 | UC-05 |
| RF-06 | Busca e ficha orientativa | Cidadão | Essencial | Must | RF-04, RF-05 | 03, 04, 05, 19, 22, 26, 27, W01, W02, W03 | UC-06, UC-07 |
| RF-07 | Guia passo a passo + checklist | Cidadão | Essencial | Must | RF-05, RF-06 | 06, 07, W04 | UC-08 |
| RF-08 | Agendamento de atendimento | Cidadão, Servidor | Importante | Should | RF-04, RF-05 | 08, 09, 10, 24, 25, W05 | UC-09, UC-10 |
| RF-09 | Acompanhar protocolo | Cidadão, Servidor | Importante | Should | RF-08, RF-11 | 10, 11, 12, 15, W06, W07 | UC-11, UC-12 |
| RF-10 | Avaliação e comentário | Cidadão | Desejável | Could | RF-08, RF-09 | 23 (v2.0) | UC-13 |
| RF-11 | FAQ e assistente de dúvida | Administrador, Cidadão | Importante | Should | RF-05 | 13, W09 | UC-14 |
| RF-12 | Gerenciar usuários internos | Administrador | Essencial | Must | RF-03 | W14 | UC-15 |
| RF-13 | Notificações | Sistema | Desejável | Could | RF-01, RF-08, RF-09 | — (v2.0) | UC-16 |
| RF-14 | Relatórios gerenciais | Administrador, Servidor | Importante | Should | RF-06, RF-08, RF-09, RF-10 | W11, W15 | UC-17 |

### 4.2 Catálogo de casos de uso

O caso de uso descreve o objetivo do ator, não a tela. A coluna **Histórias** liga o caso de uso às histórias que o exercitam; a coluna **Fluxo** aponta para o detalhamento no RF correspondente. O detalhamento completo — ator, pré-condições, gatilho, fluxo principal, fluxos alternativos, exceções, pós-condições, RN/CA e contrato — está em [Casos de uso](use-cases/README.md), com diagrama e matriz de rastreabilidade.

| ID | Caso de uso | Ator principal | RF | Histórias | Fluxo |
|---|---|---|---|---|---|
| UC-01 | Concluir cadastro do cidadão | Cidadão | RF-01 | US-13 | RF-01, fluxo principal e alternativos A1 a A6 |
| UC-02 | Autenticar e recuperar acesso | Cidadão, Servidor, Administrador | RF-02 | US-14, US-15 | RF-02, fluxos do cidadão e do servidor |
| UC-03 | Gerenciar órgãos | Administrador | RF-03 | US-16 | RF-03, campos e validações |
| UC-04 | Gerenciar unidades | Administrador | RF-04 | US-16 | RF-04, campos e validações |
| UC-05 | Publicar e versionar serviço | Administrador, Servidor autorizado | RF-05 | US-17 | RF-05, campos e validações |
| UC-06 | Buscar serviços | Cidadão | RF-06 | US-01, US-02, US-03 | RF-06, fluxo principal e alternativos A1 e A3 |
| UC-07 | Consultar ficha orientativa | Cidadão | RF-06 | US-04 | RF-06, blocos da ficha e alternativa A2 |
| UC-08 | Seguir guia e gerar PDF | Cidadão | RF-07 | US-05, US-06, US-07 | RF-07, fluxo principal |
| UC-09 | Agendar atendimento | Cidadão | RF-08 | US-08, US-09 | RF-08, fluxo principal e alternativos A1 a A3 |
| UC-10 | Remarcar ou cancelar agendamento | Cidadão | RF-08 | US-10 | RF-08, alternativa A4 |
| UC-11 | Acompanhar protocolo | Cidadão, Servidor | RF-09 | US-11 | RF-09, estados do protocolo |
| UC-12 | Anexar documento ao protocolo | Cidadão | RF-09 | US-12 | RF-09, estado "Aguardando documento" |
| UC-13 | Avaliar atendimento | Cidadão | RF-10 | US-20 | RF-10, campos e regra RN-37 |
| UC-14 | Consultar FAQ e abrir dúvida | Cidadão | RF-11 | US-21 | RF-11, campos e regra RN-38 |
| UC-15 | Gerenciar usuários internos | Administrador | RF-12 | US-18 | RF-12, campos e permissões |
| UC-16 | Notificar cidadão | Sistema | RF-13 | RF-13 (v2.0) | RF-13, canais e preferências |
| UC-17 | Gerar relatórios gerenciais | Administrador, Servidor | RF-14 | US-19 | RF-14, filtros, relatórios e saída |

### 4.3 Regras de negócio

As regras são numeradas uma única vez e citadas por todo o documento. Uma regra sem verificação automatizada é uma intenção, não uma regra.

| ID | Regra | Origem | Verificação |
|---|---|---|---|
| RN-01 | A busca textual cobre nome, descrição, categoria, órgão e sinônimos, com normalização de acentos e caixa | RF-06 | Teste de integração |
| RN-02 | O termo vazio é permitido e lista todos os serviços ativos | RF-06 | Teste de API |
| RN-03 | Os filtros são combináveis por interseção (AND) e persistidos na URL | RF-06 | Teste E2E |
| RN-04 | Os filtros oficiais são Categoria, Órgão, Canal e Município | RF-06 | Contrato OpenAPI |
| RN-05 | A lista retorna 10 itens por página, com total e paginação | RF-06 | Teste de contrato |
| RN-06 | A ficha é montada exclusivamente com dados do RF-05 e do RF-04 | RF-06 | Teste de integração |
| RN-07 | A ficha só é publicada se os oito blocos estiverem completos | RF-05, RF-06 | Checklist de publicação |
| RN-08 | Custo e prazo são exibidos em linguagem simples ("Gratuito", "Até 10 dias") | RF-06 | Revisão de conteúdo |
| RN-09 | Documentos obrigatórios e opcionais são diferenciados visualmente e por texto | RF-06 | Teste de acessibilidade |
| RN-10 | O mapa só aparece quando a unidade tem latitude e longitude | RF-06 | Teste de componente |
| RN-11 | A média de avaliações só aparece quando o RF-10 estiver habilitado | RF-06, RF-10 | Feature flag |
| RN-12 | Toda busca é registrada sem dados pessoais: termo, filtros, contagem e data | RF-06, RF-14 | Teste de integração |
| RN-13 | A busca sem resultado exibe a mensagem literal do RF-06 | RF-06 | Teste E2E |
| RN-14 | O progresso do checklist é salvo por CPF e por serviço | RF-07 | Teste de integração |
| RN-15 | O guia exibe as etapas na ordem cadastrada, com título, descrição e tempo | RF-07 | Teste de API |
| RN-16 | O PDF é gerado de forma assíncrona em até 5 segundos | RF-07 | Teste de performance |
| RN-17 | O alerta de prioridade exige PCD ou 60+ e unidade com atendimento preferencial | RF-07, RF-04 | Teste unitário |
| RN-18 | Slots têm 30 minutos e ficam dentro do horário de funcionamento | RF-08 | Teste unitário |
| RN-19 | Feriados e dias sem atendimento não geram slots | RF-08, RF-04 | Teste de integração |
| RN-20 | O protocolo segue AAAAMMDD-XXXX com sequência diária de 4 dígitos | RF-08 | Teste unitário |
| RN-21 | O mesmo CPF não pode ter dois agendamentos ativos para o mesmo serviço | RF-08 | Constraint + teste |
| RN-22 | Remarcar e cancelar só até 24 horas antes | RF-08 | Teste de integração |
| RN-23 | A linha do tempo registra data, hora, responsável e observação | RF-09 | Teste de integração |
| RN-24 | Concluído e Cancelado são estados finais | RF-09 | Máquina de estados |
| RN-25 | Anexos aceitam jpg, png e pdf até 10 MB, com verificação antivírus | RF-09, RS-04 | Teste de segurança |
| RN-26 | CPF é único, imutável e validado pelo dígito verificador | RF-01 | Constraint + teste |
| RN-27 | CEP não encontrado libera digitação manual com Município e UF do IBGE | RF-01 | Teste de integração |
| RN-28 | A sessão expira após 30 minutos sem uso | RF-02 | Teste de sessão |
| RN-29 | Após 5 tentativas erradas, o acesso é bloqueado por 5 minutos | RF-02 | Teste de segurança |
| RN-30 | O código de recuperação tem 6 dígitos e vale 15 minutos | RF-02 | Teste de segurança |
| RN-31 | Não há dois órgãos com a mesma sigla na mesma esfera | RF-03 | Constraint |
| RN-32 | Não há duas unidades com o mesmo nome e município para o mesmo órgão | RF-04 | Constraint |
| RN-33 | Serviço publicado exige ao menos uma etapa e um documento obrigatório | RF-05 | Checklist de publicação |
| RN-34 | Toda alteração de serviço gera nova versão com histórico | RF-05 | Trigger/teste |
| RN-35 | Servidor só gerencia catálogo com a permissão explícita | RF-12 | Teste de autorização |
| RN-36 | Relatórios respeitam o escopo do órgão do servidor | RF-14 | Teste de autorização |
| RN-37 | Só existe uma avaliação por protocolo concluído | RF-10 | Constraint |
| RN-38 | O FAQ devolve no máximo 3 resultados por busca | RF-11 | Teste de API |
| RN-39 | Toda alteração administrativa grava auditoria com antes e depois | Transversal | Trigger/teste |
| RN-40 | Exclusão é sempre lógica; nenhum registro é apagado fisicamente | Transversal | Revisão de schema |

### 4.4 Detalhamento por requisito

#### RF-01 · Cadastro do cidadão

| Atributo | Definição |
|---|---|
| **Objetivo** | Criar a conta do cidadão com dados pessoais, endereço e senha |
| **Atores** | Cidadão |
| **Prioridade** | Essencial · Must |
| **Pré-condições** | — |
| **Pós-condições** | Conta ativa com hash Argon2id, e-mail de confirmação enviado |
| **Dependências** | ViaCEP, IBGE, serviço de e-mail |

**Fluxo principal**

1. Cidadão acessa "Criar conta" e informa CPF, nome completo, data de nascimento, e-mail, celular, gênero, PCD (e descrição se aplicável), nome da mãe e nome do pai (opcional).
2. Cidadão informa senha (mínimo 8 caracteres, 1 maiúscula, 1 número, 1 caractere especial) e confirmação.
3. Cidadão informa CEP; o sistema consulta ViaCEP e preenche logradouro, bairro, município e UF.
4. Cidadão informa número, complemento (opcional) e foto/avatar (opcional).
5. Sistema valida todos os campos; CPF validado pelo dígito verificador e unicidade; senha armazenada com hash Argon2id + salt.
6. Sistema cria a conta e envia e-mail de confirmação.
7. Sistema exibe "Cadastro realizado com sucesso" e redireciona para o login.

**Fluxos alternativos**

| ID | Situação | Comportamento |
|---|---|---|
| A1 | CEP não encontrado | Exibe "Endereço não localizado", libera digitação manual e seleção de Município/UF do IBGE |
| A2 | CPF já cadastrado | Exibe "CPF já cadastrado" e sugere recuperação de senha |
| A3 | E-mail já cadastrado | Exibe "E-mail já cadastrado em outra conta" |
| A4 | Cancelamento | Pergunta "Todas as alterações serão perdidas. Deseja realmente cancelar?" com Sim/Não |
| A5 | Idade menor que 12 anos | Bloqueia com "É necessário ter 12 anos ou mais para se cadastrar." |
| A6 | Senha não atende requisitos | Exibe as regras: mínimo 8 caracteres, 1 maiúscula, 1 número, 1 caractere especial |

**Campos e validações**

| Campo | Tipo | Obrigatório | Regra | Mensagem de erro |
|---|---|---|---|---|
| CPF | texto(14) | Sim | Máscara XXX.XXX.XXX-XX, dígito verificador, único, imutável | "CPF inválido." / "CPF já cadastrado" |
| Nome completo | texto(120) | Sim | Mínimo 3 caracteres, apenas letras e espaços | "Campo preenchido incorretamente" |
| Data de nascimento | data | Sim | Idade ≥ 12 anos | "É necessário ter 12 anos ou mais para se cadastrar." |
| E-mail | texto(200) | Sim | Formato texto@texto.texto, único | "E-mail já cadastrado" |
| Celular/WhatsApp | texto(15) | Sim | Máscara (XX)9XXXX-XXXX | "Campo preenchido incorretamente" |
| Gênero | seleção | Sim | Lista auxiliar ativa | "Campo(s) obrigatório(s) não preenchido(s)" |
| PCD | booleano | Sim | Se sim, exige descrição | "Informe qual deficiência." |
| Qual deficiência | texto(120) | Condicional | Obrigatório se PCD = sim; dado sensível com acesso restrito | "Campo(s) obrigatório(s) não preenchido(s)" |
| Nome da mãe | texto(120) | Sim | — | "Campo(s) obrigatório(s) não preenchido(s)" |
| Nome do pai | texto(120) | Não | — | — |
| Senha | texto(128) | Sim | Mín. 8 caracteres, 1 maiúscula, 1 número, 1 especial; hash Argon2id + salt | "A senha deve ter no mínimo 8 caracteres, 1 letra maiúscula, 1 número e 1 caractere especial." |
| Confirmar senha | texto(128) | Sim | Deve coincidir com Senha | "As senhas não coincidem." |
| CEP | texto(9) | Sim | Máscara XXXXX-XXX, consulta ViaCEP | "Endereço não localizado" |
| Logradouro | texto(120) | Sim | Preenchido pelo ViaCEP ou manual | "Campo(s) obrigatório(s) não preenchido(s)" |
| Bairro | texto(80) | Sim | Preenchido pelo ViaCEP ou manual | "Campo(s) obrigatório(s) não preenchido(s)" |
| Município | texto(80) | Sim | ViaCEP ou lista IBGE | "Campo(s) obrigatório(s) não preenchido(s)" |
| UF | texto(2) | Sim | ViaCEP ou lista IBGE | "Campo(s) obrigatório(s) não preenchido(s)" |
| Número | texto(10) | Sim | Aceita "S/N" | "Campo(s) obrigatório(s) não preenchido(s)" |
| Complemento | texto(60) | Não | — | — |
| Foto/Avatar | arquivo | Não | jpg/png até 2 MB, nome = CPF | "Envie uma imagem jpg ou png de até 2 MB." |

**Regras:** RN-26, RN-27, RN-39, RN-40. **Critérios de aceite:** CA-16.

#### RF-02 · Autenticação e recuperação de acesso

| Atributo | Definição |
|---|---|
| **Objetivo** | Permitir entrada segura com CPF + senha e exibir apenas as funções do perfil |
| **Atores** | Cidadão, Servidor, Administrador |
| **Prioridade** | Essencial · Must |
| **Pré-condições** | Conta ativa (RF-01 ou RF-12) |
| **Dependências** | Serviço de e-mail |

**Fluxo principal — cidadão, servidor e administrador**

1. Usuário informa CPF e senha.
2. Sistema consulta a conta pelo CPF e recupera o hash Argon2id + salt.
3. Sistema verifica bloqueio por tentativas (5 tentativas em 5 minutos).
4. Sistema valida a senha contra o hash.
5. Sistema abre a sessão com expiração de 30 minutos de inatividade e registra o acesso.
6. Sistema redireciona à ação de origem.

**Botão "Entrar com Gov.br" (implementação futura)**

O botão "Entrar com Gov.br" permanece na tela de login para demonstrar a visão de produto. Quando clicado, exibe um modal informativo:

> **"A integração com o Gov.br estará disponível em uma futura atualização (v2.0). Utilize seu CPF e senha para entrar."**

O modal contém um botão "Entendi, quero usar CPF e senha" que o fecha e mantém o foco no formulário de CPF + senha.

**Fluxos alternativos**

| ID | Situação | Comportamento |
|---|---|---|
| A1 | 5 tentativas erradas | Bloqueio de 5 minutos, mensagem genérica "CPF ou senha inválidos. Você tem X tentativa(s) restante(s)." |
| A2 | Sessão expirada | Redireciona ao login preservando o retorno |
| A3 | Senha temporária (servidor) | Exige troca no primeiro acesso |
| A4 | Recuperação de senha | Código de 6 dígitos enviado por e-mail, válido por 15 minutos |
| A5 | Gov.br clicado | Exibe modal de "implementação futura" conforme descrito acima |

**Critérios de aceite:** CA-16.

#### RF-03 · Gerenciar órgãos

| Atributo | Definição |
|---|---|
| **Objetivo** | Manter os órgãos públicos atendidos pelo sistema |
| **Ator** | Administrador |
| **Prioridade** | Essencial · Must |

**Campos e validações**

| Campo | Tipo | Obrigatório | Regra | Mensagem |
|---|---|---|---|---|
| Nome | texto(120) | Sim | — | "Campo(s) obrigatório(s) não preenchido(s)" |
| Sigla | texto(10) | Sim | Única por esfera | "Já existe um órgão com esta sigla nesta esfera." |
| Esfera | seleção | Sim | Municipal, Estadual, Federal | "Campo(s) obrigatório(s) não preenchido(s)" |
| Descrição | texto(500) | Não | — | — |
| Status | seleção | Sim | Ativo/Inativo | — |

**Regras:** RN-31, RN-39, RN-40. **Critérios de aceite:** CA-17.

#### RF-04 · Gerenciar unidades de atendimento

| Atributo | Definição |
|---|---|
| **Objetivo** | Manter os locais presenciais, horários e dias sem atendimento |
| **Ator** | Administrador |
| **Prioridade** | Essencial · Must |

**Campos e validações**

| Campo | Tipo | Obrigatório | Regra | Mensagem |
|---|---|---|---|---|
| Órgão | referência | Sim | Órgão ativo | "Selecione um órgão ativo." |
| Nome | texto(120) | Sim | Único por órgão + município | "Já existe uma unidade com este nome neste município." |
| CEP | texto(9) | Sim | ViaCEP | "Endereço não localizado" |
| Logradouro | texto(120) | Sim | ViaCEP/manual | "Campo(s) obrigatório(s) não preenchido(s)" |
| Bairro | texto(80) | Sim | ViaCEP/manual | "Campo(s) obrigatório(s) não preenchido(s)" |
| Município | texto(80) | Sim | ViaCEP/IBGE | "Campo(s) obrigatório(s) não preenchido(s)" |
| UF | texto(2) | Sim | ViaCEP/IBGE | "Campo(s) obrigatório(s) não preenchido(s)" |
| Número | texto(10) | Sim | — | "Campo(s) obrigatório(s) não preenchido(s)" |
| Telefone | texto(15) | Não | (XX)XXXX-XXXX | "Campo preenchido incorretamente" |
| E-mail | texto(200) | Não | Formato de e-mail | "Campo preenchido incorretamente" |
| Horário por dia | hora | Não | Abertura e fechamento HH:MM; vazio = fechado | "Horário inválido." |
| Limite diário | inteiro | Sim | > 0, sugestão 40 | "Informe um limite maior que zero." |
| Latitude | decimal(9,6) | Não | -90 a 90 | "Coordenada inválida." |
| Longitude | decimal(9,6) | Não | -180 a 180 | "Coordenada inválida." |
| Acessível PCD | booleano | Sim | — | — |
| Atendimento preferencial | booleano | Sim | — | — |
| Status | seleção | Sim | Ativo/Inativo | — |

**Regras:** RN-19, RN-32, RN-39, RN-40. **Critérios de aceite:** CA-17.

#### RF-05 · Gerenciar catálogo de serviços

| Atributo | Definição |
|---|---|
| **Objetivo** | Publicar e versionar os serviços com todas as orientações da ficha |
| **Atores** | Administrador, Servidor autorizado |
| **Prioridade** | Essencial · Must |

**Campos e validações**

| Campo | Tipo | Obrigatório | Regra | Mensagem |
|---|---|---|---|---|
| Nome | texto(150) | Sim | — | "Campo(s) obrigatório(s) não preenchido(s)" |
| Categoria | seleção | Sim | Saúde, Educação, Documentos, Transporte, Assistência Social, Tributos, Trabalho | "Selecione uma categoria." |
| Descrição detalhada | texto(4000) | Sim | Responde "o que é" | "Campo(s) obrigatório(s) não preenchido(s)" |
| Quem tem direito | texto(1000) | Sim | — | "Campo(s) obrigatório(s) não preenchido(s)" |
| Órgãos vinculados | referência múltipla | Sim | ≥ 1 órgão ativo | "Vincule ao menos um órgão." |
| Pré-requisitos | texto(2000) | Não | — | — |
| Documentos | lista | Sim | ≥ 1 obrigatório, nome até 120, modelo PDF até 10 MB | "Inclua ao menos um documento obrigatório." |
| Custo | moeda | Sim | Gratuito ou 0,01 a 99.999,99 | "Informe um custo válido." |
| Prazo médio | inteiro | Sim | 0 a 365 dias | "Informe um prazo entre 0 e 365 dias." |
| Canal | seleção | Sim | Online, Presencial, Híbrido | "Selecione o canal." |
| Link externo | URL(300) | Condicional | https://, obrigatório se Online/Híbrido | "Informe um link https:// válido." |
| Etapas | lista | Sim | ≥ 1, ordem, título(100), descrição(1000), tempo(30) | "Inclua ao menos uma etapa." |
| Status | seleção | Sim | Rascunho, Ativo, Inativo | — |

**Regras:** RN-07, RN-33, RN-34, RN-39, RN-40. **Critérios de aceite:** CA-17.

#### RF-06 · Busca e ficha orientativa

| Atributo | Definição |
|---|---|
| **Objetivo** | Localizar um serviço e apresentar a ficha resumida com as orientações |
| **Ator** | Cidadão (logado ou não) |
| **Prioridade** | Essencial · Must |
| **Pré-condições** | Serviço ativo e publicado |
| **Dependências** | RF-04, RF-05 |

**Fluxo principal**

1. Cidadão informa palavra-chave e, opcionalmente, filtros.
2. Sistema normaliza o termo, consulta o índice full-text e aplica os filtros.
3. Sistema ordena por relevância e retorna 10 itens por página.
4. Cidadão seleciona um serviço.
5. Sistema monta a ficha com os oito blocos e as ações disponíveis.
6. Sistema registra o termo buscado para relatórios.

**Fluxos alternativos**

| ID | Situação | Comportamento |
|---|---|---|
| A1 | Nenhum resultado | Mensagem literal "Nenhum serviço encontrado. Tente outro termo ou categoria." + sugestões + Ouvidoria |
| A2 | Serviço inativo | Não aparece na busca; acesso direto retorna 404 |
| A3 | Filtro inválido | Retorna 400 com o campo e o valor recusado |
| A4 | Ação que exige login | Redireciona ao Gov.br preservando a ação de origem |

**Blocos da ficha**

| # | Bloco | Conteúdo | Origem |
|---|---|---|---|
| 1 | O que é | Descrição detalhada | RF-05 |
| 2 | Quem tem direito | Público elegível | RF-05 |
| 3 | O que levar | Documentos obrigatórios e opcionais | RF-05 |
| 4 | Como fazer | Títulos das etapas e tempo estimado | RF-05 |
| 5 | Onde fazer | Unidades, endereço e mapa condicional | RF-04 |
| 6 | Quando | Horário de funcionamento da unidade | RF-04 |
| 7 | Quanto custa | Gratuito ou valor | RF-05 |
| 8 | Quanto demora | Prazo médio em dias | RF-05 |

**Regras:** RN-01 a RN-13. **Critérios de aceite:** CA-01 a CA-10.

#### RF-07 · Guia passo a passo + checklist

| Atributo | Definição |
|---|---|
| **Objetivo** | Orientar o cidadão etapa por etapa, com checklist e PDF |
| **Ator** | Cidadão |
| **Prioridade** | Essencial · Must |
| **Dependências** | RF-05, RF-06 |

**Fluxo principal**

1. Cidadão abre o guia a partir da ficha.
2. Sistema lista as etapas numeradas com título, descrição e tempo.
3. Sistema lista os documentos com caixa de marcação.
4. Cidadão marca os documentos já separados; o progresso é salvo por CPF.
5. Cidadão pode gerar um PDF com nome, serviço, checklist e data/hora.
6. Se PCD ou 60+ e a unidade tiver atendimento preferencial, o alerta é exibido.

**Regras:** RN-14 a RN-17. **Critérios de aceite:** CA-11, CA-15.

#### RF-08 · Agendamento de atendimento

| Atributo | Definição |
|---|---|
| **Objetivo** | Reservar um horário presencial e emitir protocolo |
| **Atores** | Cidadão (solicita), Servidor (gerencia) |
| **Prioridade** | Importante · Should |
| **Dependências** | RF-04, RF-05 |

**Fluxo principal**

1. Cidadão autenticado escolhe serviço, unidade e data.
2. Sistema calcula slots de 30 minutos dentro do horário de funcionamento, descontando feriados, dias sem atendimento e lotação.
3. Cidadão escolhe o slot e confirma.
4. Sistema grava o agendamento em transação, gera o protocolo AAAAMMDD-XXXX e o comprovante em PDF.
5. Sistema envia aviso por e-mail.

**Fluxos alternativos**

| ID | Situação | Comportamento |
|---|---|---|
| A1 | Slot lotado entre a exibição e a confirmação | Retorna 409 e recarrega os slots |
| A2 | Agendamento duplicado | Bloqueia com "Você já tem um agendamento ativo para este serviço." |
| A3 | Data passada | Bloqueia com "Não é possível agendar em data passada." |
| A4 | Cancelamento fora do prazo | Bloqueia e orienta contatar a unidade |

**Regras:** RN-18 a RN-22. **Critérios de aceite:** CA-12, CA-13.

#### RF-09 · Acompanhar protocolo

| Atributo | Definição |
|---|---|
| **Objetivo** | Mostrar o andamento do pedido em linha do tempo |
| **Atores** | Cidadão, Servidor |
| **Prioridade** | Importante · Should |
| **Dependências** | RF-08, RF-11 |

**Estados do protocolo**

| Estado | Quem altera | Condição |
|---|---|---|
| Recebido | Sistema | Criação automática |
| Em análise | Servidor | Servidor assume o pedido |
| Aguardando documento | Servidor | Solicitação com observação |
| Em análise (retorno) | Sistema | Cidadão anexa o documento |
| Agendado | Servidor/Sistema | Atendimento confirmado |
| Concluído | Servidor | Finalização |
| Cancelado | Cidadão/Servidor | Até 24 h antes ou com motivo |

**Regras:** RN-23 a RN-25. **Critérios de aceite:** CA-14.

#### RF-10 · Avaliação e comentário (v2.0)

| Atributo | Definição |
|---|---|
| **Objetivo** | Avaliar o atendimento concluído com nota e comentário |
| **Ator** | Cidadão |
| **Prioridade** | Desejável · Could |
| **Dependências** | RF-08, RF-09 |

**Campos:** nota (1 a 5, obrigatória), comentário (até 500 caracteres, opcional).
**Regras:** RN-37, RN-11. **Critérios de aceite:** CA-19.

#### RF-11 · FAQ e assistente de dúvida

| Atributo | Definição |
|---|---|
| **Objetivo** | Responder dúvidas frequentes e abrir protocolo quando o FAQ não resolve |
| **Atores** | Administrador (cadastra), Cidadão (consulta) |
| **Prioridade** | Importante · Should |

**Campos:** pergunta (300), resposta (2000), vínculo (serviço ou categoria).
**Regras:** RN-38. **Critérios de aceite:** CA-20.

#### RF-12 · Gerenciar usuários internos

| Atributo | Definição |
|---|---|
| **Objetivo** | Criar e manter servidores e administradores com permissões granulares |
| **Ator** | Administrador |
| **Prioridade** | Essencial · Must |

**Campos:** dados básicos do RF-01, matrícula única (20), órgão lotado, nível (Administrador/Servidor), permissão "Gerenciar catálogo de serviços", status.
**Regras:** RN-35, RN-39, RN-40. **Critérios de aceite:** CA-17.

#### RF-13 · Notificações (v2.0)

| Atributo | Definição |
|---|---|
| **Objetivo** | Avisar o cidadão sobre conta, agendamento, lembrete, mudança de status e resposta de dúvida |
| **Ator** | Sistema |
| **Prioridade** | Desejável · Could |

**Canais:** e-mail transacional no MVP, dentro do RF-08/RF-09. Push no navegador, SMS e WhatsApp ficam para a v2.0/Fase 3, atrás de `FEATURE_PUSH_ENABLED`, `FEATURE_SMS_ENABLED` e `FEATURE_WHATSAPP_ENABLED` ([ADR-007](adr/ADR-007-feature-flags.md)).
**Regras:** preferência opt-in/opt-out por tipo; log de envio com status.
**Critérios de aceite:** CA-21.

#### RF-14 · Relatórios gerenciais

| Atributo | Definição |
|---|---|
| **Objetivo** | Acompanhar uso, demanda e qualidade do catálogo |
| **Atores** | Administrador, Servidor |
| **Prioridade** | Importante · Should |

**Filtros:** período, órgão, serviço, unidade.
**Relatórios:** serviços mais buscados, agendamentos por status, tempo médio de conclusão, média das avaliações.
**Saída:** tela paginada com gráfico de barras e exportação CSV/PDF.
**Escopo do MVP:** todos os relatórios acima são entregues, exceto o painel de avaliações, que depende do RF-10 e fica oculto por `FEATURE_REVIEWS_ENABLED=false`. A exportação CSV/PDF é do MVP e controlada por `FEATURE_REPORTS_EXPORT`.
**Regras:** RN-36. **Critérios de aceite:** CA-18.

---

## 5. Requisitos Não-Funcionais

Os RNFs originais foram preservados e transformados em metas verificáveis. Onde o documento dizia "até 3 s", este documento define p95, p99 e condição de carga.

| ID | Categoria | Requisito original | Meta verificável | Verificação |
|---|---|---|---|---|
| RNF-01 | Usabilidade | Interface intuitiva com hints, ajuda contextual e glossário | SUS ≥ 75 em teste com 5 cidadãos; 0 erros críticos de navegação na jornada de busca | Teste de usabilidade |
| RNF-02 | Usabilidade | Mensagens de erro claras | 100% dos erros de validação com mensagem associada ao campo e ação de correção | Revisão + axe-core |
| RNF-03 | Hardware | Servidor 4 GHz/64 GB; usuário 2 GHz/4 GB | Infraestrutura em contêineres com 2 vCPU/4 GB por réplica de API, 2 réplicas mínimas; cliente com navegador atualizado e 2 GB de RAM | Revisão de infraestrutura |
| RNF-04 | Desempenho | Busca e ficha em até 3 s com 1.000 acessos simultâneos | Busca e ficha: p95 ≤ 2,5 s e p99 ≤ 3 s com 1.000 usuários simultâneos; PDF: p95 ≤ 4 s e p99 ≤ 5 s | Teste de carga k6 |
| RNF-05 | Compatibilidade | Web responsivo, Chrome, Edge, Firefox; 99% no horário comercial | 390 px a 1440 px; últimas 2 versões dos três navegadores; disponibilidade ≥ 99,0% em 08h–18h úteis, com error budget mensal de 2,2 h | Monitoração + testes cross-browser |
| RNF-06 | Acessibilidade | WCAG 2.1 AA, teclado, fonte ampliável, leitor de tela | 0 violações críticas no axe-core; navegação completa por teclado; zoom 200% sem perda de conteúdo; contraste 4,5:1 | Auditoria + testes |
| RNF-07 | Backup | Backup diário, retenção 30 dias, restore mensal | RPO ≤ 24 h, RTO ≤ 4 h; restore testado mensalmente com evidência | Runbook + teste |
| RNF-08 | Segurança | Derivado de RS-01 a RS-05 | TLS 1.3, HSTS, CSP, rate limit, hash Argon2id, sessão de 30 min, bloqueio de 5 tentativas | Teste de segurança |
| RNF-09 | Observabilidade | Derivado da arquitetura | 100% das requisições com trace ID; latência p95/p99 por rota; alerta de fila > 100 mensagens | Painel + alerta |
| RNF-10 | Manutenibilidade | Derivado da arquitetura | Cobertura ≥ 80% no back-end e ≥ 70% no portal; complexidade ciclomática ≤ 10 por função | CI |
| RNF-11 | Portabilidade | Derivado da arquitetura | Deploy em qualquer nuvem com Docker; nenhuma dependência de serviço proprietário no núcleo; PostgreSQL 17 padrão com dump/restore documentado, mesmo quando gerenciado no Supabase | Revisão de arquitetura |
| RNF-12 | Privacidade | LGPD | Nenhum dado pessoal em log de busca; retenção definida por finalidade; exclusão lógica com anonimização após 5 anos | Auditoria de dados |

### 5.1 Orçamento de desempenho por operação

| Operação | p50 | p95 | p99 | Carga de referência |
|---|---|---|---|---|
| Busca de serviços | 350 ms | 2,5 s | 3,0 s | 1.000 usuários simultâneos |
| Ficha do serviço | 300 ms | 2,0 s | 2,5 s | 1.000 usuários simultâneos |
| Listagem de slots | 200 ms | 1,0 s | 1,5 s | 300 usuários simultâneos |
| Criação de agendamento | 400 ms | 1,5 s | 2,0 s | 100 requisições/s |
| Geração de PDF | 2,0 s | 4,0 s | 5,0 s | 20 jobs/min |
| Login Gov.br (ida e volta) | 1,2 s | 2,5 s | 3,5 s | 50 requisições/s |

**Como ler:** o p95 é o compromisso com o cidadão; o p99 é o limite que dispara alerta. A meta de 3 s do RNF-04 é o p99, não a média. Uma média de 800 ms com p99 de 8 s significa que 1 em cada 100 cidadãos espera quase 10 segundos.

### 5.2 Disponibilidade e error budget

| Item | Valor |
|---|---|
| Janela de compromisso | Dias úteis, 08h–18h (horário de Brasília) |
| Disponibilidade alvo | 99,0% na janela |
| Indisponibilidade tolerada | ~2,2 h/mês na janela |
| Horário fora da janela | Melhor esforço; deploys permitidos |
| Definição de indisponibilidade | 5xx por mais de 1 minuto ou healthcheck falhando em 2 réplicas |
| Consumo do budget | > 50% em 7 dias congela features e prioriza confiabilidade |

---

## 6. Segurança e Privacidade

### 6.1 Requisitos de segurança

| ID | Perigo | Controle | Implementação | Verificação |
|---|---|---|---|---|
| RS-01 | Protocolo trocado entre cidadãos com nomes coincidentes | CPF como chave única; nunca buscar só por nome | `accountsCitizen.cpf` único; consultas de protocolo sempre por `citizenId` | Teste de autorização |
| RS-02 | Exposição de senha ou dados pessoais | Hash + salt, HTTPS, bloqueio de tentativas, acesso restrito a PCD | Argon2id; TLS 1.3; 5 tentativas/5 min; campo de deficiência com acesso restrito | Teste de segurança + revisão |
| RS-03 | Acesso indevido à gerência | Controle por perfil e log de quem/quando/o quê | RBAC + `auditEvent`; princípio do menor privilégio | Teste de autorização |
| RS-04 | Anexo malicioso | Validar formato e tamanho, antivírus, fora da raiz web | jpg/png/pdf ≤ 10 MB; ClamAV; S3 privado com URL assinada | Teste de upload |
| RS-05 | Perda de histórico | Exclusão lógica + backup diário | `deletedAt`, `isActive`, retenção de 5 anos, restore mensal | Teste de restore |

### 6.2 Matriz de tratamento LGPD

| Dado | Finalidade | Base legal | Retenção | Acesso | Compartilhamento |
|---|---|---|---|---|---|
| CPF | Identificação do cidadão e do protocolo | Execução de políticas públicas (art. 7º, II) | 5 anos após o último protocolo | Cidadão, servidor do protocolo, administrador | Órgão responsável pelo serviço |
| Nome, e-mail, celular | Comunicação e identificação | Execução de políticas públicas | 5 anos | Cidadão, servidor, administrador | Provedor de e-mail |
| Data de nascimento | Elegibilidade e prioridade legal | Execução de políticas públicas | 5 anos | Cidadão, servidor | — |
| PCD e deficiência | Atendimento preferencial | Cumprimento de obrigação legal (art. 7º, II) | 5 anos | Cidadão, servidor autorizado | Unidade de atendimento |
| Endereço | Direcionamento à unidade | Execução de políticas públicas | 5 anos | Cidadão, servidor | — |
| Protocolo e anexos | Prestação do serviço | Execução de políticas públicas | 5 anos | Cidadão, servidor do órgão | Órgão responsável |
| Log de busca | Melhoria do catálogo | Legítimo interesse (art. 7º, IX), com anonimização | 24 meses | Administrador e gestor | — |
| Auditoria | Segurança e accountability | Obrigação legal (art. 7º, II) | 5 anos | Administrador | Autoridade competente, se solicitado |
| Avaliação | Qualidade do serviço | Consentimento (art. 7º, I) | 5 anos | Cidadão, gestor | — |

**Regras de privacidade**

1. O log de busca nunca grava CPF, e-mail, IP completo ou qualquer identificador direto.
2. O campo "Qual deficiência" é dado sensível (art. 5º, II) e só é exibido a quem tem necessidade operacional.
3. A exclusão de conta é lógica; os protocolos permanecem pelo prazo legal, com o titular identificado apenas pelo necessário.
4. Pedidos de titular (acesso, correção, portabilidade) são registrados em `auditDataSubjectRequest` e respondidos em até 15 dias.
5. Nenhum dado pessoal é enviado a ferramentas de analytics de terceiros.

### 6.3 Modelo de ameaças (STRIDE)

| Ameaça | Cenário | Controle |
|---|---|---|
| Spoofing | Alguém se passa por outro cidadão | CPF + senha com hash Argon2id; bloqueio por tentativas; sessão assinada |
| Tampering | Alteração de um agendamento em trânsito | TLS + validação server-side + auditoria |
| Repudiation | Servidor nega ter cancelado um protocolo | `auditEvent` com ator, IP e antes/depois |
| Information disclosure | Acesso a protocolo de terceiro | Autorização por `citizenId`; 404 em vez de 403 |
| Denial of service | Enxurrada de buscas | Rate limit por IP e por sessão; cache; fila |
| Elevation of privilege | Servidor tenta acessar gestão de usuários | RBAC + testes de autorização por rota |

---

## 7. Matriz de Divergências

O protótipo no Figma foi construído antes do fechamento do texto dos requisitos. As divergências abaixo não são erros escondidos: são decisões pendentes com dono e critério de encerramento. A hierarquia aplicada é a do [Pilar 0](README.md#hierarquia-de-fontes-de-verdade).

**Artefatos visuais — declaração explícita**

| Artefato | Caminho ou referência | O que é | É o protótipo oficial? |
|---|---|---|---|
| Figma `SOSP` | 45 telas (30 mobile + 15 web) | Protótipo visual de referência | **Sim** |
| HTML `rf006_busca.html` e `rf006_ficha.html` | `Prototipo/` | Implementação navegável do recorte RF-06, usada para teste | Não — artefato técnico derivado |
| `DesignSystem/index.html` | `DesignSystem/` | Documentação viva de tokens e componentes | Não — catálogo do Design System |

O HTML do RF-06 e o Figma **não são o mesmo protótipo**. O primeiro é uma prova de implementação do recorte de busca e ficha; o segundo é a referência visual de todas as 45 telas. Quando os dois divergirem entre si, vale o Figma para aparência e o requisito para comportamento.

As nove primeiras divergências foram mapeadas na entrega do RF-06. As divergências D10 a D13 são sistêmicas: atravessam requisito, arquitetura e contrato técnico, e por isso não poderiam ficar restritas ao recorte de busca.

**Legenda de decisão:** 🎨 ajustar Figma · 📝 ajustar texto · ✅ aceitar com justificativa.

| ID | Ponto | O que diz o requisito | O que mostra o protótipo | Tela no Figma | Impacto | Decisão | Responsável | Encerrado quando |
|---|---|---|---|---|---|---|---|---|
| **D1** | Ações da ficha | Três botões: Ver Passo-a-Passo, Agendar e Avaliar | Web e mobile exibem "Iniciar solicitação" e um link secundário | 05, W03 | Alto — o cidadão não encontra o guia nem o agendamento a partir da ficha | 🎨 Ajustar o Figma | Design | Tela 05 com as três ações, sendo Avaliar condicionado ao RF-10 |
| **D2** | Paginação | 10 resultados por página | Web mostra "1–4 de 148"; mobile usa rolagem contínua | 04, W02 | Médio — o requisito é verificável e o protótipo não o demonstra | 🎨 Ajustar o Figma | Design + Front-end | Lista web com 10 cards e contador; mobile com "Carregar mais" em blocos de 10 |
| **D3** | Filtros | Categoria, Órgão, Canal e Município | Web: Categoria, Órgão e "Modalidade"; mobile: chips Online, Presencial, Gratuito, Acessível, Perto de mim | 04, 27, W02 | Alto — falta um filtro oficial e o vocabulário diverge | 🎨 Ajustar o Figma | Design | Município presente nos dois layouts e "Canal" no lugar de "Modalidade" |
| **D4** | Mapa na ficha | "Onde fazer (unidades e mapa)" | Endereço e "Ver outras unidades", sem mapa | 05, 22, W03 | Médio — perda de orientação geográfica | 🎨 Ajustar o Figma | Design + Front-end | Bloco de mapa renderiza quando há latitude/longitude (RN-10) |
| **D5** | Média de avaliações | RF-10 exibe média na ficha | Nenhuma ficha mostra média ou contagem | 05, W03 | Baixo no MVP (RF-10 fora do escopo); médio na v2.0 | ✅ Aceitar no MVP | Produto | Bloco de reputação entra junto com o RF-10 |
| **D6** | Gate de login | Agendar e avaliar exigem conta | O protótipo não sinaliza o login nem o retorno à ação; o modal do Gov.br (futuro) e o formulário de CPF + senha não estão representados | 01, 08, W05, W08 | Alto — o cidadão é surpreendido no meio do fluxo | 🎨 Ajustar o Figma | Design + Requisitos | Estado "entre para agendar" e retorno pós-login representados |
| **D7** | Elegibilidade do Avaliar | RF-06 prevê o botão, sem definir elegibilidade | O botão não existe | 05, W03 | Alto — ambigüidade de escopo entre RF-06 e RF-10 | 📝 Ajustar o texto | Requisitos | Botão só existe com RF-10 habilitado; exige protocolo concluído; desabilitado com explicação |
| **D8** | Canal do serviço | Canal é um valor único: online, presencial ou híbrido | Tag "Presencial" e metadado "Atendimento Presencial e online" na mesma tela | 05, W03 | Baixo — inconsistência de conteúdo | 🎨 Ajustar o Figma | Design | Tag e metadado derivados do mesmo campo |
| **D9** | Estado vazio | Mensagem literal "Nenhum serviço encontrado. Tente outro termo ou categoria." | Mobile exibe "Não encontrou o que procura? Tente outra palavra…" | 19, W02 | Baixo — texto divergente, mas há saída | 🎨 Ajustar o Figma | Design | Mensagem literal como título e texto de apoio como complemento |
| **D10** | Autenticação do cidadão | RF-01 e RF-02 descrevem cadastro com senha e login por CPF e senha | Arquitetura define Gov.br como provedor de identidade do cidadão | 01, 02, W08 | Alto — cadastro manual do cidadão substitui Gov.br como primário no MVP | 📝 Ajustar o texto | Requisitos + Arquitetura | RF-01 e RF-02 revisados: Gov.br para cidadão, CPF/senha para servidores |
| **D11** | Canal de notificação | RF-08 e RF-13 citam SMS | Arquitetura define e-mail transacional no MVP; push, SMS e WhatsApp na v2.0/Fase 3 | — (sem tela no MVP) | Médio — promessa de canal não entregue | ✅ Aceitar com justificativa | Produto | Texto do RF-08 e RF-13 alinhado ao MVP; push, SMS e WhatsApp no roadmap |
| **D12** | Requisito de hardware | RNF-03 fixa servidor 4 GHz/64 GB e cliente 2 GHz/4 GB | Arquitetura em contêineres elásticos, sem servidor dedicado | — (não é tela) | Baixo — requisito desatualizado tecnicamente | 📝 Ajustar o texto | Arquitetura | RNF-03 reescrito como capacidade de infraestrutura e requisito de cliente |
| **D13** | Relatório de avaliações no MVP | RF-14 inclui a média das avaliações | RF-10 é Desejável/Could e está fora do MVP | W15 | Médio — relatório promete dado que o MVP não coleta | ✅ Aceitar com justificativa | Produto | Painel de avaliações oculto por feature flag até o RF-10; os demais relatórios entregues no MVP |

**Regras da matriz**

1. Toda divergência tem um ID, um dono e um critério de encerramento verificável.
2. D1, D3, D6, D7 e D10 são bloqueantes para a apresentação: afetam o que o professor verá na demonstração.
3. Nenhuma imagem do protótipo é alterada neste documento. A fonte visual continua sendo o Figma.
4. Divergência encerrada não é apagada: muda para "Encerrada" com data e link para a evidência.

---

## 8. Rastreabilidade

### 8.1 Requisito → história → caso de uso → tela → endpoint → critério

| RF | User stories | UC | Telas | Endpoints principais | Critérios |
|---|---|---|---|---|---|
| RF-01 | US-13 | UC-01 | 01, 02, 14, 29, W08, W10 | `POST /citizens`, `PATCH /citizens/me`, `GET /cep/lookup` | CA-16 |
| RF-02 | US-14, US-15 | UC-02 | 01, 17, W08 | `POST /auth/login`, `POST /auth/logout`, `POST /auth/password-recovery`, `GET /auth/session` | CA-16 |
| RF-03 | US-16 | UC-03 | 21, W13 | `GET /agencies` + Django Admin | CA-17 |
| RF-04 | US-16 | UC-04 | 22, W13 | `GET /units` + Django Admin | CA-17 |
| RF-05 | US-17 | UC-05 | 28, W12 | `GET /services/{serviceId}` + Django Admin | CA-17 |
| RF-06 | US-01 a US-04 | UC-06, UC-07 | 03, 04, 05, 19, 22, 26, 27, W01, W02, W03 | `GET /services`, `GET /services/{serviceId}` | CA-01 a CA-10 |
| RF-07 | US-05 a US-07 | UC-08 | 06, 07, W04 | `PUT /services/{serviceId}/guidance/checklist`, `POST /services/{serviceId}/guidance/pdf` | CA-11, CA-15 |
| RF-08 | US-08 a US-10 | UC-09, UC-10 | 08, 09, 10, 24, 25, W05 | `GET /units/{unitId}/slots`, `POST /appointments` | CA-12, CA-13 |
| RF-09 | US-11, US-12 | UC-11, UC-12 | 10, 11, 12, 15, W06, W07 | `GET /protocols`, `GET /protocols/{protocolNumber}` | CA-14 |
| RF-10 | US-20 | UC-13 | 23 (v2.0) | `POST /protocols/{protocolNumber}/review` | CA-19 |
| RF-11 | US-21 | UC-14 | 13, W09 | `GET /services/{serviceId}/faq`, `POST /questions` | CA-20 |
| RF-12 | US-18 | UC-15 | W14 | Django Admin (sem rota pública) | CA-17 |
| RF-13 | — | UC-16 | — | `GET /notifications/preferences`, `PUT /notifications/preferences` | CA-21 |
| RF-14 | US-19 | UC-17 | W11, W15 | `GET /reports/appointments`, `POST /reports/exports` | CA-18 |

A numeração de tela segue o [índice de telas](design/README.md): `01`–`30` são mobile e `W01`–`W15` são web. O índice liga cada tela ao RF, ao UC, ao status e ao `node-id` do Figma; o `node-id` permanece `<preencher>` até a exportação oficial.

### 8.2 Requisito → RNF → RS

| RF | RNFs aplicáveis | RS aplicáveis |
|---|---|---|
| RF-01 | RNF-01, RNF-02, RNF-06 | RS-01, RS-02 |
| RF-02 | RNF-02, RNF-08 | RS-02, RS-03 |
| RF-03, RF-04, RF-05, RF-12 | RNF-01, RNF-09, RNF-10 | RS-03, RS-05 |
| RF-06 | RNF-04, RNF-05, RNF-06 | RS-01 |
| RF-07 | RNF-04, RNF-06 | RS-01, RS-04 |
| RF-08, RF-09 | RNF-04, RNF-05, RNF-08 | RS-01, RS-04 |
| RF-10, RF-11, RF-13 | RNF-02, RNF-06 | RS-02, RS-03 |
| RF-14 | RNF-04, RNF-09 | RS-03, RS-05 |

---

## 9. Definição de Pronto

Um requisito só é considerado pronto quando **todos** os itens abaixo são verdadeiros. A lista é binária: não existe "quase pronto".

| # | Critério | Evidência |
|---|---|---|
| 1 | Todos os critérios de aceite passam em ambiente de staging | Relatório de testes |
| 2 | Testes unitários, de integração e E2E verdes | Pipeline de CI |
| 3 | Cobertura ≥ 80% no back-end e ≥ 70% no portal | Relatório de cobertura |
| 4 | Nenhuma violação crítica de acessibilidade | axe-core + teste manual com teclado |
| 5 | Contrato OpenAPI atualizado e validado | `openapi-spec-validator` no CI |
| 6 | Migração reversível e testada | `migrate` + `rollback` em staging |
| 7 | Auditoria gravando ator, antes e depois | Teste de integração |
| 8 | Nenhum dado pessoal em log | Revisão de logs |
| 9 | Documentação do requisito atualizada | Este documento + changelog |
| 10 | Divergências do requisito encerradas ou aceitas formalmente | Matriz da seção 7 |
| 11 | Demonstração de 7 minutos ensaiada | [Roteiro da demo](demo-7-minutos.md) |
| 12 | Feature flag configurada e documentada | [ADR-007](adr/ADR-007-feature-flags.md) e [Pilar 5 §7](05-engineering-devops.md#7-configuração-e-segredos) |

---

## 10. Artefatos complementares

Este pilar define **o que** o sistema deve fazer. Os documentos abaixo aprofundam **como** o requisito vira comportamento, tela, contrato e operação. Em caso de conflito, vale a [hierarquia de fontes](README.md#hierarquia-de-fontes-de-verdade): requisito → ADR → contrato → implementação → Figma.

| Artefato | O que contém | Quando consultar |
|---|---|---|
| [Casos de uso — UC-01 a UC-17](use-cases/README.md) | Ator, pré-condições, gatilho, fluxo principal, alternativos, exceções, pós-condições, RN/CA e contrato de cada UC; diagrama e matriz de rastreabilidade | Ao implementar ou testar um fluxo completo |
| [Índice de telas — 45 telas](design/README.md) | 30 telas mobile e 15 web, com RF, UC, status e `node-id`; regras de nomenclatura e governança | Ao implementar, revisar ou exportar uma tela |
| [Exportações de design](design/exports/README.md) | Padrão de nome, pasta, checklist e registro das exportações oficiais | Antes de anexar imagens ao relatório ou à apresentação |
| [Gestão do projeto](06-project-management.md) | Stakeholders, escopo, cronograma, cerimônias, riscos, métricas e Definition of Ready | Ao planejar a sprint ou comunicar status |
| [Roteiro da demo de 7 minutos](demo-7-minutos.md) | Blocos cronometrados, checklist pré-demo, plano B e perguntas prováveis | Na véspera e no dia da apresentação |
| [Glossário](glossario.md) | Vocabulário de produto, requisitos, arquitetura, segurança, processo e banco | Quando um termo aparecer sem definição no texto |
| [ADRs](adr/) | Decisões arquiteturais com contexto, alternativas e consequências | Antes de propor mudança que contrarie uma decisão aceita |
| [Protótipo oficial — Figma `SOSP`](https://www.figma.com/design/P8Pf9aZiagXQulJpP2guqz/SOSP?node-id=0-1) | Aparência, hierarquia e conteúdo das 45 telas | Ao implementar a interface; acesso somente visualização |

**Relação com o protótipo HTML.** O arquivo `Prototipo/rf006_*.html` é uma prova de implementação do recorte de busca e ficha (RF-06), não o protótipo oficial. Quando ele divergir do Figma, vale o Figma para aparência e este pilar para comportamento. O `DesignSystem/index.html` é o catálogo vivo de tokens e componentes, não uma tela do produto.

---

**Próximo:** [Pilar 2 — Design e Experiência do Usuário](02-design-ux.md)
