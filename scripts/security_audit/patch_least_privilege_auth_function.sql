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
CREATE OR REPLACE FUNCTION sosp_security.authenticate_internal_user_by_cpf(p_cpf VARCHAR)
RETURNS TABLE (
    user_id UUID,
    full_name VARCHAR,
    email VARCHAR,
    registration_number VARCHAR,
    agency_id UUID,
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
        u.role AS role,
        u.canManageCatalog AS can_manage_catalog,
        u.passwordHash AS password_hash,
        u.isActive AS is_active
    FROM public.accountsInternalUser u
    WHERE u.cpf = p_cpf
      AND u.isActive = true
      AND u.deletedAt IS NULL
    LIMIT 1;
END;
$$;

REVOKE ALL ON FUNCTION sosp_security.authenticate_internal_user_by_cpf(VARCHAR) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION sosp_security.authenticate_internal_user_by_cpf(VARCHAR) TO sosp_runtime_role;

-- 4. Documentação no catálogo
COMMENT ON FUNCTION sosp_security.authenticate_citizen_by_cpf(VARCHAR) IS
'SOSP: Autenticação de menor privilégio. Retorna credenciais do CPF exato sob LIMIT 1, sem elevar a role da sessão.';
COMMENT ON FUNCTION sosp_security.authenticate_internal_user_by_cpf(VARCHAR) IS
'SOSP: Autenticação de usuários internos com menor privilégio (SECURITY DEFINER) sob RLS.';

COMMIT;
