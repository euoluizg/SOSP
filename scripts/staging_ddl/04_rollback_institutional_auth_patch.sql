-- ==============================================================================
-- SOSP — ROLLBACK SEGURO DO PATCH DE AUTENTICAÇÃO INSTITUCIONAL (SUPABASE)
-- Restaura o estado anterior com segurança e continuidade operacional:
-- 1. Restaura a função sosp_security.authenticate_internal_user_by_cpf para 10 colunas (baseline).
-- 2. Concede permissão de execução exclusivamente a sosp_runtime_role.
-- 3. Preserva a retrocompatibilidade de colunas e constraints para evitar perda de integridade.
-- 4. Jamais remove ou interfere nas funções de autenticação de cidadãos ou recuperação de senha.
-- ==============================================================================

BEGIN;

-- 1. Restauração segura da assinatura de 10 colunas da função de autenticação institucional
DROP FUNCTION IF EXISTS sosp_security.authenticate_internal_user_by_cpf(VARCHAR);

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
    is_active BOOLEAN
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
BEGIN
    IF p_cpf IS NULL OR p_cpf !~ '^[0-9]{11}$' THEN
        RETURN;
    END IF;

    RETURN QUERY
    SELECT
        u.id AS user_id,
        u.fullName AS full_name,
        u.email AS email,
        u.registrationNumber AS registration_number,
        u.agencyId AS agency_id,
        u.unitId AS unit_id,
        u.role AS role,
        u.canManageCatalog AS can_manage_catalog,
        u.passwordHash::TEXT AS password_hash,
        u.isActive AS is_active
    FROM public.accountsInternalUser u
    WHERE u.cpf = p_cpf
      AND u.isActive = true
      AND u.deletedAt IS NULL
    LIMIT 1;
END;
$$;

REVOKE ALL ON FUNCTION sosp_security.authenticate_internal_user_by_cpf(VARCHAR) FROM PUBLIC;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sosp_runtime_role') THEN
        GRANT EXECUTE ON FUNCTION sosp_security.authenticate_internal_user_by_cpf(VARCHAR) TO sosp_runtime_role;
    END IF;
END $$;

COMMENT ON FUNCTION sosp_security.authenticate_internal_user_by_cpf(VARCHAR) IS
    'Versão restaurada (10 colunas): autenticação institucional sob RLS.';

-- Observação de Integridade: Colunas complementares (genderDescription, unitId) e constraints
-- harmonizadas são retrocompatíveis e são mantidas para não quebrar dados nem travar sessões.

COMMIT;
