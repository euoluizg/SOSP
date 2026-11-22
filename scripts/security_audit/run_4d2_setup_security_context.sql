-- ==============================================================================
-- SOSP — ETAPA 4D.2: CONFIGURAÇÃO DO SCHEMA E CONTEXTO DE SEGURANÇA (DEFINITIVO)
-- Arquitetura Criptográfica de Contexto Selado com Expiração Temporal e Anti-Replay
-- ==============================================================================

BEGIN;

-- 1. Extensão pgcrypto (instalada em extensions ou public)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'extensions') THEN
        CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA extensions;
    ELSE
        CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;
    END IF;
END;
$$;

-- 2. Criação e isolamento do schema sosp_security
CREATE SCHEMA IF NOT EXISTS sosp_security;
REVOKE ALL ON SCHEMA sosp_security FROM PUBLIC;
GRANT USAGE ON SCHEMA sosp_security TO sosp_runtime_role;

-- 3. Tabela para o segredo criptográfico HMAC (exclusiva para o banco, separada de Django SECRET_KEY)
CREATE TABLE IF NOT EXISTS sosp_security.hmac_secret (
    id INT PRIMARY KEY DEFAULT 1,
    secret_key TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_single_secret_row CHECK (id = 1)
);

REVOKE ALL ON TABLE sosp_security.hmac_secret FROM PUBLIC, sosp_runtime_role, sosp_runtime_app;

-- 4. Tabela de Nonces consumidos para Anti-Replay estrito entre transações
CREATE TABLE IF NOT EXISTS sosp_security.used_nonces (
    nonce UUID PRIMARY KEY,
    expires_at BIGINT NOT NULL,
    consumed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_used_nonces_exp ON sosp_security.used_nonces (expires_at);

REVOKE ALL ON TABLE sosp_security.used_nonces FROM PUBLIC, sosp_runtime_role, sosp_runtime_app;

-- 5. Função interna para calcular HMAC-SHA256
CREATE OR REPLACE FUNCTION sosp_security.compute_raw_hmac(p_data TEXT, p_key TEXT)
RETURNS TEXT
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = extensions, public, pg_temp
AS $$
BEGIN
    RETURN encode(hmac(p_data::bytea, p_key::bytea, 'sha256'), 'hex');
END;
$$;

REVOKE ALL ON FUNCTION sosp_security.compute_raw_hmac(TEXT, TEXT) FROM PUBLIC, sosp_runtime_role, sosp_runtime_app;

-- 6. Função administrativa para configurar o segredo (chamada apenas por postgres)
CREATE OR REPLACE FUNCTION sosp_security.set_hmac_secret(p_secret TEXT)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = sosp_security, pg_catalog, pg_temp
AS $$
BEGIN
    IF p_secret IS NULL OR length(trim(p_secret)) < 32 THEN
        RAISE EXCEPTION 'O segredo HMAC deve possuir no mínimo 32 caracteres criptográficos.';
    END IF;

    INSERT INTO sosp_security.hmac_secret (id, secret_key, created_at)
    VALUES (1, p_secret, now())
    ON CONFLICT (id) DO UPDATE
    SET secret_key = EXCLUDED.secret_key,
        created_at = now();
END;
$$;

REVOKE ALL ON FUNCTION sosp_security.set_hmac_secret(TEXT) FROM PUBLIC, sosp_runtime_role, sosp_runtime_app;

-- 7. Função interna para calcular o HMAC esperado para um contexto com expiração temporal e nonce
CREATE OR REPLACE FUNCTION sosp_security.compute_expected_hmac(
    p_user_id TEXT,
    p_role TEXT,
    p_agency_id TEXT,
    p_expires_at BIGINT,
    p_nonce TEXT
)
RETURNS TEXT
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = sosp_security, pg_catalog, pg_temp
AS $$
DECLARE
    v_secret TEXT;
    v_payload TEXT;
BEGIN
    SELECT secret_key INTO v_secret FROM sosp_security.hmac_secret WHERE id = 1;
    IF v_secret IS NULL THEN
        RETURN NULL;
    END IF;

    v_payload := coalesce(p_user_id, '') || ':' ||
                 coalesce(p_role, '') || ':' ||
                 coalesce(p_agency_id, '') || ':' ||
                 coalesce(p_expires_at::text, '') || ':' ||
                 coalesce(p_nonce, '');
    RETURN sosp_security.compute_raw_hmac(v_payload, v_secret);
END;
$$;

REVOKE ALL ON FUNCTION sosp_security.compute_expected_hmac(TEXT, TEXT, TEXT, BIGINT, TEXT) FROM PUBLIC, sosp_runtime_role, sosp_runtime_app;

-- 8. Função de definição de contexto da requisição com validação temporal e Anti-Replay
CREATE OR REPLACE FUNCTION sosp_security.set_request_context(
    p_user_id UUID,
    p_role VARCHAR,
    p_agency_id UUID,
    p_expires_at BIGINT,
    p_nonce UUID,
    p_signature VARCHAR
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = sosp_security, pg_catalog, pg_temp
AS $$
DECLARE
    v_expected TEXT;
    v_now_epoch BIGINT;
    v_uid_str TEXT := coalesce(p_user_id::text, '');
    v_role_str TEXT := coalesce(p_role::text, 'anonymous');
    v_aid_str TEXT := coalesce(p_agency_id::text, '');
    v_nonce_str TEXT := coalesce(p_nonce::text, '');
BEGIN
    -- 1. Validação temporal rigorosa (Anti-Replay)
    v_now_epoch := extract(epoch from now())::BIGINT;

    IF p_expires_at IS NULL OR p_expires_at < v_now_epoch THEN
        -- Token expirado
        PERFORM sosp_security.clear_request_context();
        RETURN FALSE;
    END IF;

    -- Rejeita expiração maior que 120 segundos no futuro (janela máxima de transação)
    IF p_expires_at > (v_now_epoch + 120) THEN
        PERFORM sosp_security.clear_request_context();
        RETURN FALSE;
    END IF;

    -- 2. Anti-Replay: Validação de Nonce de uso único
    IF p_nonce IS NULL THEN
        PERFORM sosp_security.clear_request_context();
        RETURN FALSE;
    END IF;

    BEGIN
        INSERT INTO sosp_security.used_nonces (nonce, expires_at)
        VALUES (p_nonce, p_expires_at);
    EXCEPTION WHEN unique_violation THEN
        -- Replay detectado: nonce já utilizado em transação anterior!
        PERFORM sosp_security.clear_request_context();
        RETURN FALSE;
    END;

    -- Prune opportunista de nonces expirados
    DELETE FROM sosp_security.used_nonces WHERE expires_at < v_now_epoch;

    -- 3. Validação da assinatura HMAC
    v_expected := sosp_security.compute_expected_hmac(v_uid_str, v_role_str, v_aid_str, p_expires_at, v_nonce_str);

    IF v_expected IS NOT NULL AND p_signature IS NOT NULL AND p_signature = v_expected THEN
        PERFORM set_config('sosp.current_user_id', v_uid_str, false);
        PERFORM set_config('sosp.current_role', v_role_str, false);
        PERFORM set_config('sosp.current_agency_id', v_aid_str, false);
        PERFORM set_config('sosp.context_expires_at', p_expires_at::text, false);
        PERFORM set_config('sosp.context_nonce', v_nonce_str, false);
        PERFORM set_config('sosp.context_signature', p_signature, false);
        RETURN TRUE;
    ELSE
        PERFORM sosp_security.clear_request_context();
        RETURN FALSE;
    END IF;
END;
$$;

REVOKE ALL ON FUNCTION sosp_security.set_request_context(UUID, VARCHAR, UUID, BIGINT, UUID, VARCHAR) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION sosp_security.set_request_context(UUID, VARCHAR, UUID, BIGINT, UUID, VARCHAR) TO sosp_runtime_role;

-- 9. Função para limpar o contexto explicitamente (obrigatória ao término de cada transação/requisição)
CREATE OR REPLACE FUNCTION sosp_security.clear_request_context()
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
BEGIN
    PERFORM set_config('sosp.current_user_id', '', false);
    PERFORM set_config('sosp.current_role', 'anonymous', false);
    PERFORM set_config('sosp.current_agency_id', '', false);
    PERFORM set_config('sosp.context_expires_at', '', false);
    PERFORM set_config('sosp.context_nonce', '', false);
    PERFORM set_config('sosp.context_signature', '', false);
END;
$$;

REVOKE ALL ON FUNCTION sosp_security.clear_request_context() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION sosp_security.clear_request_context() TO sosp_runtime_role;

-- 10. Função de verificação criptográfica dinâmica de validade do contexto
CREATE OR REPLACE FUNCTION sosp_security.is_context_valid()
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
STABLE
SET search_path = sosp_security, pg_catalog, pg_temp
AS $$
DECLARE
    v_uid TEXT;
    v_role TEXT;
    v_aid TEXT;
    v_exp_str TEXT;
    v_nonce_str TEXT;
    v_exp BIGINT;
    v_sig TEXT;
    v_expected TEXT;
    v_now_epoch BIGINT;
BEGIN
    v_uid := current_setting('sosp.current_user_id', true);
    v_role := current_setting('sosp.current_role', true);
    v_aid := current_setting('sosp.current_agency_id', true);
    v_exp_str := current_setting('sosp.context_expires_at', true);
    v_nonce_str := current_setting('sosp.context_nonce', true);
    v_sig := current_setting('sosp.context_signature', true);

    IF v_sig IS NULL OR v_sig = '' OR v_exp_str IS NULL OR v_exp_str = '' OR v_nonce_str IS NULL OR v_nonce_str = '' THEN
        RETURN FALSE;
    END IF;

    v_exp := v_exp_str::BIGINT;
    v_now_epoch := extract(epoch from now())::BIGINT;

    -- Se o token expirou no meio da transação, invalida
    IF v_exp < v_now_epoch THEN
        RETURN FALSE;
    END IF;

    v_expected := sosp_security.compute_expected_hmac(coalesce(v_uid, ''), coalesce(v_role, ''), coalesce(v_aid, ''), v_exp, v_nonce_str);
    RETURN (v_expected IS NOT NULL AND v_sig = v_expected);
END;
$$;

REVOKE ALL ON FUNCTION sosp_security.is_context_valid() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION sosp_security.is_context_valid() TO sosp_runtime_role;

-- 11. Funções auxiliares para políticas RLS
CREATE OR REPLACE FUNCTION sosp_security.get_current_citizen_id()
RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
STABLE
SET search_path = sosp_security, pg_catalog, pg_temp
AS $$
BEGIN
    IF sosp_security.is_context_valid() AND current_setting('sosp.current_role', true) = 'citizen' THEN
        RETURN nullif(current_setting('sosp.current_user_id', true), '')::UUID;
    END IF;
    RETURN NULL;
END;
$$;

REVOKE ALL ON FUNCTION sosp_security.get_current_citizen_id() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION sosp_security.get_current_citizen_id() TO sosp_runtime_role;

CREATE OR REPLACE FUNCTION sosp_security.get_current_internal_user_id()
RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
STABLE
SET search_path = sosp_security, pg_catalog, pg_temp
AS $$
BEGIN
    IF sosp_security.is_context_valid() AND current_setting('sosp.current_role', true) IN ('server', 'admin', 'superadmin') THEN
        RETURN nullif(current_setting('sosp.current_user_id', true), '')::UUID;
    END IF;
    RETURN NULL;
END;
$$;

REVOKE ALL ON FUNCTION sosp_security.get_current_internal_user_id() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION sosp_security.get_current_internal_user_id() TO sosp_runtime_role;

CREATE OR REPLACE FUNCTION sosp_security.get_current_agency_id()
RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
STABLE
SET search_path = sosp_security, pg_catalog, pg_temp
AS $$
BEGIN
    IF sosp_security.is_context_valid() THEN
        RETURN nullif(current_setting('sosp.current_agency_id', true), '')::UUID;
    END IF;
    RETURN NULL;
END;
$$;

REVOKE ALL ON FUNCTION sosp_security.get_current_agency_id() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION sosp_security.get_current_agency_id() TO sosp_runtime_role;

CREATE OR REPLACE FUNCTION sosp_security.get_current_role()
RETURNS VARCHAR
LANGUAGE plpgsql
SECURITY DEFINER
STABLE
SET search_path = sosp_security, pg_catalog, pg_temp
AS $$
BEGIN
    IF sosp_security.is_context_valid() THEN
        RETURN current_setting('sosp.current_role', true);
    END IF;
    RETURN 'anonymous';
END;
$$;

REVOKE ALL ON FUNCTION sosp_security.get_current_role() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION sosp_security.get_current_role() TO sosp_runtime_role;

COMMIT;
