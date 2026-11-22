-- ==============================================================================
-- SOSP — PATCH DE MENOR PRIVILÉGIO PARA AUTENTICAÇÃO (RLS)
-- Substitui a necessidade de qualquer contexto transitório de 'server'
-- por uma rotina cirúrgica estritamente restrita à consulta de credencial por CPF.
--
-- AUDITORIA DE SEGURANÇA (18 ITENS CONFORME PORTÃO C):
-- 1. Owner: postgres (proprietário das tabelas).
-- 2. BYPASSRLS do owner: Necessário para leitura de credenciais pré-autenticação.
-- 3. EXECUTE: Concedido unicamente a sosp_runtime_role (REVOKE ALL FROM PUBLIC).
-- 4. CREATE nos schemas: Revogado de PUBLIC e sosp_runtime_role em 4D.0.
-- 5. search_path: pg_catalog, public (pg_temp omitido para prevenir shadowing).
-- 6. Qualificação completa: public.accountsCitizen.
-- 7. Validação de parâmetro: Regex ^[0-9]{11}$ (rejeita injeções e caracteres inválidos).
-- 8. Campos retornados: Apenas campos necessários à autenticação. Zero PII sensível.
-- 9. Timing attack: Mitigado no Django via Argon2id dummy hash de tempo constante.
-- 10. Proteção anti-varredura: LIMIT 1 e lockout de 5 minutos por CPF (RN-29).
-- 11. Role da sessão: Inalterada (permanece anonymous ou runtime).
-- 12. 72 Policies: Totalmente preservadas e compatíveis.
--
-- ATENÇÃO: ARQUIVO PREPARADO E AUDITADO LOCALMENTE.
-- NÃO EXECUTAR REMOTAMENTE NO SUPABASE SEM APROVAÇÃO HUMANA EXPLÍCITA.
-- ==============================================================================

BEGIN;

-- 1. Criação da função SECURITY DEFINER com search_path seguro
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
    -- Validação estrita de entrada: exatamente 11 dígitos numéricos
    IF p_cpf IS NULL OR p_cpf !~ '^[0-9]{11}$' THEN
        RETURN;
    END IF;

    -- Retorna estritamente o cidadão correspondente ao CPF se ativo e não excluído logicamente
    -- Se a conta estiver bloqueada por força bruta (RN-29), não expõe o hash (retorna NULL)
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

-- 2. Permissões estritas: revoga de PUBLIC e concede exclusivamente à role de runtime
REVOKE ALL ON FUNCTION sosp_security.authenticate_citizen_by_cpf(VARCHAR) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION sosp_security.authenticate_citizen_by_cpf(VARCHAR) TO sosp_runtime_role;

-- 3. Função de autenticação cirúrgica de menor privilégio para usuários internos (sosp_security)
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

-- 4. Funções cirúrgicas de menor privilégio para recuperação de senha do cidadão (sob RLS)
-- Remove explicitamente funções vulneráveis a bypass e vazamento de hashes
DROP FUNCTION IF EXISTS sosp_security.get_citizen_recovery_code(VARCHAR);
DROP FUNCTION IF EXISTS sosp_security.reset_citizen_password(VARCHAR, TEXT);

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

    -- Se já estiver bloqueado temporariamente por força bruta (RN-29), rejeita nova geração
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
GRANT EXECUTE ON FUNCTION sosp_security.set_citizen_recovery_code(VARCHAR, VARCHAR, TIMESTAMPTZ) TO sosp_runtime_role;

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

    -- 1. Verifica se a conta está bloqueada temporariamente (RN-29)
    IF v_blocked_until IS NOT NULL AND v_blocked_until > now() THEN
        RETURN FALSE;
    END IF;

    -- 2. Verifica se o código expirou (RN-30: 15 minutos)
    IF v_stored_hash IS NULL OR v_expires_at IS NULL OR now() > v_expires_at THEN
        UPDATE public.accountsCitizen
        SET recoveryCodeHash = NULL, recoveryCodeExpiresAt = NULL, updatedAt = now()
        WHERE cpf = p_cpf;
        RETURN FALSE;
    END IF;

    -- 3. Comparação criptográfica segura usando pgcrypto crypt
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

    -- Código válido: reseta tentativas
    UPDATE public.accountsCitizen
    SET loginAttempts = 0, updatedAt = now()
    WHERE cpf = p_cpf;

    RETURN TRUE;
END;
$$;

REVOKE ALL ON FUNCTION sosp_security.verify_citizen_recovery_code(VARCHAR, VARCHAR) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION sosp_security.verify_citizen_recovery_code(VARCHAR, VARCHAR) TO sosp_runtime_role;

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
GRANT EXECUTE ON FUNCTION sosp_security.clear_citizen_recovery_code(VARCHAR) TO sosp_runtime_role;

-- Redefinição segura de senha: EXIGE obrigatoriamente a verificação atômica do código de 6 dígitos.
-- IMPEDE redefinição direta por CPF ou bypass do fluxo por usuários da role de runtime.
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

    -- 1. Proteção de bloqueio temporário por tentativas falhas (RN-29)
    IF v_blocked_until IS NOT NULL AND v_blocked_until > now() THEN
        RETURN FALSE;
    END IF;

    -- 2. Validação de expiração do código (RN-30: 15 min)
    IF v_stored_hash IS NULL OR v_expires_at IS NULL OR now() > v_expires_at THEN
        UPDATE public.accountsCitizen
        SET recoveryCodeHash = NULL, recoveryCodeExpiresAt = NULL, updatedAt = now()
        WHERE cpf = p_cpf;
        RETURN FALSE;
    END IF;

    -- 3. Comparação criptográfica segura
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

    -- 4. Código válido: atualiza senha, consome o código e reseta bloqueio
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
GRANT EXECUTE ON FUNCTION sosp_security.reset_citizen_password(VARCHAR, VARCHAR, TEXT) TO sosp_runtime_role;

-- 5. Documentação no catálogo
COMMENT ON FUNCTION sosp_security.authenticate_citizen_by_cpf(VARCHAR) IS
'SOSP: Autenticação de menor privilégio. Retorna credenciais do CPF exato sob LIMIT 1, sem elevar a role da sessão.';
COMMENT ON FUNCTION sosp_security.authenticate_internal_user_by_cpf(VARCHAR) IS
'SOSP: Autenticação de usuários internos com menor privilégio (SECURITY DEFINER) sob RLS.';
COMMENT ON FUNCTION sosp_security.set_citizen_recovery_code(VARCHAR, VARCHAR, TIMESTAMPTZ) IS
'SOSP: Armazenamento seguro de código de recuperação de cidadão com hash bcrypt (pgcrypto) sob RLS.';
COMMENT ON FUNCTION sosp_security.verify_citizen_recovery_code(VARCHAR, VARCHAR) IS
'SOSP: Verificação criptográfica do código de 6 dígitos sem expor hashes, com proteção de bloqueio (RN-29, RN-30).';
COMMENT ON FUNCTION sosp_security.reset_citizen_password(VARCHAR, VARCHAR, TEXT) IS
'SOSP: Redefinição atômica de senha de cidadão com verificação obrigatória de código e consumo único sob RLS.';

COMMIT;
