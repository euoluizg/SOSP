-- ==============================================================================
-- SOSP — ETAPA 4D.2: APLICAÇÃO DE MÍNIMO PRIVILÉGIO DML (DEFINITIVO)
-- Concessão estrita de privilégios para sosp_runtime_role
-- ==============================================================================
-- Regras de Segurança:
-- 1. ZERO TRUNCATE em todas as 38 tabelas (RLS não protege contra TRUNCATE).
-- 2. ZERO REFERENCES em todas as 38 tabelas (evita criação de FKs por roles não autorizadas).
-- 3. ZERO TRIGGER em todas as 38 tabelas (evita bypass de lógica via triggers maliciosos).
-- 4. ZERO MAINTAIN em todas as 38 tabelas.
-- 5. ZERO DELETE em todas as entidades de negócio (proibição de DELETE físico por RN-40).
--    DELETE permitido exclusivamente em entidades efêmeras ('accountsSession' e 'notificationsPushSubscription').
-- 6. Tabelas de log/auditoria (auditEvent, searchQueryLog, attachments, transitions) são APPEND-ONLY (SELECT, INSERT).
-- ==============================================================================

BEGIN;

-- 1. Sequências (auto-incremento e identity)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO sosp_runtime_role;

-- 2. Tabelas de Leitura e Escrita de Negócio (SELECT, INSERT, UPDATE) - Zero DELETE físico (RN-40)
GRANT SELECT, INSERT, UPDATE ON TABLE
    public.accountsCitizen,
    public.accountsInternalUser,
    public.accountsLoginAttempt,
    public.accountsPasswordReset,
    public.catalogAgency,
    public.catalogUnit,
    public.catalogUnitOpeningHour,
    public.catalogNonWorkingDay,
    public.catalogService,
    public.catalogServiceAgency,
    public.catalogUnitService,
    public.catalogServiceStep,
    public.catalogServiceDocument,
    public.catalogFaq,
    public.catalogServiceVersion,
    public.searchSynonym,
    public.guidanceProgress,
    public.guidanceGeneratedPdf,
    public.schedulingSlot,
    public.schedulingAppointment,
    public.schedulingProtocol,
    public.feedbackReview,
    public.feedbackReviewReport,
    public.feedbackQuestion,
    public.notificationsTemplate,
    public.notificationsPreference,
    public.notificationsDelivery,
    public.reportsExport,
    public.auditDataSubjectRequest
TO sosp_runtime_role;

-- 3. Tabelas Efêmeras com suporte a descarte (SELECT, INSERT, UPDATE, DELETE)
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE
    public.accountsSession,
    public.notificationsPushSubscription
TO sosp_runtime_role;

-- 4. Tabelas Imutáveis / Append-Only (SELECT, INSERT) - Zero UPDATE, Zero DELETE
GRANT SELECT, INSERT ON TABLE
    public.searchQueryLog,
    public.schedulingProtocolAttachment,
    public.schedulingProtocolTransition,
    public.auditEvent
TO sosp_runtime_role;

-- 5. Tabelas de Domínio e Controle de Somente Leitura (SELECT)
GRANT SELECT ON TABLE
    public.accountsGender
TO sosp_runtime_role;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'django_migrations') THEN
        EXECUTE 'GRANT SELECT ON TABLE public.django_migrations TO sosp_runtime_role;';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'django_content_type') THEN
        EXECUTE 'GRANT SELECT ON TABLE public.django_content_type TO sosp_runtime_role;';
    END IF;
END;
$$;

-- 6. Garantia Atômica de Security Invoker nas Views Analíticas (PG15+)
ALTER VIEW public.vw_catalogservicesearch SET (security_invoker = true);
ALTER VIEW public.vw_schedulingslotavailability SET (security_invoker = true);

-- 7. Views Analíticas com Security Invoker (SELECT)
GRANT SELECT ON TABLE
    public.vw_catalogservicesearch,
    public.vw_schedulingslotavailability
TO sosp_runtime_role;

COMMIT;
