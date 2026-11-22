-- ==============================================================================
-- SOSP — ROLLBACK DO PATCH DE MENOR PRIVILÉGIO PARA AUTENTICAÇÃO
-- Remove com segurança a função sosp_security.authenticate_citizen_by_cpf
-- em caso de necessidade de reversão durante a homologação.
--
-- ATENÇÃO: ARQUIVO PREPARADO E TESTADO LOCALMENTE.
-- NÃO EXECUTAR REMOTAMENTE SEM AUTORIZAÇÃO HUMANA EXPLÍCITA.
-- ==============================================================================

BEGIN;

-- Revoga privilégios antes do DROP
REVOKE ALL ON FUNCTION sosp_security.authenticate_citizen_by_cpf(VARCHAR) FROM sosp_runtime_role;
REVOKE ALL ON FUNCTION sosp_security.authenticate_citizen_by_cpf(VARCHAR) FROM PUBLIC;

-- Remove a função usando RESTRICT (impede remoção acidental de dependências)
DROP FUNCTION IF EXISTS sosp_security.authenticate_citizen_by_cpf(VARCHAR) RESTRICT;

COMMIT;
