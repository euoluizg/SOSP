# SOSP — Runbook Operacional de Conexão com o Supabase PostgreSQL

> **Ambiente Alvo:** Supabase PostgreSQL 17 gerenciado (Região `sa-east-1` — São Paulo, AWS — Supabase Free Tier)  
> **Framework:** Django 5.1.15 + Django REST Framework + `psycopg` 3.2+  
> **Status:** Preparação Local e Hardening Concluídos — **Aguardando Liberação para Primeiro Pré-Voo Remoto Somente Leitura**  
> **Referências Normativas:** [`ADR-001`](../adr/ADR-001-monolito-modular-django-nextjs.md), [`ADR-002`](../adr/ADR-002-convencoes-nomenclatura-sql-camelcase.md), [`ADR-003`](../adr/ADR-003-autenticacao-autorizacao-rbac.md), [`ADR-005`](../adr/ADR-005-reserva-atomica-agendamento-idempotencia.md), [`ADR-008`](../adr/ADR-008-supabase-postgresql-gerenciado.md), [`schema.sql`](schema.sql), [`django-postgresql-foundation.md`](django-postgresql-foundation.md).

---

## 1. Visão Geral e Parâmetros Oficiais Confirmados

O SOSP utiliza um banco de dados relacional **PostgreSQL 17** hospedado no **Supabase** na região de São Paulo (`sa-east-1`). No padrão arquitetural do projeto, o portal Next.js 15 **nunca** acessa o banco diretamente; todo o tráfego de dados é intermediado pela API REST do Django (`ADR-001 §1`).

### Parâmetros Oficiais Confirmados pelo Proprietário do Projeto:
Os parâmetros de conectividade foram visualmente verificados e confirmados no painel oficial do Supabase:
- **Método de Conexão:** Session Pooler (Supavisor)
- **Host Oficial:** `aws-1-sa-east-1.pooler.supabase.com`
- **Porta:** `5432`
- **Database:** `postgres`
- **Username:** Valor exato do painel Connect no formato `postgres.<project-ref>`
- **SSL Mode:** `require` (no mínimo)

> [!CAUTION]
> **Host Incorreto em Documentações Anteriores:**  
> Versões preliminares citavam erroneamente `aws-0-sa-east-1.pooler.supabase.com`. **NÃO utilize `aws-0-...`**. O host validado e atribuído pelo Supabase a este projeto é estritamente **`aws-1-sa-east-1.pooler.supabase.com`**.  
> Nunca deduza ou invente hosts, portas ou identificadores de projeto (`project-ref`).

```mermaid
flowchart TD
    subgraph AppServer["Servidor de Aplicação (Render / Local)"]
        DjangoApp["Django 5 Runtime (Gunicorn/Uvicorn)\nREPOSITORY_BACKEND=memory (padrão)"]
        DjangoMigrate["Django Migrations (CI/CD ou Deploy Job)\nSession Pooler (Porta 5432)"]
        DiagScripts["Scripts de Pré-Voo (backend/scripts/)\nSomente Leitura (Read-Only)"]
    end

    subgraph SupabaseInfra["Infraestrutura Supabase (AWS sa-east-1 / São Paulo)"]
        subgraph Supavisor["Supavisor Connection Pooler (IPv4 / Dual-Stack)"]
            SessionPooler["Session Pooler (Porta 5432)\n★ aws-1-sa-east-1.pooler.supabase.com"]
            TxPooler["Transaction Pooler (Porta 6543)\n(Stateless / DISABLE_SERVER_SIDE_CURSORS)"]
        end
        DirectConn["Direct PostgreSQL Engine (Porta 5432 / IPv6 Exclusivo no Free Tier)"]
        PostgresDB[("PostgreSQL 17 Engine\n(36 tabelas SOSP + 2 views)")]
        DataAPI["Supabase PostgREST (Data API HTTP)\n[VERIFICAÇÃO OBRIGATÓRIA / DESATIVAR]"]
    end

    DjangoApp -->|Padrão Oficial: Runtime & Migrações| SessionPooler
    DjangoApp -.->|Alta Concorrência Leitura| TxPooler
    DjangoMigrate -->|Obrigatório: DDL Suportado| SessionPooler
    DjangoMigrate -.->|Alternativa com suporte IPv6| DirectConn
    DiagScripts -->|Validação Prévia Somente Leitura| SessionPooler

    SessionPooler --> PostgresDB
    TxPooler --> PostgresDB
    DirectConn --> PostgresDB

    DataAPI -.->|Restringir no Painel Supabase| PostgresDB
```

---

## 2. Modos de Conexão: Comparativo Técnico

O Supabase oferece três portas/métodos de acesso ao banco:

| Critério | Modo A: Direct Connection | Modo B: Session Pooler (Padrão Oficial) | Modo C: Transaction Pooler |
| :--- | :--- | :--- | :--- |
| **Host** | `db.<project-ref>.supabase.co` | **`aws-1-sa-east-1.pooler.supabase.com`** | **`aws-1-sa-east-1.pooler.supabase.com`** |
| **Porta** | `5432` | **`5432`** | `6543` |
| **Pilha IP** | **IPv6 Exclusivo** (no plano Free) | **IPv4 / IPv6** (Dual-Stack) | **IPv4 / IPv6** (Dual-Stack) |
| **Formato Usuário** | `postgres` | `postgres.<project-ref>` | `postgres.<project-ref>` |
| **Estado da Sessão** | Preservado | Preservado | **Descartado após transação** |
| **Prepared Statements** | Suportado | Suportado | Limitado / Requer atenção |
| **Server-Side Cursors** | Suportado | Suportado | **Incompatível** (`DISABLE_SERVER_SIDE_CURSORS = True`) |
| **Suporte a Migrations DDL** | **Total** | **Total** | **NÃO** (pode falhar com locks e DDL transacional) |
| **Compatibilidade com Render** | **Incompatível** (Render não suporta IPv6 outbound) | **100% Compatível (Recomendado)** | Compatível apenas para runtime |
| **Uso no SOSP** | Conexões locais via IPv6 | **Runtime e Migrações (Padrão Oficial)** | Opcional para workloads stateless |

> [!IMPORTANT]
> **Compatibilidade com Render.com:** O ambiente padrão do Render não possui suporte a roteamento IPv6 de saída. Conexões diretas (`db.<project-ref>.supabase.co`) falharão com erro de timeout ou rede inacessível. **Utilize exclusivamente o Session Pooler (`aws-1-sa-east-1.pooler.supabase.com:5432`)** para qualquer deploy no Render.

---

## 3. Padrão de Configuração Django (`backend/config/settings/base.py`)

A padronização das variáveis de ambiente de banco de dados segue regras estritas de governança:

1. **`DB_ENGINE`:**
   - Formatos suportados: `postgresql`, `django.db.backends.postgresql`, `postgres`, `sqlite3`, `django.db.backends.sqlite3`.
   - **Proibição de Fallback Silencioso:** Qualquer valor desconhecido gera imediatamente `ImproperlyConfigured`.
2. **`DB_REMOTE_REQUIRED=true`:**
   - Quando esta variável estiver ativa, a aplicação é **proibida de selecionar SQLite sob qualquer hipótese**. Se `DB_ENGINE` for `sqlite3` ou se faltarem credenciais remotas (`DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`), o Django abortará com `ImproperlyConfigured`.
3. **`REPOSITORY_BACKEND=memory`:**
   - Mantém-se como configuração **padrão** do repositório no MVP até que a base de dados remota seja formalmente implantada e validada.
4. **Segurança de SSL e Timeouts:**
   - Conexões remotas exigem `sslmode=require` (ou superior).
   - Timeouts padrão configurados: `connect_timeout=10` e `statement_timeout=30000ms`.

---

## 4. Matriz de Papéis (RBAC) e Não-Utilização de Contas Acadêmicas

O projeto SOSP implementa estrita segregação de privilégios (`ADR-003`, `RS-01` e `RS-03`):

1. **Separação Obrigatória entre Usuário de Aplicação e Usuário de Migrations:**
   - **`sosp_migration_user`:** Utilizado exclusivamente por pipelines de CI/CD ou deploys controlados. Possui direitos DDL (`CREATE`, `ALTER`, `DROP` em tabelas, views, triggers e sequences no schema `public`).
   - **`sosp_app_user`:** Utilizado pelo Django em runtime 24/7. Possui apenas permissões DML (`SELECT`, `INSERT`, `UPDATE`). **`DELETE` físico terminantemente revogado** (`RN-40`, `RS-05`). Não possui privilégios DDL.
2. **Proibição de Contas Acadêmicas da 3AF em Produção:**
   - As contas criadas no contexto acadêmico da 3AF (`sosp_leitor_role`, `sosp_operador_role`) com senhas de teste acadêmico **NÃO são credenciais de produção**. Não devem ser utilizadas no backend Django real nem vinculadas ao Supabase de produção.
3. **Não Utilizar o Superuser `postgres` em Runtime:**
   - O usuário default `postgres` ignora políticas de RLS e expõe schemas internos do Supabase (`auth`, `storage`, `vault`, `graphql_public`).
4. **Salvaguarda Operacional:**
   - **NÃO execute comandos remotos `GRANT`, `REVOKE` ou `CREATE ROLE` nesta etapa.** Quaisquer ajustes de papéis devem ser previamente planejados e autorizados pelo Tech Lead.

---

## 5. Cuidados com a Exposição via Supabase Data API (PostgREST)

Por padrão, novas instâncias do Supabase expõem todas as tabelas criadas no schema `public` via HTTP REST (PostgREST) na URL `https://<ref>.supabase.co/rest/v1/`.

### 5.1 Diretriz de Segurança SOSP
- O frontend Next.js consome exclusivamente os endpoints da API Django (`https://<api-domain>/api/v1/`), onde residem autenticação CPF/Argon2id, controle RBAC, validações RFC 7807 e auditoria imutável em `auditEvent`.
- **RLS e Views com `security_invoker = true`:** O script `baseline_0001_schema.sql` habilita `ENABLE ROW LEVEL SECURITY` nas **36 tabelas de domínio do SOSP** (negando acesso por padrão a roles não-proprietárias sem políticas explícitas) e cria as duas views analíticas (`vw_catalogServiceSearch` e `vw_schedulingSlotAvailability`) com `WITH (security_invoker = true)`, impedindo bypass de RLS.
- **Atenção:** **NÃO presuma que a Supabase Data API já esteja desabilitada.** É obrigatório verificar visualmente no painel do Supabase.
- **Ações Recomendadas no Painel e Pós-Implantação:**
  1. Acesse **Project Settings > API > Data API Settings**.
  2. No campo **"Exposed schemas"**, remova o schema `public` se nenhum client direto do Supabase for utilizado.
  3. Garanta que as roles `PUBLIC`, `anon` e `authenticated` não possuam privilégios DML (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) concedidos nas tabelas e views do SOSP no schema `public`.

---

## 6. Procedimento Seguro de Pré-Voo (Scripts em `backend/scripts/`)

Os scripts de pré-voo foram desenhados para execução estritamente somente-leitura e não-destrutiva.

### 6.1 Tratamento Seguro de Senhas e SSL (Sem Flags Inseguras na CLI)
> [!IMPORTANT]
> **1. Remoção Total da Opção `--password` na CLI:**  
> A opção CLI `--password` foi totalmente removida dos scripts. Fornecer senhas diretamente na linha de comando expõe credenciais no histórico do shell (`.zsh_history`, `history`) e na listagem de processos do sistema (`ps`).  
> Configure a senha na sessão do shell com `export DB_PASSWORD=...` (ou `export PGPASSWORD=...`) ou execute os scripts sem parâmetro para que o terminal solicite a senha interativamente de forma oculta via `getpass.getpass()`.
>
> **2. Rigor de SSL em Conexões Remotas:**  
> Para qualquer host remoto (`aws-1-sa-east-1.pooler.supabase.com`), os scripts exigem obrigatoriamente `sslmode=require`, `verify-ca` ou `verify-full`. Conexões remotas com `disable`, `allow` ou `prefer` são **rejeitadas imediatamente por governança** com erro de segurança. O modo `disable`/`prefer` é aceito exclusivamente para hosts locais (`localhost`, `127.0.0.1`, socket Unix).

### 6.2 Execução do Teste de Conectividade (`preflight_connectivity.py`)
```bash
# 1. Configurar variáveis na sessão segura do terminal (sem salvar em arquivos Git)
export DB_HOST="aws-1-sa-east-1.pooler.supabase.com"
export DB_PORT="5432"
export DB_NAME="postgres"
export DB_USER="postgres.<project-ref>"
export DB_SSLMODE="require"
# A senha deve ser informada via prompt interativo (recomendado) ou export temporário em memória:
# read -s DB_PASSWORD; export DB_PASSWORD

# 2. Executar o script de conectividade (lê do ambiente ou getpass interativo)
python backend/scripts/preflight_connectivity.py
```

**Códigos de Retorno:**
- `0`: Conectividade TCP/Socket, resolução DNS e handshake PostgreSQL/SSL aprovados.
- `1`: Falha de rede, timeout, DNS, autenticação ou modo SSL inseguro em host remoto.

### 6.3 Execução da Inspeção de Schema (`preflight_schema_inspection.py`)
Executa forçando `default_transaction_read_only=on`.

```bash
python backend/scripts/preflight_schema_inspection.py
```

**Matriz Diagnóstica de Saída:**
- `🟢 STATUS: PRONTO PARA IMPLANTAÇÃO INICIAL (READY_FOR_BASELINE) [AVALIAÇÃO PRELIMINAR]` (Exit code `0`):
  - Schema `public` limpo de tabelas, views e migrações.
  - Permissão `CREATE` confirmada.
  - Extensões `pg_trgm` e `unaccent` disponíveis.
  - > [!WARNING]
    > **Natureza Estritamente Preliminar:**  
    > O status `READY_FOR_BASELINE` representa unicamente uma **avaliação preliminar de não-conflito** no schema `public`. Ele **NÃO constitui autorização automática** para executar migrations.  
    > Contagens de objetos e ausência de tabelas não comprovam sozinhas a integridade semântica completa do banco (ex.: integridade de tipos, restrições e catálogo do sistema).  
    > A aplicação de qualquer migration requer **aprovação humana formal e explícita** do Tech Lead e CODEOWNER (`@euoluizg`).
- `🔵 STATUS: BASE TOTALMENTE IMPLANTADA (ALREADY_PROVISIONED)` (Exit code `0`):
  - Todas as 36 tabelas SOSP e 2 views presentes.
  - Todas as 14 migrações Django registradas em `django_migrations` (11 migrações iniciais + 3 migrações `0002_align_orm_state_with_schema` de alinhamento de estado do ORM).
  - Zero tabelas desconhecidas.
  - > [!NOTE]
    > Contagens quantitativas de tabelas (36 SOSP + 2 Django) e registros de migrations atestam a presença dos objetos físicos, devendo a integridade funcional ser complementada e comprovada pela suíte de testes de integração da aplicação (`62` testes automatizados em PostgreSQL).
- `🟡 STATUS: ESTADO PARCIAL DETECTADO (PARTIAL_STATE)` (Exit code `2`):
  - Tabelas ou migrações incompletas no banco.
  - **Ação:** Migração bloqueada. Requer investigação detalhada de integridade.
- `⚠️ STATUS: REVISÃO MANUAL OBRIGATÓRIA (MANUAL_REVIEW_REQUIRED)` (Exit code `2`):
  - Detectadas tabelas desconhecidas no schema `public`, views órfãs ou ausência de permissão `CREATE`.
  - **Ação:** Migração terminantemente bloqueada. Exige auditoria humana prévia.

---

## 7. Instruções para Execução Segura de Migrations

Após pré-voo com resultado `READY_FOR_BASELINE` e **autorização humana explícita do Tech Lead**:

```bash
# 1. Simular plano de migrações sem aplicar alterações físicas
python backend/manage.py migrate --plan

# 2. Aplicar migrações da baseline
python backend/manage.py migrate

# 3. Validar aplicação
python backend/manage.py showmigrations

# 4. Re-executar pré-voo de schema para comprovar ALREADY_PROVISIONED
python backend/scripts/preflight_schema_inspection.py
```

---

## 8. Estratégia Realista de Rollback, Contingência e Desastre (Supabase Free)

> [!CAUTION]
> **PROIBIÇÃO ABSOLUTA DE `migrate accounts zero` EM PRODUÇÃO:**  
> O script reverso da migration baseline `accounts.0001_initial` executa `DROP TABLE` em todas as 36 tabelas de aplicação e views com perda total e definitiva de dados. Este comando é terminantemente proibido fora de ambientes de teste temporários locais.

### 8.1 Limitações Reais do Plano Supabase Free
- **Sem Point-in-Time Recovery (PITR):** O recurso PITR não existe no plano Free (exclusivo para planos pagos/Pro).
- **Sem Restauração de Snapshot Point-and-Click:** O plano gratuito não oferece restauração automática diária com reversão de estado pelo painel com um clique.

### 8.2 Plano Oficial de Backup e Restauração Lógica Manual (`--schema=public`)
Para suprir as limitações do plano Free sem interferir nos schemas gerenciados pelo Supabase (`auth`, `storage`, `extensions`, `vault`), adote o procedimento de backup lógico restrito ao schema `public`:

1. **Geração de Backup Lógico Pré-Deploy / Pré-Migração (`pg_dump`):**
   ```bash
   # Executado a partir de ambiente seguro autorizado com pg_dump instalado
   pg_dump \
     -h aws-1-sa-east-1.pooler.supabase.com \
     -p 5432 \
     -U "postgres.<project-ref>" \
     -d postgres \
     --schema=public \
     --no-owner \
     --no-privileges \
     -f "./backups/sosp_public_backup_$(date +%Y%m%d_%H%M%S).sql"
   ```
2. **Armazenamento Seguro do Dump:**
   - Os arquivos de dump devem ser imediatamente transferidos para armazenamento criptografado privado (ex.: bucket privado S3 com criptografia SSE-KMS e retenção versionada).
   - **NUNCA armazene dumps no Git ou em servidores web públicos.**
3. **Distinção Obrigatória de Recuperação (Banco Vazio vs. Banco com Dados):**
   - **Cenário 1 — Falha Durante a Primeira Implantação (Banco Ainda Vazio / Etapa 4C.2):**
     - Como `baseline_0001_schema.sql` e cada migration do Django executam em transações atômicas (`BEGIN ... COMMIT`), uma falha durante `accounts.0001_initial` reverte automaticamente todas as 36 tabelas e 2 views (estado permanece `0` tabelas).
     - Caso a falha ocorra em uma migration subsequente com banco comprovadamente sem dados de negócio (`0` registros nas 36 tabelas), pode-se reexecutar `python backend/manage.py migrate` após corrigir a causa.
   - **Cenário 2 — Recuperação em Banco Já Contendo Dados:**
     - **Jamais execute `migrate accounts zero`, `DROP SCHEMA public CASCADE` ou `TRUNCATE`.**
     - Valide o dump primeiro em uma instância PostgreSQL isolada de homologação:
       ```bash
       psql -h <host-isolado> -U <user> -d sosp_restore_test -v ON_ERROR_STOP=1 -f "./backups/sosp_public_backup_YYYYMMDD_HHMMSS.sql"
       ```
     - Aplique correções estruturais exclusivamente via **Forward Migrations** aditivas (`0003_...`) após backup lógico verificado.
4. **Fallback de Emergência para In-Memory:**
   - Em caso de indisponibilidade severa do banco remoto, reinicie o backend com `REPOSITORY_BACKEND=memory` para manter a navegação consultiva de serviços operando.

> [!NOTE]
> **NÃO execute backup remoto nem restauração nesta etapa.** Este plano detalha a governança técnica a ser acionada em janelas operacionais autorizadas.

---

## 9. Checklist de Aprovação para o Primeiro Pré-Voo Remoto Somente Leitura

Antes de executar o primeiro pré-voo remoto:

- [ ] Host confirmado como `aws-1-sa-east-1.pooler.supabase.com` (Porta 5432).
- [ ] Credenciais obtidas no painel do Supabase e exportadas na sessão local do shell (`DB_PASSWORD`).
- [ ] `DB_ENGINE=postgresql` e `REPOSITORY_BACKEND=memory` configurados.
- [ ] Execução de `preflight_connectivity.py` retornando código `0`.
- [ ] Execução de `preflight_schema_inspection.py` retornando código `0` (`READY_FOR_BASELINE`).
- [ ] Aprovação formal do CODEOWNER (`@euoluizg`) para autorizar a aplicação remota de migrações em etapa subsequente.
