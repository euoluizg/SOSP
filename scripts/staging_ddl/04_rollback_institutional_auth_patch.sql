-- ==============================================================================
-- SOSP — ROLLBACK DO PATCH DE AUTENTICAÇÃO INSTITUCIONAL E SCHEMA
-- ==============================================================================

BEGIN;

DROP FUNCTION IF EXISTS sosp_security.authenticate_internal_user_by_cpf(VARCHAR);
DROP FUNCTION IF EXISTS sosp_security.authenticate_citizen_by_cpf(VARCHAR);
DROP FUNCTION IF EXISTS sosp_security.set_citizen_recovery_code(VARCHAR, VARCHAR, TIMESTAMPTZ);
DROP FUNCTION IF EXISTS sosp_security.verify_citizen_recovery_code(VARCHAR, VARCHAR);
DROP FUNCTION IF EXISTS sosp_security.clear_citizen_recovery_code(VARCHAR);
DROP FUNCTION IF EXISTS sosp_security.reset_citizen_password(VARCHAR, VARCHAR, TEXT);

-- Observação: Colunas adicionadas (genderDescription, unitId) e constraints harmonizadas
-- não devem ser removidas em produção para preservar a integridade dos dados já gravados.

COMMIT;
