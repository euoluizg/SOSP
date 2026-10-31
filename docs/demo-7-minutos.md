# Demonstração — Roteiro de 7 Minutos

> **Projeto:** SOSP — Sistema de Orientação para Serviços Públicos
> **Versão:** 1.1.0 · **Data:** 31/10/2026 · **Status:** Em revisão
> **Autores:** Equipe de Engenharia de Software — CESMAC
> **Documentos irmãos:** [Pilar 0](README.md) · [Pilar 1](01-product-specs.md) · [Pilar 2](02-design-ux.md) · [Pilar 3](03-architecture.md) · [Pilar 4](04-data-api.md) · [Pilar 5](05-engineering-devops.md)

---

## Sumário

1. [Objetivo da demonstração](#1-objetivo-da-demonstração)
2. [Mensagem central](#2-mensagem-central)
3. [Antes de começar](#3-antes-de-começar)
4. [Roteiro cronometrado](#4-roteiro-cronometrado)
5. [Plano B](#5-plano-b)
6. [O que não mostrar](#6-o-que-não-mostrar)
7. [Perguntas prováveis](#7-perguntas-prováveis)
8. [Depois da demo](#8-depois-da-demo)

---

## 1. Objetivo da demonstração

Em **7 minutos**, provar três coisas:

1. **O problema é real e a solução responde a ele.** O cidadão não sabe o nome do serviço; o SOSP traduz a necessidade em uma ficha com oito respostas.
2. **A jornada completa funciona.** Buscar → entender → seguir o guia → agendar → acompanhar o protocolo, sem intervenção manual e sem tela falsa.
3. **A engenharia sustenta a jornada.** Há contrato, banco, testes, CI, observabilidade e decisões registradas por trás do que aparece na tela.

A demo não é um tour por todas as telas. É uma **história com começo, meio e fim**, contada na perspectiva de uma pessoa.

**Público:** professor, avaliador e colegas. Assume conhecimento técnico, mas não conhecimento do domínio do SOSP.

**Duração:** 7 minutos de demo + 3 a 5 minutos de perguntas. O relógio é rígido: se a demo passar de 8 minutos, o encerramento é cortado, não a jornada.

---

## 2. Mensagem central

> **"O cidadão chega com uma necessidade, não com o nome do serviço. O SOSP entrega a orientação completa, o passo a passo e o protocolo — sem obrigar ninguém a adivinhar o vocabulário do governo."**

Toda fala da demo deve reforçar uma das quatro ideias:

| Ideia | Onde aparece |
|---|---|
| **Orientação antes de formulário** | Busca e ficha sem login |
| **Uma ficha, oito perguntas** | Bloco dos oito itens |
| **Rastro do começo ao fim** | Agendamento → protocolo → linha do tempo |
| **Engenharia verificável** | Contrato, testes, CI e ADRs no encerramento |

---

## 3. Antes de começar

### 3.1 Checklist de 30 minutos antes

| # | Item | Como verificar |
|---|---|---|
| 1 | Staging no ar | Abrir a home e fazer uma busca simples |
| 2 | Banco com massa de demonstração | Buscar "certidão" e confirmar que retorna serviço |
| 3 | Login CPF+senha funcional | Fazer login de teste com a conta de demonstração em janela anônima |
| 4 | Conta de demonstração com perfil completo | Conferir "Meus pedidos" |
| 5 | Conta de cidadão criada com CPF e senha | Login manual com CPF + senha na tela de autenticação |
| 6 | Agendamento de teste disponível | Conferir slots nos próximos 7 dias |
| 7 | PDF gera em até 5 s | Gerar um PDF de teste e abrir |
| 8 | E-mail transacional chega | Conferir caixa de teste (Mailpit ou conta dedicada) |
| 9 | Flags no estado da demo | `FEATURE_REVIEWS_ENABLED=false`, `FEATURE_PUSH_ENABLED=false`, `FEATURE_REPORTS_EXPORT=true` |
| 10 | Abas abertas na ordem | Home, busca, ficha, guia, agendamento, protocolo, back-office |
| 11 | Plano B aberto | Vídeo de 3 min ou capturas em `docs/design/exports/` |
| 12 | Cronômetro visível | Celular no modo cronômetro, virado para quem apresenta |
| 13 | Áudio e fonte | Testar compartilhamento de tela e zoom do navegador |

### 3.2 Dados da demonstração

| Elemento | Valor sugerido | Por quê |
|---|---|---|
| **Termo buscado** | `tirar rg` | Mostra a tradução de linguagem simples para o nome oficial |
| **Serviço** | Emitir Carteira de Identidade | Serviço conhecido, ficha rica e fácil de explicar |
| **Unidade** | Unidade de atendimento com endereço e horário | Permite mostrar mapa, quando houver coordenadas |
| **Cidadão** | Conta fictícia, perfil completo | Evita cadastro no meio da demo |
| **Protocolo** | Um agendamento criado na hora | Prova que o fluxo é real, não gravado |
| **Back-office** | Relatório de agendamentos do período | Mostra que o dado gerado na demo aparece na gestão |

**Regra de privacidade:** nenhum dado real de cidadão. A conta, o CPF e o e-mail são fictícios e declarados como tal.

### 3.3 Divisão de papéis

| Papel | Quem | O que faz |
|---|---|---|
| **Apresentador** | PO ou pessoa designada | Conduz a narrativa e o mouse |
| **Operador** | Back-end ou DevOps | Monitora logs, fila e saúde do ambiente; resolve imprevisto |
| **Apoio** | Design ou QA | Controla o tempo e aciona o plano B se necessário |

**Regra:** uma pessoa fala por vez. O operador não narra; ele age em silêncio se algo falhar.

---

## 4. Roteiro cronometrado

### 4.1 Visão geral

| Tempo | Bloco | Tela | Mensagem |
|---|---|---|---|
| 0:00–0:15 | Abertura | Home | O problema e a promessa |
| 0:15–0:30 | Login | Tela de login | Login CPF+senha; modal Gov.br v2.0 |
| 0:30–1:30 | Busca | 04 | Linguagem simples encontra o serviço |
| 1:30–3:00 | Ficha | 05 | As oito perguntas respondidas |
| 3:00–4:00 | Guia e PDF | 06, 07 | O que levar, sem esquecer nada |
| 4:00–5:30 | Agendamento | 08, 09, 10 | Horário real e protocolo |
| 5:30–6:30 | Acompanhamento | 10, 12 | Rastro e transparência |
| 6:30–7:00 | Encerramento | Back-office ou diagrama | Engenharia por trás |

---

### 4.2 Bloco 1 — Abertura (0:00–0:30)

**Tela:** home (`03` / `W01`).

**Fala sugerida:**

> "Boa tarde. O cidadão sabe que precisa tirar um documento, mas não sabe que o serviço se chama 'Emitir Carteira de Identidade', nem qual órgão procura, nem o que levar. Ele liga, vai ao balcão, volta. O SOSP é um ponto de entrada único: ele descreve a necessidade e recebe a orientação completa, o passo a passo e o protocolo."

**O que fazer:** abrir a home, sem clicar ainda. Deixar a busca visível.

**Não fazer:** explicar arquitetura, listar tecnologias ou mostrar slide.

---

### 4.3 Bloco 2 — Busca (0:30–1:30)

**Tela:** busca (`04` / `W02`).

**O que fazer:**

1. Digitar `tirar rg` e pressionar Enter.
2. Mostrar o resultado com o serviço "Emitir Carteira de Identidade".
3. Mostrar o total de resultados e a paginação de 10 itens.
4. Aplicar um filtro de canal ou município e mostrar que a URL preserva o estado.
5. Se houver tempo, mostrar o estado vazio com `xyz` e a mensagem literal + saída para a Ouvidoria.

**Fala sugerida:**

> "A busca normaliza acento e caixa, usa full-text e similaridade. 'Tirar rg' encontra 'Emitir Carteira de Identidade' porque o índice cobre nome, descrição, categoria, órgão e sinônimos. O resultado mostra órgão, canal, custo e prazo — o suficiente para o cidadão decidir se vale a pena."

**Evidência técnica (1 frase):** "São 10 itens por página, com total, e os filtros são combináveis por interseção."

---

### 4.4 Bloco 3 — Ficha (1:30–3:00)

**Tela:** ficha (`05` / `W03`).

**O que fazer:**

1. Abrir a ficha.
2. Percorrer os oito blocos, sem ler todos: **o que é**, **quem tem direito**, **o que levar**, **como fazer**, **onde**, **quando**, **quanto custa**, **quanto demora**.
3. Destacar documentos obrigatórios vs. opcionais.
4. Mostrar o alerta de atendimento preferencial, se a conta de demonstração for PCD ou 60+.
5. Mostrar o mapa, se a unidade tiver coordenadas.
6. Apontar as três ações: Ver passo a passo, Agendar e, se a flag estiver ligada, Avaliar (na demo, a flag está desligada).

**Fala sugerida:**

> "A ficha é montada exclusivamente com dados do catálogo e das unidades. Ela não inventa informação: se o dado não existe, o bloco não aparece. São as oito perguntas que o cidadão faria no balcão, na ordem em que ele perguntaria."

**Evidência técnica (1 frase):** "A ficha é pública; o login só aparece quando há efeito transacional — agendar ou anexar documento."

---

### 4.5 Bloco 4 — Guia e PDF (3:00–4:00)

**Tela:** guia (`06`) e checklist/PDF (`07`).

**O que fazer:**

1. Clicar em "Ver passo a passo".
2. Mostrar as etapas numeradas com tempo estimado.
3. Marcar dois documentos no checklist.
4. Gerar o PDF e abrir o arquivo.
5. Mostrar que o PDF tem nome, serviço, checklist e data/hora.

**Fala sugerida:**

> "O guia transforma a ficha em ação. O cidadão marca o que já separou, o progresso fica salvo por CPF e serviço, e o PDF leva o checklist para o atendimento. Se ele é PCD ou tem 60+, o alerta de prioridade aparece quando a unidade oferece o atendimento preferencial."

**Evidência técnica (1 frase):** "O PDF é gerado de forma assíncrona por um worker; o portal acompanha o job e não trava a navegação."

**Cuidado:** se o PDF demorar, não ficar olhando para a tela. Falar do fluxo assíncrono enquanto o job termina.

---

### 4.6 Bloco 5 — Agendamento (4:00–5:30)

**Tela:** agendamento (`08`, `09`, `10`).

**O que fazer:**

1. Clicar em "Agendar".
2. Se não estiver logado, mostrar o redirecionamento ao login CPF + senha e o retorno à ação. (Na demo, entrar já logado para economizar tempo.)
3. Escolher unidade e data.
4. Mostrar os slots de 30 minutos, com apenas horários livres.
5. Escolher um slot e confirmar.
6. Mostrar o protocolo `AAAAMMDD-XXXX` e o comprovante.
7. Se o e-mail chegar rápido, mostrar a caixa de entrada; se não, dizer que o envio é assíncrono e tem retry.

**Fala sugerida:**

> "O sistema calcula slots de 30 minutos dentro do horário da unidade, desconta feriado, dia sem atendimento e lotação. A confirmação é transacional: se dois cidadãos disputarem o mesmo horário, um recebe 409 e volta para a escolha. O protocolo é gerado com sequência diária e o comprovante fica disponível."

**Evidência técnica (1 frase):** "A criação usa `Idempotency-Key`; reenviar a mesma requisição não duplica o agendamento."

---

### 4.7 Bloco 6 — Acompanhamento (5:30–6:30)

**Tela:** protocolo (`10`, `12`).

**O que fazer:**

1. Abrir "Meus pedidos".
2. Mostrar o protocolo recém-criado com status "Recebido".
3. Abrir a linha do tempo com data, hora, responsável e observação.
4. Mostrar a próxima ação esperada.
5. Se houver tempo, mostrar o estado "Aguardando documento" e o botão de anexo (sem enviar arquivo, para não gastar tempo).

**Fala sugerida:**

> "Todo agendamento vira protocolo, todo protocolo tem linha do tempo e toda mudança de status é auditável. O cidadão não precisa ligar para a unidade para saber o que está acontecendo. Quando o servidor pede um documento, o cidadão anexa e o pedido volta para análise."

**Evidência técnica (1 frase):** "O cidadão só vê o próprio protocolo; acesso a protocolo de terceiro responde 404, não 403."

---

### 4.8 Bloco 7 — Encerramento (6:30–7:00)

**Tela:** back-office (`W11`/`W15`) ou diagrama C4 do [Pilar 3](03-architecture.md#3-c4-nível-2--containers).

**O que fazer:** mostrar por 15 segundos o relatório de agendamentos ou o diagrama de containers. Não navegar por várias telas.

**Fala sugerida:**

> "Por trás da jornada: Django e DRF na API, Next.js no portal, PostgreSQL 17 gerenciado no Supabase, Redis e workers para PDF e e-mail. O contrato OpenAPI é validado no CI, o schema tem migrações versionadas e as decisões estão em ADRs. O MVP entrega busca, ficha, guia, agendamento e protocolo; avaliação e push ficam para a v2.0, atrás de feature flags."

**Frase de fechamento:**

> "O SOSP não substitui o órgão: ele traduz a necessidade do cidadão em um próximo passo concreto. Obrigado."

---

## 5. Plano B

### 5.1 Matriz de falhas

| Falha | Sinal | Ação imediata | O que dizer |
|---|---|---|---|
| **Gov.br indisponível** | Redirecionamento falha ou callback dá erro | Usar conta de demonstração já autenticada ou login local de servidor para o back-office | "No MVP, o login é local (CPF + senha). O Gov.br está preparado como v2.0; para a demo, uso uma sessão já preparada." |
| **Internet instável** | Busca ou ficha não carrega | Trocar para o vídeo de 3 minutos ou para as capturas em `docs/design/exports/` | "Vou mostrar a gravação do fluxo enquanto a conexão se recupera." |
| **PDF não gera** | Job pendente ou erro | Mostrar um PDF gerado anteriormente; seguir para o agendamento | "A geração é assíncrona; este é o PDF de uma execução anterior, com o mesmo conteúdo." |
| **E-mail não chega** | Caixa vazia | Mostrar o log de envio ou a fila; não esperar | "O envio é assíncrono, com retry; o agendamento já está confirmado." |
| **Slot lota** | 409 ao confirmar | Escolher outro horário e explicar a regra | "É exatamente o comportamento esperado: o sistema não vende o mesmo horário duas vezes." |
| **Ambiente fora do ar** | 5xx ou timeout | Ir direto para o vídeo e para o diagrama | "O ambiente de staging está indisponível; vou mostrar a jornada gravada e a arquitetura." |
| **Back-office lento** | Relatório não carrega | Mostrar o diagrama C4 e os ADRs | "O relatório consulta dados agregados; a arquitetura está documentada no Pilar 3." |

### 5.2 Vídeo de contingência

Gravar um vídeo de **3 minutos** com a jornada completa, sem narração de tela, apenas com o fluxo:

1. Busca `tirar rg`.
2. Ficha.
3. Guia e PDF.
4. Agendamento.
5. Protocolo.

**Regras:** gravar em staging, com a mesma massa da demo, resolução 1080p, sem dados pessoais. Guardar em `docs/design/exports/` ou em link privado. Testar o áudio antes.

### 5.3 Frase de transição para o plano B

> "Se a rede falhar, eu tenho a gravação do fluxo e as capturas do protótipo. O que importa é o comportamento, não a coincidência de a rede estar boa."

---

## 6. O que não mostrar

| Não mostrar | Por quê |
|---|---|
| Tela de avaliação (23) | RF-10 está fora do MVP; a flag está desligada |
| Preferências de push | RF-13 está fora do MVP |
| Django Admin cru, com tabelas técnicas | Confunde o avaliador e expõe detalhe irrelevante |
| Logs com stack trace | Passa impressão de instabilidade |
| Telas em construção | "Pendente" não é demo |
| Slides antes da tela | A demo é software rodando; slide é apoio |
| Métricas inventadas | Use as metas dos RNFs, não números fabricados |
| Dados reais de cidadão | Viola LGPD e destrói a credibilidade |

---

## 7. Perguntas prováveis

| Pergunta | Resposta curta | Onde aprofundar |
|---|---|---|
| **"Por que não usam o Gov.br?"** | A API oficial exige credenciamento institucional que não temos no momento. Optamos por cadastro manual com CPF + senha (Argon2id) e mantivemos o botão na interface para demonstrar a visão de produto. A integração é v2.0. | [ADR-003](adr/ADR-003-autenticacao-govbr-rbac.md) |
| **"Como garantem a segurança da senha?"** | Argon2id com salt individual, sessão de 30 minutos, bloqueio após 5 tentativas e recuperação por código de 6 dígitos. | [Pilar 1 RF-02](01-product-specs.md#rf-02--autenticação-e-recuperação-de-acesso) |
| **"Como garantem que a informação está correta?"** | O catálogo é versionado, a ficha só publica com os oito blocos e toda alteração tem auditoria. | [Pilar 1 RF-05](01-product-specs.md#rf-05--gerenciar-catálogo-de-serviços) |
| **"E se o órgão não atualizar?"** | O serviço tem data de atualização visível e o administrador pode despublicar; a ficha não inventa dado. | [Pilar 4](04-data-api.md) |
| **"Por que Django e Next.js?"** | Monolito modular: uma API, um portal, um banco; menos peças móveis para um time pequeno. | [ADR-001](adr/ADR-001-monolito-modular-django-nextjs.md) |
| **"Por que Supabase?"** | PostgreSQL gerenciado em São Paulo; Auth, Data API e Realtime desabilitados; Django é a única porta de escrita. | [ADR-008](adr/ADR-008-supabase-postgresql-gerenciado.md) |
| **"Como escalam a busca?"** | Full-text + `pg_trgm`, índice dedicado, cache e teste de carga com 1.000 usuários. | [Pilar 3 §6](03-architecture.md#6-estratégia-de-escalabilidade) |
| **"O que acontece se o worker cair?"** | Retry com backoff e DLQ; o job não se perde e a fila é monitorada. | [ADR-005](adr/ADR-005-processamento-assincrono-dlq.md) |
| **"Como testam acessibilidade?"** | axe-core no CI, teste de teclado e leitor de tela; 0 violações críticas é gate de release. | [Pilar 2 §7](02-design-ux.md#7-acessibilidade) |
| **"O que fica para a v2.0?"** | Avaliação, push/SMS/WhatsApp e relatórios de avaliação; tudo atrás de flag. | [Pilar 1 §1.5](01-product-specs.md#15-mvp--roadmap-v20) |
| **"Por que Git Flow e não trunk-based?"** | Time pequeno, releases acadêmicas e necessidade de staging estável; `main` e `develop` com branches curtas por área. | [ADR-004](adr/ADR-004-git-flow-simplificado.md) |
| **"Qual a maior fragilidade?"** | Dependência da qualidade do catálogo e da estabilidade do ambiente; ambas têm mitigação e plano B. | [Pilar 6 §9](06-project-management.md#9-riscos) |

**Regra para perguntas:** responder em até 30 segundos. Se a resposta exigir mais, dizer "posso detalhar depois" e apontar o documento. Não improvisar número que não está na documentação.

---

## 8. Depois da demo

### 8.1 Checklist imediato

- [ ] Confirmar que o protocolo criado na demo não ficou em estado inconsistente.
- [ ] Remover a conta e o agendamento de demonstração, se forem descartáveis.
- [ ] Registrar a data, a versão e o resultado da demo no [CHANGELOG](CHANGELOG.md).
- [ ] Guardar as evidências (capturas, vídeo, logs) em `docs/design/exports/` ou no repositório.
- [ ] Anotar as perguntas que não foram respondidas com segurança.
- [ ] Atualizar o [Pilar 6 §9](06-project-management.md#9-riscos) se algum risco se materializou.

### 8.2 Avaliação da demo

| Critério | Pergunta | Nota (1–5) |
|---|---|---|
| Clareza | A história ficou clara em 30 segundos? | |
| Completude | A jornada foi do problema ao protocolo? | |
| Veracidade | Tudo que apareceu na tela era real? | |
| Tempo | Coube em 7 minutos? | |
| Engenharia | A explicação técnica sustentou a demo? | |
| Plano B | Alguma falha foi tratada sem quebrar a narrativa? | |

**Regra:** a nota não é vaidade. O que ficou abaixo de 4 vira ação concreta para a próxima apresentação.

---

*Roteiro derivado do [Pilar 1](01-product-specs.md) e do [Pilar 6](06-project-management.md). A demo prova o MVP; não promete a v2.0.*
