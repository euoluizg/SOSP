-- Ensaio do par migration Django + função institucional em banco PostgreSQL isolado.
-- Executar somente após accounts.0002 e o patch 04, como role administrativa.

DO $$
DECLARE
    function_oid oid;
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM public.django_migrations
        WHERE app = 'accounts' AND name = '0002_add_gender_description_and_unit_to_accounts'
    ) THEN
        RAISE EXCEPTION 'Migration accounts.0002 ausente';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'accountsinternaluser' AND column_name = 'unitid'
    ) OR NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE schemaname = 'public' AND tablename = 'accountsinternaluser'
          AND indexname = 'idxaccountsinternaluserunit'
    ) THEN
        RAISE EXCEPTION 'Coluna ou índice unitId ausente';
    END IF;

    SELECT p.oid INTO function_oid
    FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'sosp_security'
      AND p.proname = 'authenticate_internal_user_by_cpf'
      AND pg_get_function_identity_arguments(p.oid) = 'p_cpf character varying';

    IF function_oid IS NULL THEN
        RAISE EXCEPTION 'Função institucional ausente';
    END IF;

    IF NOT (SELECT prosecdef FROM pg_proc WHERE oid = function_oid)
       OR NOT (SELECT 'search_path=pg_catalog, public' = ANY(proconfig)
               FROM pg_proc WHERE oid = function_oid)
       OR pg_get_function_result(function_oid) NOT LIKE '%must_change_password boolean%'
    THEN
        RAISE EXCEPTION 'Assinatura ou configuração de segurança da função incorreta';
    END IF;

    IF EXISTS (
        SELECT 1 FROM pg_proc p, LATERAL aclexplode(p.proacl) acl
        WHERE p.oid = function_oid AND acl.grantee = 0 AND acl.privilege_type = 'EXECUTE'
    ) OR NOT has_function_privilege(
        'sosp_runtime_app', function_oid, 'EXECUTE'
    ) OR NOT pg_has_role('sosp_runtime_app', 'sosp_runtime_role', 'USAGE') THEN
        RAISE EXCEPTION 'Grants da função ou herança de role incorretos';
    END IF;

    IF NOT (SELECT relrowsecurity FROM pg_class WHERE oid = 'public.accountsinternaluser'::regclass) THEN
        RAISE EXCEPTION 'RLS de accountsInternalUser desabilitada';
    END IF;
END $$;

BEGIN;
INSERT INTO public.accountsInternalUser
    (cpf, fullName, email, registrationNumber, role, passwordHash)
VALUES
    ('33366699957', 'Servidor Sintetico', 'local@example.test', 'SSP-LOCAL', 'server', 'synthetic-hash');
GRANT SELECT ON public.accountsInternalUser TO sosp_runtime_role;
SET ROLE sosp_runtime_app;
DO $$
BEGIN
    IF (SELECT count(*) FROM public.accountsInternalUser) <> 0 THEN
        RAISE EXCEPTION 'Runtime enxergou diretamente a conta protegida por RLS';
    END IF;
    IF (SELECT count(*) FROM sosp_security.authenticate_internal_user_by_cpf('33366699957')
        WHERE role = 'server' AND must_change_password IS TRUE) <> 1 THEN
        RAISE EXCEPTION 'Função institucional não encontrou a conta sintética';
    END IF;
    IF (SELECT count(*) FROM sosp_security.authenticate_internal_user_by_cpf('333.666.999-57')) <> 0 THEN
        RAISE EXCEPTION 'Função institucional aceitou CPF fora do formato estrito';
    END IF;
END $$;
RESET ROLE;
ROLLBACK;
