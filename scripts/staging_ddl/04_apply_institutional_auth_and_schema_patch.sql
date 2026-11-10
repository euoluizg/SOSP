-- ==============================================================================
-- SOSP — PATCH DE ATUALIZAÇÃO DE SCHEMA E AUTENTICAÇÃO INSTITUCIONAL (SUPABASE)
-- Aplica com estrita idempotência:
-- 1. Colunas e índices complementares (genderDescription, unitId).
-- 2. Harmonização das constraints (role institucional aceitando 'server', matrículas com hífen).
-- 3. Schema sosp_security e funções de menor privilégio para autenticação sob RLS.
-- ==============================================================================

BEGIN;

-- 1. Alinhamento de colunas e índices
ALTER TABLE public.accountsCitizen
    ADD COLUMN IF NOT EXISTS genderDescription varchar(120);

ALTER TABLE public.accountsInternalUser
    ADD COLUMN IF NOT EXISTS unitId uuid;

CREATE INDEX IF NOT EXISTS idxAccountsInternalUserUnit
    ON public.accountsInternalUser (unitId);

-- 2. Remoção de constraints legadas do baseline antigo
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

-- 6. Função de autenticação cirúrgica de menor privilégio para cidadãos
DROP FUNCTION IF EXISTS sosp_security.authenticate_citizen_by_cpf(VARCHAR);
CREATE OR REPLACE FUNCTION sosp_security.authenticate_citizen_by_cpf(p_cpf VARCHAR)
RETURNS TABLE (
    citizen_id UUID,
    full_name VARCHAR,
    email VARCHAR,
    password_hash TEXT,
    is_active BOOLEAN,
    blocked_until TIMESTAMPTZ,
    login_attempts INT,
    role VARCHAR
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
        c.id AS citizen_id,
        c.fullName AS full_name,
        c.email AS email,
        CASE
            WHEN (c.blockedUntil IS NOT NULL AND c.blockedUntil > clock_timestamp()) THEN NULL::TEXT
            ELSE c.passwordHash
        END AS password_hash,
        c.isActive AS is_active,
        c.blockedUntil AS blocked_until,
        c.loginAttempts AS login_attempts,
        'citizen'::VARCHAR AS role
    FROM public.accountsCitizen c
    WHERE c.cpf = p_cpf
      AND c.isActive = true
      AND c.deletedAt IS NULL
    LIMIT 1;
END;
$$;

REVOKE ALL ON FUNCTION sosp_security.authenticate_citizen_by_cpf(VARCHAR) FROM PUBLIC;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sosp_runtime_role') THEN
        GRANT EXECUTE ON FUNCTION sosp_security.authenticate_citizen_by_cpf(VARCHAR) TO sosp_runtime_role;
    END IF;
END $$;

-- 7. Função de autenticação cirúrgica de menor privilégio para usuários internos
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

-- 8. Funções de menor privilégio para recuperação de senha do cidadão (sob RLS)
DROP FUNCTION IF EXISTS sosp_security.get_citizen_recovery_code(VARCHAR);

CREATE OR REPLACE FUNCTION sosp_security.set_citizen_recovery_code(
    p_cpf VARCHAR,
    p_code VARCHAR,
    p_expires_at TIMESTAMPTZ
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
BEGIN
    IF p_cpf IS NULL OR p_cpf !~ '^[0-9]{11}$' THEN
        RETURN FALSE;
    END IF;
    IF p_code IS NULL OR p_code !~ '^[0-9]{6}$' THEN
        RETURN FALSE;
    END IF;

    IF EXISTS (
        SELECT 1 FROM public.accountsCitizen
        WHERE cpf = p_cpf AND blockedUntil IS NOT NULL AND blockedUntil > now()
    ) THEN
        RETURN FALSE;
    END IF;

    UPDATE public.accountsCitizen
    SET recoveryCodeHash = crypt(p_code, gen_salt('bf', 8)),
        recoveryCodeExpiresAt = p_expires_at,
        updatedAt = now()
    WHERE cpf = p_cpf
      AND isActive = true
      AND deletedAt IS NULL;

    RETURN FOUND;
END;
$$;

REVOKE ALL ON FUNCTION sosp_security.set_citizen_recovery_code(VARCHAR, VARCHAR, TIMESTAMPTZ) FROM PUBLIC;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sosp_runtime_role') THEN
        GRANT EXECUTE ON FUNCTION sosp_security.set_citizen_recovery_code(VARCHAR, VARCHAR, TIMESTAMPTZ) TO sosp_runtime_role;
    END IF;
END $$;

CREATE OR REPLACE FUNCTION sosp_security.verify_citizen_recovery_code(
    p_cpf VARCHAR,
    p_code VARCHAR
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
    v_stored_hash TEXT;
    v_expires_at TIMESTAMPTZ;
    v_blocked_until TIMESTAMPTZ;
    v_attempts INT;
BEGIN
    IF p_cpf IS NULL OR p_cpf !~ '^[0-9]{11}$' THEN
        RETURN FALSE;
    END IF;
    IF p_code IS NULL OR p_code !~ '^[0-9]{6}$' THEN
        RETURN FALSE;
    END IF;

    SELECT recoveryCodeHash, recoveryCodeExpiresAt, blockedUntil, loginAttempts
    INTO v_stored_hash, v_expires_at, v_blocked_until, v_attempts
    FROM public.accountsCitizen
    WHERE cpf = p_cpf AND isActive = true AND deletedAt IS NULL
    FOR UPDATE;

    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;

    IF v_blocked_until IS NOT NULL AND v_blocked_until > now() THEN
        RETURN FALSE;
    END IF;

    IF v_stored_hash IS NULL OR v_expires_at IS NULL OR now() > v_expires_at THEN
        UPDATE public.accountsCitizen
        SET recoveryCodeHash = NULL, recoveryCodeExpiresAt = NULL, updatedAt = now()
        WHERE cpf = p_cpf;
        RETURN FALSE;
    END IF;

    IF crypt(p_code, v_stored_hash) != v_stored_hash THEN
        IF v_attempts + 1 >= 5 THEN
            UPDATE public.accountsCitizen
            SET loginAttempts = v_attempts + 1,
                blockedUntil = now() + interval '5 minutes',
                recoveryCodeHash = NULL,
                recoveryCodeExpiresAt = NULL,
                updatedAt = now()
            WHERE cpf = p_cpf;
        ELSE
            UPDATE public.accountsCitizen
            SET loginAttempts = v_attempts + 1,
                updatedAt = now()
            WHERE cpf = p_cpf;
        END IF;
        RETURN FALSE;
    END IF;

    UPDATE public.accountsCitizen
    SET loginAttempts = 0, updatedAt = now()
    WHERE cpf = p_cpf;

    RETURN TRUE;
END;
$$;

REVOKE ALL ON FUNCTION sosp_security.verify_citizen_recovery_code(VARCHAR, VARCHAR) FROM PUBLIC;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sosp_runtime_role') THEN
        GRANT EXECUTE ON FUNCTION sosp_security.verify_citizen_recovery_code(VARCHAR, VARCHAR) TO sosp_runtime_role;
    END IF;
END $$;

CREATE OR REPLACE FUNCTION sosp_security.clear_citizen_recovery_code(p_cpf VARCHAR)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
BEGIN
    IF p_cpf IS NULL OR p_cpf !~ '^[0-9]{11}$' THEN
        RETURN FALSE;
    END IF;

    UPDATE public.accountsCitizen
    SET recoveryCodeHash = NULL,
        recoveryCodeExpiresAt = NULL,
        updatedAt = now()
    WHERE cpf = p_cpf;

    RETURN FOUND;
END;
$$;

REVOKE ALL ON FUNCTION sosp_security.clear_citizen_recovery_code(VARCHAR) FROM PUBLIC;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sosp_runtime_role') THEN
        GRANT EXECUTE ON FUNCTION sosp_security.clear_citizen_recovery_code(VARCHAR) TO sosp_runtime_role;
    END IF;
END $$;

CREATE OR REPLACE FUNCTION sosp_security.reset_citizen_password(
    p_cpf VARCHAR,
    p_code VARCHAR,
    p_new_password_hash TEXT
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
    v_stored_hash TEXT;
    v_expires_at TIMESTAMPTZ;
    v_blocked_until TIMESTAMPTZ;
    v_attempts INT;
BEGIN
    IF p_cpf IS NULL OR p_cpf !~ '^[0-9]{11}$' THEN
        RETURN FALSE;
    END IF;
    IF p_code IS NULL OR p_code !~ '^[0-9]{6}$' THEN
        RETURN FALSE;
    END IF;
    IF p_new_password_hash IS NULL OR length(p_new_password_hash) < 10 THEN
        RETURN FALSE;
    END IF;

    SELECT recoveryCodeHash, recoveryCodeExpiresAt, blockedUntil, loginAttempts
    INTO v_stored_hash, v_expires_at, v_blocked_until, v_attempts
    FROM public.accountsCitizen
    WHERE cpf = p_cpf AND isActive = true AND deletedAt IS NULL
    FOR UPDATE;

    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;

    IF v_blocked_until IS NOT NULL AND v_blocked_until > now() THEN
        RETURN FALSE;
    END IF;

    IF v_stored_hash IS NULL OR v_expires_at IS NULL OR now() > v_expires_at THEN
        UPDATE public.accountsCitizen
        SET recoveryCodeHash = NULL, recoveryCodeExpiresAt = NULL, updatedAt = now()
        WHERE cpf = p_cpf;
        RETURN FALSE;
    END IF;

    IF crypt(p_code, v_stored_hash) != v_stored_hash THEN
        IF v_attempts + 1 >= 5 THEN
            UPDATE public.accountsCitizen
            SET loginAttempts = v_attempts + 1,
                blockedUntil = now() + interval '5 minutes',
                recoveryCodeHash = NULL,
                recoveryCodeExpiresAt = NULL,
                updatedAt = now()
            WHERE cpf = p_cpf;
        ELSE
            UPDATE public.accountsCitizen
            SET loginAttempts = v_attempts + 1,
                updatedAt = now()
            WHERE cpf = p_cpf;
        END IF;
        RETURN FALSE;
    END IF;

    UPDATE public.accountsCitizen
    SET passwordHash = p_new_password_hash,
        recoveryCodeHash = NULL,
        recoveryCodeExpiresAt = NULL,
        loginAttempts = 0,
        blockedUntil = NULL,
        updatedAt = now()
    WHERE cpf = p_cpf;

    RETURN TRUE;
END;
$$;

REVOKE ALL ON FUNCTION sosp_security.reset_citizen_password(VARCHAR, VARCHAR, TEXT) FROM PUBLIC;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sosp_runtime_role') THEN
        GRANT EXECUTE ON FUNCTION sosp_security.reset_citizen_password(VARCHAR, VARCHAR, TEXT) TO sosp_runtime_role;
    END IF;
END $$;

COMMIT;
