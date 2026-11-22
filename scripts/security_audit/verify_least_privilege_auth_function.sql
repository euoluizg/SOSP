-- ==============================================================================
-- SOSP — AUDITORIA E VERIFICAÇÃO PÓS-INSTALAÇÃO DA FUNÇÃO DE AUTENTICAÇÃO
-- Executa em transação READ ONLY para inspecionar permissões, owner e search_path.
--
-- ATENÇÃO: ARQUIVO DE AUDITORIA READ ONLY.
-- ==============================================================================

BEGIN TRANSACTION READ ONLY;

-- 1. Verifica existência, owner e security_definer
SELECT
    p.proname AS function_name,
    pg_get_userbyid(p.proowner) AS owner_name,
    p.prosecdef AS is_security_definer,
    p.proconfig AS configuration_settings
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'sosp_security'
  AND p.proname = 'authenticate_citizen_by_cpf';

-- 2. Verifica privilégios de execução: deve ser permitido apenas a sosp_runtime_role e negado a PUBLIC
SELECT
    has_function_privilege('public', 'sosp_security.authenticate_citizen_by_cpf(varchar)', 'execute') AS public_can_execute,
    has_function_privilege('sosp_runtime_role', 'sosp_security.authenticate_citizen_by_cpf(varchar)', 'execute') AS runtime_can_execute;

-- 3. Confirma que a tabela sosp_security.hmac_secret continua inacessível
SELECT has_table_privilege('sosp_runtime_role', 'sosp_security.hmac_secret', 'select') AS runtime_can_read_secret;

ROLLBACK;
