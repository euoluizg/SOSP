# SOSP — Sistema de Orientação para Serviços Públicos
## Avaliação Final (3AF) — Disciplina de Banco de Dados
### Critério: Criação de Contas e Permissões para Acessar a Estrutura (1,0 Ponto)
#### Relatório de Implementação e Endurecimento de Segurança (Revisão Pós-Auditoria)

---

- **Instituição:** Centro Universitário Cesmac (CESMAC)
- **Curso:** Bacharelado em Engenharia de Software
- **Disciplina:** Banco de Dados
- **Data Limite de Avaliação:** 27 de novembro de 2026
- **Equipe Oficial do Projeto:**
  - **Product Owner (PO):** Mozart Melo
  - **Tech Lead, Back-end (`Django 5 + DRF`) e DevOps:** Arthur Franco
  - **Front-end (`Next.js 15`), UI/UX Design e QA:** Luiz Gustavo
- **Repositório:** `euoluizg/SOSP` (Branch de Trabalho: `feature/postgresql-roles-rls-fixes`)

---

## 1. Objetivo Acadêmico e Escopo da Entrega

O presente documento e os scripts SQL que o acompanham atendem formalmente ao critério avaliativo da **3AF — Disciplina de Banco de Dados**:

> **"Criação de Contas e Permissões para acessar a estrutura" — Valor: 1,0 ponto.**

Esta revisão pós-auditoria aprimora a camada de **Governança, Controle de Acesso Baseado em Papéis (RBAC - Role-Based Access Control)** e **Segurança em Nível de Linha (RLS - Row-Level Security)** no SGBD **PostgreSQL 17 / 18**, endereçando:
1. **Auditoria e Bloqueio de Bypass de RLS em Views:** Aplicação de `security_invoker = true` nas views `vw_catalogServiceSearch` e `vw_schedulingSlotAvailability`;
2. **Eliminação de Exceções Genéricas (`WHEN OTHERS`):** Testes rigorosos e determinísticos com `ON_ERROR_STOP on` e captura exclusiva de `insufficient_privilege`;
3. **Validação da Herança Transitiva (`INHERIT`):** Papéis de grupo configurados com `INHERIT` no PostgreSQL 17, comprovando que o operador herda leitura do leitor;
4. **Princípio do Menor Privilégio (*PoLP*):** Remoção de concessões genéricas em sequências (`GRANT USAGE ON ALL SEQUENCES`), uma vez que o schema adota exclusivamente identificadores `UUID` (`gen_random_uuid()`);
5. **Salvaguardas de Execução:** Proteção ativa contra comandos `TRUNCATE CASCADE` em ambientes não descartáveis (Supabase/produção);
6. **Autenticação Real (`LOGIN`) vs. Impersonação (`SET ROLE`):** Comprovação prática de login com sessões independentes e segredos voláteis não versionados.

---

## 2. Arquitetura de Contas e Roles PostgreSQL

A arquitetura adota a separação estrita entre **Papéis de Grupo (*Group Roles / NOLOGIN*)** e **Contas de Usuário (*User Accounts / LOGIN*)**. Usuários recebem privilégios exclusivamente através de herança declarativa (`INHERIT`):

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
     |   (NOLOGIN, INHERIT)  |                       |   (NOLOGIN, INHERIT)  |
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
   - **Privilégios:** Acesso somente leitura (`SELECT`) às 11 tabelas do catálogo de serviços públicos, à tabela de sinônimos (`searchSynonym`), à tabela de capacidade de agendamento (`schedulingSlot`) e às duas views públicas.
   - **Restrições:** Proibição irrestrita de qualquer operação de escrita (`INSERT`, `UPDATE`, `DELETE`) e de qualquer comando DDL.
2. **`sosp_operador_role`:**
   - **Propósito:** Papel operacional de suporte e atendimento aos serviços públicos.
   - **Privilégios:** Herda todos os acessos de consulta de `sosp_leitor_role` via `GRANT sosp_leitor_role TO sosp_operador_role WITH INHERIT TRUE`; possui permissão controlada para registrar telemetria de buscas (`searchQueryLog`) e gerenciar conteúdo de FAQ (`catalogFaq`) e sinônimos (`searchSynonym`).
   - **Restrições:** Proibição de exclusão física (`DELETE`) em qualquer tabela; proibição total de leitura ou escrita em dados pessoais (`accountsCitizen`), credenciais (`accountsInternalUser`, `accountsPasswordReset`), agendamentos nominais (`schedulingAppointment`, `schedulingProtocol`) e auditoria imutável (`auditEvent`).

### 2.2. Contas de Demonstração (User Accounts — `LOGIN`)

- **`sosp_leitor_3af`:** Usuário com login pertencente ao papel `sosp_leitor_role`.
- **`sosp_operador_3af`:** Usuário com login pertencente ao papel `sosp_operador_role`.

---

## 3. Matriz Real de Privilégios (GRANT e REVOKE)

### 3.1. Revogações Efetivamente Executadas

1. **Revogação de Criação Pública no Schema:**
   ```sql
   REVOKE CREATE ON SCHEMA public FROM PUBLIC;
   ```
2. **Revogação Estrita de DELETE Físico (Atendimento a `RN-40` e `RS-05`):**
   ```sql
   REVOKE DELETE ON ALL TABLES IN SCHEMA public FROM sosp_leitor_role, sosp_operador_role;
   ```

### 3.2. Matriz de Acesso aos Objetos Reais do SOSP

| Domínio / Tabela Real | Tipo de Objeto | `sosp_leitor_role` | `sosp_operador_role` | Justificativa de Segurança |
| :--- | :--- | :---: | :---: | :--- |
| `catalogAgency` | Tabela | `SELECT` | `SELECT` *(herdado)* | Dados cadastrais públicos de órgãos |
| `catalogUnit` | Tabela | `SELECT` | `SELECT` *(herdado)* | Unidades de atendimento presenciais |
| `catalogService` | Tabela | `SELECT` | `SELECT` *(herdado)* | Fichas orientativas de serviços |
| `catalogUnitOpeningHour`| Tabela | `SELECT` | `SELECT` *(herdado)* | Horários de funcionamento das unidades |
| `catalogNonWorkingDay` | Tabela | `SELECT` | `SELECT` *(herdado)* | Feriados e pontos facultativos |
| `catalogServiceAgency` | Tabela | `SELECT` | `SELECT` *(herdado)* | Vínculo N:N de órgãos competentes |
| `catalogUnitService` | Tabela | `SELECT` | `SELECT` *(herdado)* | Vínculo N:N de unidades que ofertam o serviço |
| `catalogServiceStep` | Tabela | `SELECT` | `SELECT` *(herdado)* | Etapas do guia passo a passo |
| `catalogServiceDocument`| Tabela | `SELECT` | `SELECT` *(herdado)* | Relação de documentos obrigatórios |
| `catalogServiceVersion` | Tabela | `SELECT` | `SELECT` *(herdado)* | Histórico versionado de fichas |
| `catalogFaq` | Tabela | `SELECT` | `SELECT`, `INSERT`, `UPDATE` | Operador gerencia dúvidas frequentes |
| `searchSynonym` | Tabela | `SELECT` | `SELECT`, `INSERT`, `UPDATE` | Sinônimos utilizados na view de busca |
| `searchQueryLog` | Tabela | **NEGADO** | `SELECT`, `INSERT` | Registro anônimo de termos pesquisados |
| `schedulingSlot` | Tabela | `SELECT` | `SELECT` *(herdado)* | Capacidade agregada de horários |
| `vw_catalogServiceSearch` | View | `SELECT` | `SELECT` *(herdado)* | Busca unificada com `security_invoker = true` |
| `vw_schedulingSlotAvailability` | View | `SELECT` | `SELECT` *(herdado)* | Vagas disponíveis com `security_invoker = true` |
| `accountsCitizen` | Tabela | **NEGADO** | **NEGADO** | Dados pessoais e LGPD (`RS-01`) |
| `accountsCitizenSession`| Tabela | **NEGADO** | **NEGADO** | Sessões ativas do cidadão |
| `accountsInternalUser` | Tabela | **NEGADO** | **NEGADO** | Credenciais administrativas de servidores |
| `accountsPasswordReset` | Tabela | **NEGADO** | **NEGADO** | Tokens temporários de recuperação |
| `schedulingAppointment`| Tabela | **NEGADO** | **NEGADO** | Agendamentos presenciais do cidadão |
| `schedulingProtocol` | Tabela | **NEGADO** | **NEGADO** | Protocolos nominais `AAAAMMDD-XXXX` |
| `auditEvent` | Tabela | **NEGADO** | **NEGADO** | Trilha imutável de auditoria (`RN-39`) |
| `auditDataSubjectRequest`| Tabela | **NEGADO** | **NEGADO** | Solicitações de direitos LGPD |

---

## 4. Auditoria de Views e Bloqueio de Bypass de RLS (`security_invoker = true`)

### 4.1. O Risco de Bypass de RLS em Views Padrão

No PostgreSQL (versões 15, 16, 17 e 18), views relacionais operam por padrão no modo **Security Definer** implícito:
> *Quando um usuário consulta uma view, as permissões e políticas de RLS das tabelas subjacentes são avaliadas com os privilégios do **criador/proprietário da view** (geralmente `postgres` / DBA).*

Esse comportamento causaria uma grave brecha no SOSP:
- A tabela `catalogService` possui política RLS que proíbe o leitor de ver serviços em rascunho (`status = 'draft'`).
- Caso a view `vw_catalogServiceSearch` fosse consultada no modo padrão, ela consultaria `catalogService` como `postgres`, **expondo serviços em rascunho a qualquer cidadão**.

### 4.2. Solução Implementada

Configuramos ambas as views existentes com o parâmetro `security_invoker = true`:
```sql
ALTER VIEW vw_catalogServiceSearch SET (security_invoker = true);
ALTER VIEW vw_schedulingSlotAvailability SET (security_invoker = true);
```

Com essa diretiva:
1. O PostgreSQL avalia o RLS das tabelas base utilizando a identidade do **usuário chamador** (`invoker`);
2. Quando `sosp_leitor_3af` consulta `vw_catalogServiceSearch`, a política `p_leitor_catalog_service_select` é acionada, retornando **0 serviços em rascunho**;
3. Para viabilizar a execução legítima das views sem erros de permissão, foram concedidos privilégios de leitura e políticas RLS nas tabelas componentes `searchSynonym` e `schedulingSlot`.

---

## 5. Salvaguardas de Execução e Autenticação Real

### 5.1. Proteção contra TRUNCATE Acidental em Produção/Supabase

Para prevenir que a execução acidental de testes destrua dados em bancos reais, a suíte de testes [test_roles_permissions.sql](file:///Users/euoluizg/Desktop/CESMAC/EngenhariaDeSoftware/SOSP/docs/database/tests/test_roles_permissions.sql) inicia com validação ativa:
```sql
DO $$
DECLARE
  v_db text := current_database();
BEGIN
  IF v_db NOT ILIKE '%test%' AND v_db NOT ILIKE '%local%' AND v_db NOT ILIKE '%sosp_isolated%' THEN
    RAISE EXCEPTION 'BLOQUEIO DE SEGURANÇA: Este script de teste contém TRUNCATE CASCADE e NÃO pode ser executado no banco "%"!', v_db;
  END IF;

  IF current_user = 'supabase_admin' THEN
    RAISE EXCEPTION 'BLOQUEIO DE SEGURANÇA: Detectado usuário "supabase_admin". Execução abortada!';
  END IF;
END
$$;
```

### 5.2. Autenticação Real (`LOGIN`) vs. Impersonação (`SET ROLE`)

- **`SET ROLE` (Autorização / Impersonação):** Altera temporariamente o `current_user` mantendo o `session_user` original. É útil para auditoria em lote dentro de uma transação.
- **Autenticação Real (LOGIN):** Estabelece uma conexão de rede TCP/Socket independente onde `current_user = session_user = sosp_leitor_3af`.

Foi criado o script automatizado [test_auth_login.sh](file:///Users/euoluizg/Desktop/CESMAC/EngenhariaDeSoftware/SOSP/docs/database/tests/test_auth_login.sh), que gera senhas aleatórias voláteis via `openssl rand -hex 16`, conecta diretamente como `sosp_leitor_3af` e `sosp_operador_3af`, valida a sessão real e revoga os segredos temporários imediatamente, sem expor ou versionar senhas.

---

## 6. Resultados e Evidências dos Testes Automatizados

A suíte foi executada em PostgreSQL 18.6 com `\set ON_ERROR_STOP on`. Nenhum erro foi mascarado com `WHEN OTHERS`.

### 6.1. Tabela Consolidada de Resultados

| Cenário | Operação Testada | Papel Executante | Resultado Esperado | Resultado Obtido | Status |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **A** | `SELECT` em `catalogAgency` | `sosp_leitor_3af` | Autorizado com sucesso | Recuperou `SESAU` | **APROVADO** |
| **G.1**| RLS direto em `catalogService` | `sosp_leitor_3af` | Filtrar rascunhos | 1 ativo, 0 rascunhos | **APROVADO** |
| **G.3**| RLS na view `vw_catalogServiceSearch` | `sosp_leitor_3af` | `security_invoker` bloqueia rascunhos | 1 ativo, 0 rascunhos na view | **APROVADO** |
| **G.4**| Leitura da view `vw_schedulingSlotAvailability` | `sosp_leitor_3af` | Consulta de vagas autorizada | 1 slot disponível recuperado | **APROVADO** |
| **B** | `INSERT` em `catalogService` | `sosp_leitor_3af` | Negado (`insufficient_privilege`) | Bloqueado com sucesso | **APROVADO** |
| **C** | `UPDATE` em `catalogAgency` | `sosp_leitor_3af` | Negado (`insufficient_privilege`) | Bloqueado com sucesso | **APROVADO** |
| **E.1**| `SELECT` em `accountsCitizen` | `sosp_leitor_3af` | Negado (`insufficient_privilege`) | Acesso a CPF/dados barrado | **APROVADO** |
| **F.1**| `CREATE TABLE` no schema public | `sosp_leitor_3af` | Negado (`insufficient_privilege`) | DDL bloqueado | **APROVADO** |
| **H** | Herança de leitura via `INHERIT` | `sosp_operador_3af` | Ler catálogo e ver rascunhos | 2 serviços (1 ativo, 1 draft) | **APROVADO** |
| **D.1**| `INSERT` em `searchQueryLog` | `sosp_operador_3af` | Inserção autorizada | Telemetria gravada | **APROVADO** |
| **D.2**| `SELECT` em `searchQueryLog` | `sosp_operador_3af` | Leitura autorizada | Termo recuperado | **APROVADO** |
| **D.3**| `INSERT` e `UPDATE` em `catalogFaq`| `sosp_operador_3af` | Operações autorizadas | FAQ criada e atualizada | **APROVADO** |
| **E.2**| `SELECT` em `accountsCitizen` | `sosp_operador_3af` | Negado (`insufficient_privilege`) | Acesso a dados barrado | **APROVADO** |
| **E.3**| `SELECT` em `auditEvent` | `sosp_operador_3af` | Negado (`insufficient_privilege`) | Auditoria barrada | **APROVADO** |
| **E.4**| `DELETE` em `catalogFaq` | `sosp_operador_3af` | Negado (`insufficient_privilege`) | Exclusão física impedida | **APROVADO** |
| **F.2**| `CREATE TABLE` no schema public | `sosp_operador_3af` | Negado (`insufficient_privilege`) | DDL bloqueado | **APROVADO** |
| **G.2**| RLS `WITH CHECK` em `catalogFaq` | `sosp_operador_3af` | Rejeitar pergunta curta (< 5 car.) | `violates row-level security` | **APROVADO** |
| **AUTH**| Conexão de rede TCP com credenciais | `sosp_leitor_3af` / `sosp_operador_3af` | `current_user = session_user` | Autenticação real confirmada | **APROVADO** |

---

## 7. Registro de Ferramentas de Inteligência Artificial

Em estrito cumprimento das diretrizes de integridade acadêmica, documenta-se o uso de ferramentas de Inteligência Artificial:

- **Ambiente de Desenvolvimento:** Google DeepMind Antigravity IDE (Advanced Agentic Coding);
- **Modelos de Linguagem Empregados:**
  - **Claude Opus 5.5 / 3.7 Sonnet (Anthropic)**: Auditoria de segurança de permissões, modelagem de RLS e revisão crítica de scripts;
  - **Gemini 3.8 Flash / 2.5 Pro (Google DeepMind)**: Execução rápida de testes automatizados e conferência de sintaxe PL/pgSQL;
- **Preservação de Prompts:** Todos os prompts de comando foram preservados na íntegra no histórico técnico e na documentação do projeto.

---

## 8. Conclusão

A camada de segurança SQL do SOSP atende integralmente ao critério avaliativo da **3AF (1,0 ponto)**. Com a introdução de `security_invoker = true` nas views, herança transitiva declarativa, testes rigorosos sem `WHEN OTHERS` e comprovação de login independente, o banco de dados apresenta um modelo robusto de defesa em profundidade, 100% pronto para a futura integração com o Django 5 e o Supabase.
