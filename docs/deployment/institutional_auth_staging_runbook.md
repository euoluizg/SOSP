# SOSP — Runbook de Implantação e Migração Supervisionada: Autenticação Institucional em Staging

> **Documento:** `docs/deployment/institutional_auth_staging_runbook.md`  
> **Ambiente Alvo:** Staging (Render Backend + Supabase PostgreSQL 17.11 — Projeto `cidtcgfowvgwgggvhbym`)  
> **Responsáveis:** Arthur Franco (Tech Lead, Back-end e DevOps) / Operador Autorizado  
> **Data:** Novembro / 2026  
> **Status:** Homologado para Execução Supervisionada  

---

## 1. Contexto e Justificativa Arquitetural

### 1.1. Separação Estrita de Responsabilidades e a Regra do `render-build.sh`

O script `backend/render-build.sh` possui uma salvaguarda inegociável documentada explicitamente:

```bash
# REGRA CRÍTICA DE SEGURANÇA:
# NUNCA adicionar 'python manage.py migrate' neste script.
# O schema no Supabase PostgreSQL 17.11 já está implantado (4C.2/4D.2)
# e qualquer migração deve seguir processo administrativo supervisionado.
```

Esta regra decorre das decisões arquiteturais **ADR-001** (Monólito Modular), **ADR-003** (Segurança e RBAC) e **ADR-008** (Supabase Gerenciado):

1. **Princípio do Menor Privilégio no Runtime:** A aplicação em execução no Render conecta-se ao banco sob a role restrita `sosp_runtime_app`. Essa role possui permissões exclusivas de DML (`SELECT`, `INSERT`, `UPDATE`) e execução cirúrgica de funções (`SECURITY DEFINER`), **sem permissões de DDL** (`CREATE TABLE`, `ALTER TABLE`, `DROP`, `GRANT`).
2. **Prevenção de Locks e Concorrência:** Comandos de migração automática em build de contêineres podem exigir bloqueios exclusivos de schema (`AccessExclusiveLock`), gerando *race conditions* durante deploys contínuos (*rolling deploys*) ou derrubando instâncias ativas caso ocorra *timeout* de migração.
3. **Isolamento de Staging vs. Produção:** Toda alteração de schema em banco de dados compartilhado/remoto deve ser realizada exclusivamente por operador humano autenticado com a role de alta permissão (`postgres`), precedida por verificação de integridade e seguida por testes de aceitação.

---

## 2. Checklist de Pré-Voo (Pre-Flight Checklist)

Antes de executar qualquer instrução no Supabase Staging:

- [ ] **1. Identificação do Projeto:** Confirmar que a conexão aponta para o projeto de staging `cidtcgfowvgwgggvhbym`.
- [ ] **2. Ponto de Conexão (Pooler vs. Session):**
  - Para comandos DDL / Migrations: Utilizar a porta direta de sessão **`5432`** (Session Pooler) ou o **Supabase SQL Editor**.
  - **Atenção:** A porta `6543` (Transaction Pooler / PgBouncer) não suporta comandos transacionais de DDL ou `prepared statements` de schema.
- [ ] **3. Backup e Snapshots:** Confirmar no painel do Supabase (*Database* -> *Backups*) que há snapshot recente disponível para restauração imediata.
- [ ] **4. Verificação de Locks Concorrentes:**
  ```sql
  SELECT pid, usename, query, state, age(clock_timestamp(), query_start) AS duration
  FROM pg_stat_activity
  WHERE wait_event_type = 'Lock' OR state = 'active'
  ORDER BY duration DESC;
  ```
- [ ] **5. Zero Modificações Fictícias:** Jamais criar órgãos ou unidades falsas no banco remoto. Respeitar o catálogo oficial.

---

## 3. Diagnóstico e Comparação de Schema

Execute as consultas abaixo no **Supabase SQL Editor** como role `postgres`:

### 3.1. Verificação de Migrações Aplicadas

```sql
SELECT app, name, applied 
FROM django_migrations 
WHERE app = 'accounts' 
ORDER BY applied DESC;
```

*Critério de Aceite:* Verificar se as migrações `0001_initial` e `0002_fix_constraints_and_registration` constam na tabela.

### 3.2. Verificação das Funções de Autenticação sob Menor Privilégio (`sosp_security`)

```sql
SELECT routine_schema, routine_name, security_type, data_type
FROM information_schema.routines
WHERE routine_schema = 'sosp_security'
  AND routine_name IN ('authenticate_citizen_by_cpf', 'authenticate_internal_user_by_cpf');
```

*Critério de Aceite:*
- `authenticate_citizen_by_cpf`: `security_type = 'DEFINER'`, retorna 8 colunas (`citizen_id`, `full_name`, `email`, `password_hash`, `is_active`, `blocked_until`, `login_attempts`, `role`).
- `authenticate_internal_user_by_cpf`: `security_type = 'DEFINER'`, retorna 11 colunas incluindo `must_change_password`.

### 3.3. Verificação da Coluna `mustChangePassword` em `accountsInternalUser`

```sql
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_name = 'accountsinternaluser'
  AND column_name = 'mustchangepassword';
```

---

## 4. Ordem e Comandos de Execução Supervisionada

### Passo 1: Execução das Migrações Django (Se Pendentes)

Conecte-se ao terminal operacional com as variáveis administrativas de staging:

```bash
cd backend
export DATABASE_URL="postgresql://postgres:[SENHA_POSTGRES]@aws-0-sa-east-1.pooler.supabase.com:5432/postgres?sslmode=require"
python manage.py showmigrations accounts
python manage.py migrate accounts
```

### Passo 2: Sincronização da Função de Autenticação Institucional (SQL Editor)

Caso a função `sosp_security.authenticate_internal_user_by_cpf` precise ser atualizada para suportar a 11ª coluna (`must_change_password`) com estrito menor privilégio:

```sql
-- Executar como role postgres no Supabase SQL Editor
CREATE OR REPLACE FUNCTION sosp_security.authenticate_internal_user_by_cpf(p_cpf VARCHAR)
RETURNS TABLE (
    user_id UUID,
    full_name VARCHAR,
    email VARCHAR,
    registration_number VARCHAR,
    agency_id UUID,
    unit_id UUID,
    role VARCHAR,
    can_manage_catalog BOOLEAN,
    password_hash TEXT,
    is_active BOOLEAN,
    must_change_password BOOLEAN
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
    v_clean_cpf VARCHAR(11);
BEGIN
    v_clean_cpf := regexp_replace(p_cpf, '[^0-9]', '', 'g');
    IF length(v_clean_cpf) != 11 THEN
        RETURN;
    END IF;

    RETURN QUERY
    SELECT 
        u.id AS user_id,
        u.fullname AS full_name,
        u.email,
        u.registrationnumber AS registration_number,
        u.agencyid AS agency_id,
        u.unitid AS unit_id,
        u.role,
        u.canmanagecatalog AS can_manage_catalog,
        u.passwordhash AS password_hash,
        u.isactive AS is_active,
        COALESCE(u.mustchangepassword, true) AS must_change_password
    FROM accountsinternaluser u
    WHERE u.cpf = v_clean_cpf
      AND u.isactive = true
      AND u.deletedat IS NULL
    LIMIT 1;
END;
$$;

-- Restringe privilégios: Revoga acesso público e concede exclusivamente a sosp_runtime_app
REVOKE ALL ON FUNCTION sosp_security.authenticate_internal_user_by_cpf(VARCHAR) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION sosp_security.authenticate_internal_user_by_cpf(VARCHAR) TO sosp_runtime_app;
```

### Passo 3: Provisionamento Idempotente dos Usuários Institucionais

Execute o comando canônico `provision_homologation_users`:

#### Cenário A — Com Órgão SSP e Unidade Reais Cadastrados:
```bash
python manage.py provision_homologation_users \
  --agency-acronym SSP \
  --unit-name "Já! Centro" \
  --interactive
```

#### Cenário B — Staging Atual (Zero Unidades Cadastradas / Sem SSP):
```bash
python manage.py provision_homologation_users \
  --allow-unlinked \
  --interactive
```

> **Aviso de Fail-Closed:** No Cenário B, o servidor é provisionado com `unit_id = None`. Sob a regra **RN-36** e **ADR-003**, endpoints operacionais de agendamento e atendimento retornarão `403 Forbidden` até que o servidor seja vinculado a uma unidade real pelo Administrador Geral no painel `/admin/usuarios`.

---

## 5. Verificação Pós-Execução (Post-Flight Verification)

Execute as seguintes validações no SQL Editor do Supabase:

### 5.1. Teste de Invocação Simulada sob `sosp_runtime_app`

```sql
SET ROLE sosp_runtime_app;

-- 1. Teste Admin Geral
SELECT user_id, full_name, role, must_change_password 
FROM sosp_security.authenticate_internal_user_by_cpf('99988877714');

-- 2. Teste Servidor Operacional
SELECT user_id, full_name, role, unit_id, must_change_password 
FROM sosp_security.authenticate_internal_user_by_cpf('33366699957');

-- 3. Confirmação de Menor Privilégio (SELECT direto DEVE retornar 0 linhas via RLS)
SELECT count(*) FROM accountsinternaluser;

RESET ROLE;
```

*Critérios de Sucesso:*
1. Admin retorna `role = 'superadmin'` e `must_change_password = true`.
2. Servidor retorna `role = 'server'` e `must_change_password = true`.
3. `SELECT count(*)` como `sosp_runtime_app` retorna `0` linhas (RLS ativa).

### 5.2. Validação da Sessão e Troca de Senha na API

1. Realizar login institucional em `POST /api/v1/auth/login`.
2. Confirmar que a resposta HTTP 200 contém `"mustChangePassword": true`.
3. Acessar endpoint protegido `/api/v1/audit/events` e confirmar `403 Forbidden` (`CHANGE_PASSWORD_REQUIRED`).
4. Executar troca de senha em `POST /api/v1/auth/change-password`.
5. Confirmar novo token com `"mustChangePassword": false` e acesso liberado às telas autorizadas.

---

## 6. Procedimento de Rollback Não-Destrutivo

Caso ocorra qualquer inconsistência ou necessidade de reversão:

1. **Reversão de Migração no Django:**
   ```bash
   python manage.py migrate accounts 0001_initial
   ```
2. **Compatibilidade com Assinatura Legada:**
   O código do backend (`CitizenDjangoORMRepository.get_internal_user_by_cpf_for_auth`) possui fallback transparente e seguro: caso a função retorne 10 colunas, ela assume de forma estrita `mustChangePassword = True` (*fail-closed*), garantindo que nenhum usuário consiga contornar a troca de senha mesmo em caso de reversão de schema.
3. **Preservação dos Dados:**
   Jamais execute comandos de limpeza destrutiva (`DROP TABLE`, `TRUNCATE` ou `CASCADE`). Todas as entidades utilizam exclusão lógica (`deletedAt`).
