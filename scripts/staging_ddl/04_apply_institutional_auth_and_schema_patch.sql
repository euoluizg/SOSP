-- ==============================================================================
-- SOSP — PATCH DE ATUALIZAÇÃO DE SCHEMA E AUTENTICAÇÃO INSTITUCIONAL (SUPABASE)
-- Aplica com estrita idempotência:
-- 1. Colunas e índices complementares (genderDescription, unitId).
-- 2. Harmonização das constraints (role institucional aceitando 'server', matrículas com hífen).
-- 3. Schema sosp_security e função de autenticação institucional de menor privilégio sob RLS.
-- (Escopo estritamente institucional: não altera funções de cidadão ou recuperação de senha)
-- ==============================================================================

BEGIN;

-- 1. Alinhamento de colunas e índices
ALTER TABLE public.accountsCitizen
    ADD COLUMN IF NOT EXISTS genderDescription varchar(120);

ALTER TABLE public.accountsInternalUser
    ADD COLUMN IF NOT EXISTS unitId uuid;

CREATE INDEX IF NOT EXISTS idxAccountsInternalUserUnit
    ON public.accountsInternalUser (unitId);

-- 2. Remoção de constraints legadas do baseline antigo se existirem
ALTER TABLE public.accountsInternalUser DROP CONSTRAINT IF EXISTS chkAccountsInternalUserRole;
ALTER TABLE public.accountsInternalUser DROP CONSTRAINT IF EXISTS chkAccountsInternalUserRegistration;
ALTER TABLE public.accountsInternalUser DROP CONSTRAINT IF EXISTS chkAccountsInternalUserCpf;

-- 3. Harmonização de constraints de accountsInternalUser
ALTER TABLE public.accountsInternalUser DROP CONSTRAINT IF EXISTS chkAccountsInternalRole;
ALTER TABLE public.accountsInternalUser ADD CONSTRAINT chkAccountsInternalRole
    CHECK (role IN ('superadmin', 'admin', 'gestor', 'server', 'manager', 'servant', 'administrator'));

ALTER TABLE public.accountsInternalUser DROP CONSTRAINT IF EXISTS chkAccountsInternalRegistration;
ALTER TABLE public.accountsInternalUser ADD CONSTRAINT chkAccountsInternalRegistration
    CHECK (registrationNumber ~ '^[A-Za-z0-9-]{1,20}$');

ALTER TABLE public.accountsInternalUser DROP CONSTRAINT IF EXISTS chkAccountsInternalCpf;
ALTER TABLE public.accountsInternalUser ADD CONSTRAINT chkAccountsInternalCpf
    CHECK (cpf ~ '^[0-9]{11}$');

ALTER TABLE public.accountsInternalUser DROP CONSTRAINT IF EXISTS chkAccountsInternalEmail;
ALTER TABLE public.accountsInternalUser ADD CONSTRAINT chkAccountsInternalEmail
    CHECK (email ~* '^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$');

ALTER TABLE public.accountsInternalUser DROP CONSTRAINT IF EXISTS chkAccountsInternalName;
ALTER TABLE public.accountsInternalUser ADD CONSTRAINT chkAccountsInternalName
    CHECK (char_length(fullName) >= 3);

-- 4. Harmonização de constraint de accountsSession
ALTER TABLE public.accountsSession DROP CONSTRAINT IF EXISTS chkAccountsSessionSubjectType;
ALTER TABLE public.accountsSession DROP CONSTRAINT IF EXISTS chkAccountsSessionSubject;
ALTER TABLE public.accountsSession ADD CONSTRAINT chkAccountsSessionSubject
    CHECK (subjectType IN ('citizen', 'internal'));

-- 5. Configuração do schema sosp_security
CREATE SCHEMA IF NOT EXISTS sosp_security;
REVOKE CREATE ON SCHEMA sosp_security FROM PUBLIC;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sosp_runtime_role') THEN
        GRANT USAGE ON SCHEMA sosp_security TO sosp_runtime_role;
    END IF;
END $$;

-- 6. Função de autenticação cirúrgica de menor privilégio para usuários internos
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
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sosp_runtime_role') THEN
        GRANT EXECUTE ON FUNCTION sosp_security.authenticate_internal_user_by_cpf(VARCHAR) TO sosp_runtime_role;
    END IF;
END $$;

COMMENT ON FUNCTION sosp_security.authenticate_internal_user_by_cpf(VARCHAR) IS
    'Autenticação institucional segura sob RLS para servidores, gestores e administradores (ADR-003, RS-01).';

COMMIT;
