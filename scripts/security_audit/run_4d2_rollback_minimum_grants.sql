-- ==============================================================================
-- SOSP — ETAPA 4D.2: ROLLBACK DE PRIVILÉGIOS DML
-- Revoga todos os privilégios concedidos a sosp_runtime_role no schema public
-- Retorna o banco exatamente ao estado seguro pós-4D.1 (zero privilégios DML)
-- ==============================================================================

BEGIN;

-- 1. Revoga acesso a sequências
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM sosp_runtime_role;

-- 2. Revoga acesso a todas as 38 tabelas do schema public
REVOKE ALL ON TABLE
    public.accountsCitizen,
    public.accountsGender,
    public.accountsInternalUser,
    public.accountsSession,
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
    public.searchQueryLog,
    public.searchSynonym,
    public.guidanceProgress,
    public.guidanceGeneratedPdf,
    public.schedulingSlot,
    public.schedulingAppointment,
    public.schedulingProtocol,
    public.schedulingProtocolAttachment,
    public.schedulingProtocolTransition,
    public.feedbackReview,
    public.feedbackReviewReport,
    public.feedbackQuestion,
    public.notificationsTemplate,
    public.notificationsPreference,
    public.notificationsDelivery,
    public.notificationsPushSubscription,
    public.reportsExport,
    public.auditEvent,
    public.auditDataSubjectRequest,
    public.django_migrations,
    public.django_content_type
FROM sosp_runtime_role;

-- 3. Revoga acesso às views analíticas
REVOKE ALL ON TABLE
    public.vw_catalogservicesearch,
    public.vw_schedulingslotavailability
FROM sosp_runtime_role;

COMMIT;
