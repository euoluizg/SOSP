-- ==============================================================================
-- SOSP — FUNÇÃO DE AUTENTICAÇÃO INSTITUCIONAL (SUPABASE)
-- Pré-requisito: migration accounts.0002_add_gender_description_and_unit_to_accounts
-- aplicada e registrada pelo Django. A migration é a única responsável pelas colunas,
-- índices e constraints; este arquivo atualiza somente o schema de segurança e a função.
-- Não altera funções de cidadão ou recuperação de senha.
-- ==============================================================================

BEGIN;

-- Falha explicitamente se a execução estiver fora da sequência aprovada.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM public.django_migrations
        WHERE app = 'accounts' AND name = '0002_add_gender_description_and_unit_to_accounts'
    ) OR NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'accountsinternaluser' AND column_name = 'unitid'
    ) THEN
        RAISE EXCEPTION 'A migration accounts.0002 e a coluna unitId são pré-requisitos para a função institucional';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sosp_runtime_role') THEN
        RAISE EXCEPTION 'Role sosp_runtime_role ausente; interrompa e revise os grants';
    END IF;
END $$;

-- Configuração do schema sosp_security
CREATE SCHEMA IF NOT EXISTS sosp_security;
REVOKE CREATE ON SCHEMA sosp_security FROM PUBLIC;
GRANT USAGE ON SCHEMA sosp_security TO sosp_runtime_role;

-- Função de autenticação cirúrgica de menor privilégio para usuários internos
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
    is_active BOOLEAN,
    must_change_password BOOLEAN
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
        u.isActive AS is_active,
        u.mustChangePassword AS must_change_password
    FROM public.accountsInternalUser u
    WHERE u.cpf = p_cpf
      AND u.isActive = true
      AND u.deletedAt IS NULL
    LIMIT 1;
END;
$$;

REVOKE ALL ON FUNCTION sosp_security.authenticate_internal_user_by_cpf(VARCHAR) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION sosp_security.authenticate_internal_user_by_cpf(VARCHAR) TO sosp_runtime_role;

COMMENT ON FUNCTION sosp_security.authenticate_internal_user_by_cpf(VARCHAR) IS
    'Autenticação institucional segura sob RLS para servidores, gestores e administradores (ADR-003, RS-01).';

COMMIT;
