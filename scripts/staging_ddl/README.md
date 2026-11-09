# SOSP — Preparação e Execução Supervisionada de DDL (Supabase Staging)

> **Ambiente:** STAGING (`aws-1-sa-east-1.pooler.supabase.com:5432 / postgres`)  
> **Versão do Banco:** PostgreSQL 17 gerenciado no Supabase  
> **Branch de Versionamento:** `feat/be/supabase-ddl-prep`  
> **Status:** Preparado e Auditado Localmente (Aguardando Aprovação Humana para Execução Remota)  

---

## 1. Visão Geral e Princípios Inegociáveis

Este diretório contém a suíte completa e idempotente de migração e verificação estrutural do banco de dados do SOSP para o ambiente de STAGING.

Seguindo estritamente o `AGENTS.md` e as regras de arquitetura:
1. **Identificadores em `camelCase` sem aspas duplas (`ADR-002`):**
   - Todas as 36 tabelas de domínio, 2 views, colunas e constraints utilizam `camelCase` sem aspas duplas.
   - O PostgreSQL realiza o case-folding ordinário para minúsculas internamente no catálogo (`pg_class`, `information_schema`), garantindo compatibilidade total com os models Django (`db_table` e `db_column`).
2. **Exclusão Lógica Obrigatória (`RN-40`, `RS-05`):**
   - Nenhum comando `DROP TABLE` ou `TRUNCATE` é utilizado. A aplicação é estritamente aditiva e idempotente (`CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`).
3. **Segurança de Autenticação (`RS-02`, `RN-29`):**
   - Criação do schema `sosp_security` e da função cirúrgica `sosp_security.authenticate_citizen_by_cpf`.
   - Definida com `SECURITY DEFINER` e `SET search_path = pg_catalog, public`.
   - Validação estrita de entrada (regex `^[0-9]{11}$`).
   - Retorno sob `LIMIT 1` contendo estritamente as credenciais necessárias, omitindo o hash de senha se a conta estiver bloqueada por tentativas excessivas (`blockedUntil > clock_timestamp()`).
   - `REVOKE ALL ON FUNCTION ... FROM PUBLIC`.
4. **Defesa em Profundidade com Row Level Security (RLS):**
   - `ALTER TABLE ... ENABLE ROW LEVEL SECURITY;` habilitado em 100% das 36 tabelas.
5. **Views Analíticas com `security_invoker = true`:**
   - As views `vw_catalogServiceSearch` e `vw_schedulingSlotAvailability` são declaradas com `security_invoker = true` para respeitar as políticas de acesso do chamador.

---

## 2. Inventário Físico e Lógico de Objetos (40 Objetos Relacionais)

| Tipo | Quantidade | Nomes dos Objetos |
|---|:---:|---|
| **Tabelas de Contas (`accounts`)** | 6 | `accountsGender`, `accountsCitizen`, `accountsInternalUser`, `accountsSession`, `accountsLoginAttempt`, `accountsPasswordReset` |
| **Tabelas de Catálogo (`catalog`)** | 11 | `catalogAgency`, `catalogUnit`, `catalogUnitOpeningHour`, `catalogNonWorkingDay`, `catalogService`, `catalogServiceAgency`, `catalogUnitService`, `catalogServiceStep`, `catalogServiceDocument`, `catalogFaq`, `catalogServiceVersion` |
| **Tabelas de Busca (`search`)** | 2 | `searchQueryLog`, `searchSynonym` |
| **Tabelas de Guia (`guidance`)** | 2 | `guidanceProgress`, `guidanceGeneratedPdf` |
| **Tabelas de Agendamento (`scheduling`)** | 5 | `schedulingSlot`, `schedulingAppointment`, `schedulingProtocol`, `schedulingProtocolAttachment`, `schedulingProtocolTransition` |
| **Tabelas de Feedback (`feedback`)** | 3 | `feedbackReview`, `feedbackReviewReport`, `feedbackQuestion` |
| **Tabelas de Notificações (`notifications`)** | 4 | `notificationsTemplate`, `notificationsPreference`, `notificationsDelivery`, `notificationsPushSubscription` |
| **Tabelas de Relatórios (`reports`)** | 1 | `reportsExport` |
| **Tabelas de Auditoria (`audit`)** | 2 | `auditEvent`, `auditDataSubjectRequest` |
| **Views Analíticas** | 2 | `vw_catalogServiceSearch`, `vw_schedulingSlotAvailability` |
| **Tabelas Core do Django** | 2 | `django_migrations`, `django_content_type` |
| **TOTAL GERAL** | **40** | **36 Tabelas de Domínio + 2 Tabelas Django + 2 Views Analíticas** |

---

## 3. Relação de Scripts e Arquivos

- **[`01_preflight_check.py`](01_preflight_check.py):** Script de inspeção prévia em modo estritamente *read-only* (`default_transaction_read_only=on`). Verifica versão do PostgreSQL, extensões instaladas, schemas, objetos existentes e ausência de locks conflitantes.
- **[`02_apply_schema.sql`](02_apply_schema.sql):** Script SQL consolidado, 100% idempotente e transacional contendo todo o DDL do SOSP (36 tabelas, 2 views, funções com search_path restrito, índices e RLS).
- **[`02_apply_staging_ddl.py`](02_apply_staging_ddl.py):** Executor Python com suporte nativo a Dry-Run (transação encerrada com `ROLLBACK`) e Apply (transação confirmada com `COMMIT` mediante autorização humana explícita).
- **[`03_postflight_verify.py`](03_postflight_verify.py):** Script de auditoria pós-execução. Valida os 7 critérios essenciais (36 tabelas, 2 views, 100% RLS, função de segurança ativa sem permissão pública, triggers e FTS).
- **[`run_staging_ddl_suite.sh`](run_staging_ddl_suite.sh):** Pipeline automatizado que executa os passos em sequência supervisionada.

---

## 4. Procedimento Operacional Passo a Passo

### Passo 1: Pré-Voo Somente Leitura (Sem risco)
```bash
python scripts/staging_ddl/01_preflight_check.py
```
*Garantia: O banco não sofre nenhuma alteração. Retorna o inventário atual e diagnóstico de prontidão.*

### Passo 2: Simulação Dry-Run (Sem risco)
```bash
python scripts/staging_ddl/02_apply_staging_ddl.py --dry-run
```
*Garantia: O script DDL é executado dentro de uma transação PostgreSQL que é revertida ao final com `ROLLBACK`. Comprova que não há erros de sintaxe, tipos inválidos ou restrições conflitantes.*

### Passo 3: Aplicação Real no Supabase Staging (Requer Autorização Humana)
> [!CAUTION]
> **Portão de Aprovação Humana:** Este comando só deve ser executado com aprovação formal do Tech Lead / PO.

```bash
SOSP_CONFIRM_STAGING_APPLY=true python scripts/staging_ddl/02_apply_staging_ddl.py --apply --confirm-apply
```

### Passo 4: Auditoria de Pós-Voo
```bash
python scripts/staging_ddl/03_postflight_verify.py
```
*Garantia: Confirma que todos os 40 objetos foram criados com sucesso e que a função de autenticação está protegida.*
