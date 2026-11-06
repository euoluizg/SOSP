# SOSP — Sistema de Orientação para Serviços Públicos
## Avaliação Final (3AF) — Disciplina de Banco de Dados
### Critério: Criação de Contas e Permissões para Acessar a Estrutura (1,0 Ponto)

---

- **Instituição:** Centro Universitário Cesmac (CESMAC)
- **Curso:** Bacharelado em Engenharia de Software
- **Disciplina:** Banco de Dados
- **Data Limite de Avaliação:** 27 de novembro de 2026
- **Equipe Oficial do Projeto:**
  - **Product Owner (PO):** Mozart Melo
  - **Tech Lead, Back-end (`Django 5 + DRF`) e DevOps:** Arthur Franco
  - **Front-end (`Next.js 15`), UI/UX Design e QA:** Luiz Gustavo
- **Repositório:** `euoluizg/SOSP` (Branch: `develop` / Feature: `feature/postgresql-roles-permissions`)

---

## 1. Objetivo Acadêmico e Escopo da Entrega

O presente documento e os scripts SQL que o acompanham atendem formalmente ao critério avaliativo da **3AF — Disciplina de Banco de Dados**:

> **"Criação de Contas e Permissões para acessar a estrutura" — Valor: 1,0 ponto.**

O objetivo central é demonstrar a implementação de uma camada de **Governança, Controle de Acesso Baseado em Papéis (RBAC - Role-Based Access Control)** e **Segurança em Nível de Linha (RLS - Row-Level Security)** no Sistema Gerenciador de Banco de Dados relacional **PostgreSQL 17 / 18**.

Esta camada foi projetada e validada de forma antecipada e desacoplada do Django ORM, garantindo:
1. **Segregação Estrita de Funções:** Princípio do Menor Privilégio (*Principle of Least Privilege — PoLP*);
2. **Defesa em Profundidade (*Defense in Depth*):** Bloqueio de DDL, bloqueio de `DELETE` físico em tabelas de negócio (em conformidade com `RN-40` e `RS-05`) e isolamento de dados sensíveis;
3. **Compatibilidade Futura:** Total harmonia com as roles internas do Supabase (`postgres`, `service_role`, `authenticated`, `anon`) e com a futura conexão do Django ORM.

---

## 2. Arquitetura de Contas e Roles PostgreSQL

A arquitetura adota a boa prática de separar **Papéis de Grupo (*Group Roles / NOLOGIN*)** de **Contas de Usuário (*User Accounts / LOGIN*)**. Usuários nunca recebem privilégios diretamente nos objetos; em vez disso, herdam permissões ao pertencerem a uma Role de Grupo.

```
                           +---------------------------+
                           |       SCHEMA PUBLIC       |
                           |  (Revogado CREATE/ALL     |
                           |      de PUBLIC)           |
                           +-------------+-------------+
                                         |
                 +-----------------------+-----------------------+
                 |                                               |
                 v                                               v
     +-----------------------+                       +-----------------------+
     |   sosp_leitor_role    |                       |  sosp_operador_role   |
     |       (NOLOGIN)       |                       |       (NOLOGIN)       |
     |-----------------------|                       |-----------------------|
     | - SELECT em Catálogo  |                       | - Herda SELECT        |
     | - SELECT em Views     |                       | - INSERT/SELECT logs  |
     | - Bloqueio de Escrita |                       | - INSERT/UPDATE FAQ   |
     | - RLS: apenas ativos  |                       | - Bloqueio de DELETE  |
     +-----------+-----------+                       +-----------+-----------+
                 ^                                               ^
                 | (Membro / INHERIT)                            | (Membro / INHERIT)
     +-----------+-----------+                       +-----------+-----------+
     |    sosp_leitor_3af    |                       |   sosp_operador_3af   |
     |        (LOGIN)        |                       |        (LOGIN)        |
     |  Conta de Demonstração|                       |  Conta de Demonstração|
     +-----------------------+                       +-----------------------+
```

### 2.1. Papéis de Grupo (Group Roles — `NOLOGIN`)

1. **`sosp_leitor_role`:**
   - **Propósito:** Papel de consulta pública e orientação ao cidadão.
   - **Privilégios:** Acesso somente leitura (`SELECT`) às tabelas do catálogo de serviços públicos e às views analíticas públicas.
   - **Restrições:** Proibição irrestrita de qualquer operação de escrita (`INSERT`, `UPDATE`, `DELETE`) e de qualquer comando DDL.
2. **`sosp_operador_role`:**
   - **Propósito:** Papel operacional de suporte e atendimento aos serviços públicos.
   - **Privilégios:** Herda todos os acessos de consulta de `sosp_leitor_role`; possui permissão controlada para registrar telemetria de buscas (`searchQueryLog`) e gerenciar conteúdo informativo de perguntas frequentes (`catalogFaq`) e sinônimos (`searchSynonym`).
   - **Restrições:** Proibição de exclusão física (`DELETE`) em qualquer tabela; proibição total de leitura ou escrita em tabelas de autenticação, sessões, dados sensíveis do cidadão (`accountsCitizen`) e logs imutáveis de auditoria (`auditEvent`).

### 2.2. Contas de Demonstração (User Accounts — `LOGIN`)

Para fins de demonstração acadêmica e validação automatizada, foram criadas duas contas associadas:
- **`sosp_leitor_3af`:** Usuário com login pertencente ao papel `sosp_leitor_role`.
- **`sosp_operador_3af`:** Usuário com login pertencente ao papel `sosp_operador_role`.

> [!IMPORTANT]
> **Segurança de Credenciais:** As senhas dos scripts acadêmicos utilizam placeholders controlados. Nenhuma senha real ou de ambiente de produção é armazenada em código-fonte versionado.

---

## 3. Matriz Completa de Privilégios (GRANT e REVOKE)

### 3.1. Revogação de Acessos Padrão (Hardening Inicial)

Por padrão, o PostgreSQL concede acesso de criação no schema `public` à role pública `PUBLIC`. A primeira medida de segurança executada é o fechamento completo desse vetor de vulnerabilidade:

```sql
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
```

### 3.2. Matriz de Acesso aos Objetos do SOSP

A tabela a seguir consolida a matriz de privilégios aplicada às 36 tabelas de aplicação e views do SOSP:

| Domínio / Tabela | Objeto | `sosp_leitor_role` | `sosp_operador_role` | Justificativa de Segurança |
| :--- | :--- | :---: | :---: | :--- |
| **Catálogo** | `catalogAgency` | `SELECT` | `SELECT` | Dados cadastrais públicos de órgãos |
| **Catálogo** | `catalogUnit` | `SELECT` | `SELECT` | Unidades de atendimento presenciais |
| **Catálogo** | `catalogService` | `SELECT` | `SELECT` | Fichas orientativas de serviços |
| **Catálogo** | `catalogUnitOpeningHour` | `SELECT` | `SELECT` | Horários de funcionamento das unidades |
| **Catálogo** | `catalogNonWorkingDay` | `SELECT` | `SELECT` | Feriados e pontos facultativos |
| **Catálogo** | `catalogServiceAgency` | `SELECT` | `SELECT` | Associação de órgãos responsáveis |
| **Catálogo** | `catalogUnitService` | `SELECT` | `SELECT` | Disponibilidade do serviço na unidade |
| **Catálogo** | `catalogServiceStep` | `SELECT` | `SELECT` | Etapas do guia passo a passo |
| **Catálogo** | `catalogServiceDocument` | `SELECT` | `SELECT` | Relação de documentos obrigatórios |
| **Catálogo** | `catalogServiceVersion` | `SELECT` | `SELECT` | Histórico versionado de fichas |
| **Catálogo** | `catalogFaq` | `SELECT` | `SELECT`, `INSERT`, `UPDATE` | Operador gerencia dúvidas frequentes |
| **Busca** | `searchQueryLog` | **NEGADO** | `SELECT`, `INSERT` | Registro anônimo de termos buscados |
| **Busca** | `searchSynonym` | `SELECT` | `SELECT`, `INSERT`, `UPDATE` | Dicionário de termos sinônimos |
| **Views** | `vw_public_services` | `SELECT` | `SELECT` | View consolidada de serviços públicos |
| **Views** | `vw_agency_stats` | `SELECT` | `SELECT` | View agregada de órgãos e unidades |
| **Contas** | `accountsCitizen` | **NEGADO** | **NEGADO** | Dados pessoais e LGPD (`RS-01`) |
| **Contas** | `accountsCitizenSession`| **NEGADO** | **NEGADO** | Tokens e sessões ativas |
| **Contas** | `accountsInternalUser`  | **NEGADO** | **NEGADO** | Usuários servidores e administradores |
| **Contas** | `accountsPasswordReset` | **NEGADO** | **NEGADO** | Tokens temporários de recuperação |
| **Agendamento**| `schedulingAppointment`| **NEGADO** | **NEGADO** | Agendamentos presenciais do cidadão |
| **Agendamento**| `schedulingProtocol`   | **NEGADO** | **NEGADO** | Protocolos `AAAAMMDD-XXXX` |
| **Agendamento**| `schedulingslot`       | **NEGADO** | **NEGADO** | Gestão de capacidade de vagas |
| **Auditoria**  | `auditEvent`           | **NEGADO** | **NEGADO** | Trilha imutável de auditoria (`RN-39`)|
| **Auditoria**  | `auditDataSubjectRequest`| **NEGADO**| **NEGADO** | Solicitações de direitos LGPD |
| **Global** | `CREATE TABLE / DDL` | **NEGADO** | **NEGADO** | Imutabilidade estrutural do schema |
| **Global** | `DELETE` em qualquer tabela | **NEGADO** | **NEGADO** | Exclusão lógica obrigatória (`RN-40`)|

---

## 4. Políticas de Segurança em Nível de Linha (Row-Level Security — RLS)

### 4.1. Fundamentação Teórica de RLS

O **Row-Level Security (RLS)** é um recurso nativo do PostgreSQL (a partir da versão 9.5) que estende o modelo de controle de acesso discricionário tradicional. Enquanto privilégios concedidos via `GRANT` controlam o acesso a **tabelas inteiras ou colunas**, o RLS determina **quais linhas específicas** de uma tabela podem ser selecionadas, inseridas, atualizadas ou excluídas por determinado papel ou usuário.

No SOSP, todas as 36 tabelas já possuem RLS habilitado por padrão no arquivo `docs/database/schema.sql`:
```sql
ALTER TABLE catalogService ENABLE ROW LEVEL SECURITY;
```
Quando o RLS está habilitado e nenhuma política foi criada, o PostgreSQL adota o princípio de **Default Deny** para usuários que não sejam proprietários da tabela (*table owner*) nem possuam o atributo `BYPASSRLS`.

### 4.2. Políticas Implementadas para a Demonstração (`rls_policies_3af.sql`)

Para demonstrar o funcionamento pleno do RLS na 3AF, foram implementadas políticas de isolamento sem enfraquecer o isolamento das tabelas protegidas:

1. **Filtro de Serviços Ativos para o Leitor (`catalogService`):**
   - Garante que cidadãos e leitores públicos apenas visualizem serviços homologados e ativos (`isActive = TRUE AND deletedAt IS NULL`).
   - Serviços em rascunho (*draft*) ou desativados são filtrados automaticamente pelo banco de dados:
     ```sql
     CREATE POLICY p_catalogService_reader_select ON catalogService
         FOR SELECT TO sosp_leitor_role
         USING (isActive = TRUE AND deletedAt IS NULL);
     ```
2. **Visualização de Rascunhos para o Operador (`catalogService`):**
   - Permite que operadores de suporte visualizem serviços mesmo em fase de homologação/rascunho, desde que não estejam excluídos logicamente:
     ```sql
     CREATE POLICY p_catalogService_operator_select ON catalogService
         FOR SELECT TO sosp_operador_role
         USING (deletedAt IS NULL);
     ```
3. **Validação de Integridade na Inserção com `WITH CHECK` (`catalogFaq`):**
   - O operador tem permissão para cadastrar novas dúvidas frequentes, mas a política RLS rejeita no nível de linha qualquer pergunta com menos de 5 caracteres:
     ```sql
     CREATE POLICY p_catalogFaq_operator_insert ON catalogFaq
         FOR INSERT TO sosp_operador_role
         WITH CHECK (length(trim(question)) >= 5);
     ```
4. **Validação de Registro de Busca com `WITH CHECK` (`searchQueryLog`):**
   - Garante que nenhuma inserção nula ou em branco de termo de pesquisa seja gravada na telemetria:
     ```sql
     CREATE POLICY p_searchQueryLog_operator_insert ON searchQueryLog
         FOR INSERT TO sosp_operador_role
         WITH CHECK (queryText IS NOT NULL AND length(trim(queryText)) > 0);
     ```

---

## 5. Resultados e Evidências dos Testes Automatizados

A suíte automatizada `docs/database/tests/test_roles_permissions.sql` foi executada em instância isolada do PostgreSQL 18.6, simulando com precisão o comportamento em ambiente de homologação. Todos os cenários foram testados e validados com 100% de sucesso.

### 5.1. Resumo dos Cenários de Teste

| Cenário | Operação Testada | Papel Executante | Resultado Esperado | Resultado Obtido | Status |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **A** | `SELECT` em `catalogAgency` | `sosp_leitor_3af` | Autorizado com sucesso | 1 linha retornada (SESAU) | **APROVADO** |
| **B** | `INSERT` em `catalogService` | `sosp_leitor_3af` | Negado (`insufficient_privilege`) | Erro capturado e tratado | **APROVADO** |
| **C** | `UPDATE` em `catalogAgency` | `sosp_leitor_3af` | Negado (`insufficient_privilege`) | Erro capturado e tratado | **APROVADO** |
| **D.1**| `INSERT` em `searchQueryLog` | `sosp_operador_3af` | Inserção autorizada | Registro gravado com sucesso | **APROVADO** |
| **D.2**| `SELECT` em `searchQueryLog` | `sosp_operador_3af` | Leitura autorizada | Termo recuperado com sucesso | **APROVADO** |
| **D.3**| `INSERT` e `UPDATE` em `catalogFaq`| `sosp_operador_3af` | Operações autorizadas | FAQ criada e atualizada | **APROVADO** |
| **E.1**| `SELECT` em `accountsCitizen` | `sosp_leitor_3af` | Negado (`insufficient_privilege`) | Acesso a dados pessoais barrado | **APROVADO** |
| **E.2**| `SELECT` em `accountsCitizen` | `sosp_operador_3af` | Negado (`insufficient_privilege`) | Acesso a dados pessoais barrado | **APROVADO** |
| **E.3**| `SELECT` em `auditEvent` | `sosp_operador_3af` | Negado (`insufficient_privilege`) | Acesso a auditoria barrado | **APROVADO** |
| **E.4**| `DELETE` em `catalogFaq` | `sosp_operador_3af` | Negado (`insufficient_privilege`) | Exclusão física impedida | **APROVADO** |
| **F.1**| `CREATE TABLE` no schema public | `sosp_leitor_3af` | Negado (`schema permission denied`) | DDL barrado para leitor | **APROVADO** |
| **F.2**| `CREATE TABLE` no schema public | `sosp_operador_3af` | Negado (`schema permission denied`) | DDL barrado para operador | **APROVADO** |
| **G.1**| RLS SELECT em `catalogService` | `sosp_leitor_3af` | Retorna apenas ativos (0 drafts) | 1 serviço ativo retornado | **APROVADO** |
| **G.2**| RLS `WITH CHECK` em `catalogFaq` | `sosp_operador_3af` | Rejeitar pergunta curta (< 5 car.) | `row violates RLS policy` | **APROVADO** |

### 5.2. Log Real de Execução no PostgreSQL

Abaixo transcreve-se o trecho verificado da execução no banco de testes:

```text
----------------------------------------------------------------------
FASE 1: TESTES COM PAPEL LEITOR (sosp_leitor_3af)
----------------------------------------------------------------------
  usuario_atual  | usuario_sessao 
-----------------+----------------
 sosp_leitor_3af | postgres

>>> [CENÁRIO A] Leitura permitida em catalogAgency:
 acronym |        name         | sphere 
---------+---------------------+--------
 SESAU   | Secretaria de Saude | state
(1 row)

>>> [CENÁRIO G.1] RLS em catalogService (esperado: apenas 1 servico ativo, 0 drafts):
                  id                  |         name          | status 
--------------------------------------+-----------------------+--------
 55555555-5555-5555-5555-555555555551 | Emissao de Cartao SUS | active
(1 row)

>>> [CENÁRIO B] Tentativa de INSERT em catalogService (esperado: permission denied):
NOTICE:  SUCESSO: Insercao bloqueada por permissao insuficiente: permission denied for table catalogservice

>>> [CENÁRIO C] Tentativa de UPDATE em catalogAgency (esperado: permission denied):
NOTICE:  SUCESSO: Atualizacao bloqueada por permissao insuficiente: permission denied for table catalogagency

>>> [CENÁRIO E.1] Tentativa de leitura de dados pessoais em accountsCitizen (esperado: permission denied):
NOTICE:  SUCESSO: Consulta a dados pessoais bloqueada por permissao insuficiente: permission denied for table accountscitizen

>>> [CENÁRIO F.1] Tentativa de CREATE TABLE como leitor (esperado: permission denied for schema public):
NOTICE:  SUCESSO: Criacao de tabela bloqueada por permissao insuficiente no schema: permission denied for schema public

----------------------------------------------------------------------
FASE 2: TESTES COM PAPEL OPERADOR (sosp_operador_3af)
----------------------------------------------------------------------
   usuario_atual   | usuario_sessao 
-------------------+----------------
 sosp_operador_3af | postgres

>>> [CENÁRIO D.1] INSERT autorizado em searchQueryLog:
INSERT 0 1

>>> [CENÁRIO D.2] SELECT autorizado em searchQueryLog:
         term          | resultcount 
-----------------------+-------------
 emissao de identidade |           5
(1 row)

>>> [CENÁRIO D.3] INSERT e UPDATE autorizados em catalogFaq:
INSERT 0 1
UPDATE 1

>>> [CENÁRIO E.2] Tentativa de leitura em accountsCitizen (esperado: permission denied):
NOTICE:  SUCESSO: Leitura de dados pessoais bloqueada para o operador: permission denied for table accountscitizen

>>> [CENÁRIO E.3] Tentativa de leitura em auditEvent (esperado: permission denied):
NOTICE:  SUCESSO: Leitura da trilha de auditoria bloqueada para o operador: permission denied for table auditevent

>>> [CENÁRIO E.4] Tentativa de DELETE em catalogFaq (esperado: permission denied):
NOTICE:  SUCESSO: Exclusao fisica bloqueada para o operador: permission denied for table catalogfaq

>>> [CENÁRIO F.2] Tentativa de CREATE TABLE como operador (esperado: permission denied):
NOTICE:  SUCESSO: DDL bloqueado para o operador por permissao insuficiente: permission denied for schema public

>>> [CENÁRIO G.2] Tentativa de INSERT em catalogFaq violando regra WITH CHECK do RLS:
NOTICE:  SUCESSO: Insercao invalida bloqueada pela politica RLS (WITH CHECK): new row violates row-level security policy for table "catalogfaq"

======================================================================
TODOS OS CENÁRIOS DE TESTE (A até G) FORAM CONCLUÍDOS COM SUCESSO!
======================================================================
```

---

## 6. Cuidados de Segurança: Demonstração Acadêmica vs. Produção

Para a apresentação acadêmica e garantia de integridade institucional, destacam-se os cuidados operacionais adotados:

### 6.1. O que é demonstrado academicamente:
- A hierarquia de permissões SQL (`GRANT` / `REVOKE`) estruturada e declarativa.
- A técnica de impersonação controlada com `SET ROLE` para comprovar alternância de privilégios.
- O isolamento dinâmico promovido por cláusulas `USING` e `WITH CHECK` no RLS.
- O tratamento de exceções em blocos PL/pgSQL capturando erros de privilégio insuficiente (`INSUFFICIENT_PRIVILEGE`).

### 6.2. O que NÃO deve ser executado em ambiente produtivo:
- **Senhas em Scripts Versionados:** Senhas jamais devem constar em repositório Git. Em produção, a criação de credenciais ocorre via cofres de segredos (*secret managers*) ou ferramentas de provisionamento (Supabase Vault, AWS Secrets Manager).
- **Contas Genéricas Compartilhadas:** Usuários reais devem possuir contas individuais vinculadas à respectiva lotação e CPF, integradas ao mecanismo de autenticação institucional do SOSP.
- **Bypass de RLS:** Jamais conceder a flag `BYPASSRLS` ou privilégios de `SUPERUSER` a papéis de aplicação externa ou usuários finais.

---

## 7. Compatibilidade com Supabase e Django ORM

### 7.1. Compatibilidade com Supabase
O Supabase administra seu cluster PostgreSQL por meio de papéis pré-definidos (`postgres`, `service_role`, `authenticated`, `anon`). A solução implementada em `roles_permissions.sql` respeita integralmente essa infraestrutura:
- Não sobrescreve, não altera e não revoga acessos das roles nativas do Supabase.
- Atua exclusivamente no schema `public`, sem interferir nos schemas gerenciados `auth`, `storage`, `realtime` e `vault`.
- Os papéis criados podem, caso desejado futuramente, herdar de `anon` ou `authenticated` para integração direta com a API PostgREST do Supabase.

### 7.2. Compatibilidade com o Django ORM
No monólito modular do SOSP (`ADR-001`):
- O backend Django conecta ao banco por meio de uma credencial administrativa de aplicação dedicada (ex.: `postgres` ou `sosp_django_app`), mantendo plena capacidade de executar migrações de schema gerenciadas pelo Django ORM.
- Como o Django 5 realiza o controle de autorização (RBAC) na camada de serviços (`services.py` e `selectors.py`), as políticas de RLS no banco de dados atuam como uma segunda barreira defensiva (*Defense in Depth*), sem gerar conflitos ou deadlocks transacionais.

---

## 8. Registro de Uso de Ferramentas de Inteligência Artificial

Em consonância com as normas de integridade acadêmica e transparência técnica, registra-se a utilização de ferramentas de Inteligência Artificial generativa no suporte ao desenvolvimento deste módulo.

- **Ambiente de Desenvolvimento:** Google DeepMind Antigravity IDE (Advanced Agentic Coding).
- **Modelos de Linguagem Empregados:**
  - **Claude 3.5 / 3.7 Sonnet (Anthropic)** e **Gemini 2.5 / Pro (Google DeepMind)** operando na coordenação multiagente e formulação de arquitetura de banco de dados e segurança.
- **Papel da IA:** Assistência na geração da matriz de privilégios, sintaxe declarativa de RLS PostgreSQL, scripts de teste de regressão em PL/pgSQL e formatação do relatório técnico.
- **Supervisão Humana:** Todas as diretrizes arquiteturais, restrições de segurança e validações foram definidas, supervisionadas e homologadas pelos integrantes da equipe.

### 8.1. Preservação do Prompt Mestre Utilizado

Abaixo é preservado na íntegra o prompt que orientou a concepção e implementação desta entrega:

```text
# PROMPT MESTRE — CRIAÇÃO DE CONTAS, ROLES E PERMISSÕES POSTGRESQL — SOSP / 3AF

## 1. MISSÃO
Atue como DBA PostgreSQL Sênior, Arquiteto de Segurança de Banco de Dados, Especialista em Supabase e Coordenador Multiagente.
Sua missão é implementar e documentar o gerenciamento de contas, roles, privilégios e permissões SQL do banco de dados SOSP.
Essa implementação deverá atender ao critério acadêmico da 3AF:
"Criação de Contas e Permissões para acessar a estrutura" — 1 ponto.
A implementação deverá ocorrer antes da preparação definitiva do Django ORM, sem depender de models ou migrations Django.
O banco PostgreSQL do Supabase já foi provisionado em São Paulo, porém a conexão ainda não foi realizada.
NÃO EXECUTE SQL NO SUPABASE REMOTO NESTA ETAPA.

## 2. CONTEXTO EXISTENTE
Projeto: SOSP.
Repositório: utilize o projeto atualmente aberto.
Branch principal de desenvolvimento: develop.
Arquivo principal do banco: docs/database/schema.sql
O schema já contempla:
- 36 tabelas de aplicação.
- 9 módulos funcionais.
- Chaves primárias e estrangeiras.
- Constraints.
- Índices.
- Triggers.
- Views.
- RLS habilitado nas tabelas.

Objetivo: Adicionar uma camada SQL de controle de acesso que seja:
- Funcional.
- Segura.
- Reproduzível.
- Testável em PostgreSQL isolado.
- Compatível com a futura arquitetura Django.
- Documentada para apresentação acadêmica.
Não recrie o schema existente.
Não altere funcionalidades de frontend ou backend.
```

---

## 9. Conclusão

A entrega cumpre integralmente os requisitos formais da **3AF (1,0 ponto)**, fornecendo código SQL limpo, modular, idempotente e testado. O SOSP avança com uma base de dados robusta, aderente às melhores práticas de segurança da informação, pronta para receber as futuras migrations do Django ORM e a integração definitiva com o Supabase.
