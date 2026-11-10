-- ==============================================================================
-- SOSP — ETAPA 4D.2: APLICAÇÃO DE POLÍTICAS DE ROW-LEVEL SECURITY (RLS)
-- Políticas Granulares com Prevenção de Falsificação e Restrição de Autoria
-- Cobre 100% das 38 tabelas do banco de dados (todas com RLS habilitado na 4C.2)
-- ==============================================================================

BEGIN;

-- ------------------------------------------------------------------------------
-- 1. accountsCitizen (Perfil do Cidadão)
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS p_citizen_select ON public.accountsCitizen;
CREATE POLICY p_citizen_select ON public.accountsCitizen
    FOR SELECT TO sosp_runtime_role
    USING (
        id = sosp_security.get_current_citizen_id()
        OR sosp_security.get_current_role() IN ('server', 'admin', 'superadmin')
    );

DROP POLICY IF EXISTS p_citizen_insert ON public.accountsCitizen;
CREATE POLICY p_citizen_insert ON public.accountsCitizen
    FOR INSERT TO sosp_runtime_role
    WITH CHECK (
        -- Auto-cadastro permitido apenas a usuários não autenticados (anônimos) ou administradores
        sosp_security.get_current_role() = 'anonymous'
        OR sosp_security.get_current_role() IN ('admin', 'superadmin')
    );

DROP POLICY IF EXISTS p_citizen_update ON public.accountsCitizen;
CREATE POLICY p_citizen_update ON public.accountsCitizen
    FOR UPDATE TO sosp_runtime_role
    USING (
        id = sosp_security.get_current_citizen_id()
        OR sosp_security.get_current_role() IN ('admin', 'superadmin')
    )
    WITH CHECK (
        id = sosp_security.get_current_citizen_id()
        OR sosp_security.get_current_role() IN ('admin', 'superadmin')
    );

-- ------------------------------------------------------------------------------
-- 2. accountsInternalUser (Usuários Internos)
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS p_internal_user_select ON public.accountsInternalUser;
CREATE POLICY p_internal_user_select ON public.accountsInternalUser
    FOR SELECT TO sosp_runtime_role
    USING (
        id = sosp_security.get_current_internal_user_id()
        OR sosp_security.get_current_role() IN ('admin', 'superadmin')
        OR (
            sosp_security.get_current_role() = 'server'
            AND agencyId = sosp_security.get_current_agency_id()
        )
    );

DROP POLICY IF EXISTS p_internal_user_insert ON public.accountsInternalUser;
CREATE POLICY p_internal_user_insert ON public.accountsInternalUser
    FOR INSERT TO sosp_runtime_role
    WITH CHECK (
        sosp_security.get_current_role() IN ('admin', 'superadmin')
    );

DROP POLICY IF EXISTS p_internal_user_update ON public.accountsInternalUser;
CREATE POLICY p_internal_user_update ON public.accountsInternalUser
    FOR UPDATE TO sosp_runtime_role
    USING (
        id = sosp_security.get_current_internal_user_id()
        OR sosp_security.get_current_role() IN ('admin', 'superadmin')
    );

-- ------------------------------------------------------------------------------
-- 3. accountsSession (Sessões Autenticadas)
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS p_session_all ON public.accountsSession;
CREATE POLICY p_session_all ON public.accountsSession
    FOR ALL TO sosp_runtime_role
    USING (
        subjectId = sosp_security.get_current_citizen_id()
        OR subjectId = sosp_security.get_current_internal_user_id()
        OR sosp_security.get_current_role() IN ('admin', 'superadmin')
    );

-- ------------------------------------------------------------------------------
-- 4. accountsLoginAttempt (Controle de Tentativas / Lockout)
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS p_login_attempt_select ON public.accountsLoginAttempt;
CREATE POLICY p_login_attempt_select ON public.accountsLoginAttempt
    FOR SELECT TO sosp_runtime_role
    USING (true);

DROP POLICY IF EXISTS p_login_attempt_insert ON public.accountsLoginAttempt;
CREATE POLICY p_login_attempt_insert ON public.accountsLoginAttempt
    FOR INSERT TO sosp_runtime_role
    WITH CHECK (true);

-- ------------------------------------------------------------------------------
-- 5. accountsPasswordReset (Recuperação de Senha)
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS p_password_reset_all ON public.accountsPasswordReset;
CREATE POLICY p_password_reset_all ON public.accountsPasswordReset
    FOR ALL TO sosp_runtime_role
    USING (true)
    WITH CHECK (true);

-- ------------------------------------------------------------------------------
-- 6. accountsGender (Domínio / Referência)
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS p_gender_select ON public.accountsGender;
CREATE POLICY p_gender_select ON public.accountsGender
    FOR SELECT TO sosp_runtime_role
    USING (isActive = true OR sosp_security.get_current_role() IN ('server', 'admin', 'superadmin'));

-- ------------------------------------------------------------------------------
-- 7. catalogAgency (Órgãos Públicos)
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS p_agency_select ON public.catalogAgency;
CREATE POLICY p_agency_select ON public.catalogAgency
    FOR SELECT TO sosp_runtime_role
    USING (isActive = true OR sosp_security.get_current_role() IN ('server', 'admin', 'superadmin'));

DROP POLICY IF EXISTS p_agency_modify ON public.catalogAgency;
CREATE POLICY p_agency_modify ON public.catalogAgency
    FOR ALL TO sosp_runtime_role
    USING (sosp_security.get_current_role() IN ('admin', 'superadmin'))
    WITH CHECK (sosp_security.get_current_role() IN ('admin', 'superadmin'));

-- ------------------------------------------------------------------------------
-- 8. catalogUnit (Unidades de Atendimento)
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS p_unit_select ON public.catalogUnit;
CREATE POLICY p_unit_select ON public.catalogUnit
    FOR SELECT TO sosp_runtime_role
    USING (isActive = true OR sosp_security.get_current_role() IN ('server', 'admin', 'superadmin'));

DROP POLICY IF EXISTS p_unit_modify ON public.catalogUnit;
CREATE POLICY p_unit_modify ON public.catalogUnit
    FOR ALL TO sosp_runtime_role
    USING (
        sosp_security.get_current_role() IN ('admin', 'superadmin')
        OR (sosp_security.get_current_role() = 'server' AND agencyId = sosp_security.get_current_agency_id())
    )
    WITH CHECK (
        sosp_security.get_current_role() IN ('admin', 'superadmin')
        OR (sosp_security.get_current_role() = 'server' AND agencyId = sosp_security.get_current_agency_id())
    );

-- ------------------------------------------------------------------------------
-- 9. catalogUnitOpeningHour & catalogNonWorkingDay (Horários e Feriados)
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS p_opening_hour_select ON public.catalogUnitOpeningHour;
CREATE POLICY p_opening_hour_select ON public.catalogUnitOpeningHour
    FOR SELECT TO sosp_runtime_role USING (true);

DROP POLICY IF EXISTS p_opening_hour_modify ON public.catalogUnitOpeningHour;
CREATE POLICY p_opening_hour_modify ON public.catalogUnitOpeningHour
    FOR ALL TO sosp_runtime_role
    USING (
        sosp_security.get_current_role() IN ('admin', 'superadmin')
        OR (
            sosp_security.get_current_role() = 'server'
            AND unitId IN (SELECT id FROM public.catalogUnit WHERE agencyId = sosp_security.get_current_agency_id())
        )
    );

DROP POLICY IF EXISTS p_non_working_day_select ON public.catalogNonWorkingDay;
CREATE POLICY p_non_working_day_select ON public.catalogNonWorkingDay
    FOR SELECT TO sosp_runtime_role USING (true);

DROP POLICY IF EXISTS p_non_working_day_modify ON public.catalogNonWorkingDay;
CREATE POLICY p_non_working_day_modify ON public.catalogNonWorkingDay
    FOR ALL TO sosp_runtime_role
    USING (
        sosp_security.get_current_role() IN ('admin', 'superadmin')
        OR (
            sosp_security.get_current_role() = 'server'
            AND unitId IN (SELECT id FROM public.catalogUnit WHERE agencyId = sosp_security.get_current_agency_id())
        )
    );

-- ------------------------------------------------------------------------------
-- 10. catalogService (Catálogo de Serviços)
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS p_service_select ON public.catalogService;
CREATE POLICY p_service_select ON public.catalogService
    FOR SELECT TO sosp_runtime_role
    USING (
        (deletedAt IS NULL AND status = 'active')
        OR sosp_security.get_current_role() IN ('server', 'admin', 'superadmin')
    );

DROP POLICY IF EXISTS p_service_insert ON public.catalogService;
CREATE POLICY p_service_insert ON public.catalogService
    FOR INSERT TO sosp_runtime_role
    WITH CHECK (
        sosp_security.get_current_role() IN ('admin', 'superadmin')
        OR (
            sosp_security.get_current_role() = 'server'
            AND id IN (SELECT serviceId FROM public.catalogServiceAgency WHERE agencyId = sosp_security.get_current_agency_id())
        )
    );

DROP POLICY IF EXISTS p_service_update ON public.catalogService;
CREATE POLICY p_service_update ON public.catalogService
    FOR UPDATE TO sosp_runtime_role
    USING (
        sosp_security.get_current_role() IN ('admin', 'superadmin')
        OR (
            sosp_security.get_current_role() = 'server'
            AND id IN (SELECT serviceId FROM public.catalogServiceAgency WHERE agencyId = sosp_security.get_current_agency_id())
        )
    );

-- ------------------------------------------------------------------------------
-- 11. catalogServiceAgency & catalogUnitService (Relações de Catálogo)
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS p_service_agency_select ON public.catalogServiceAgency;
CREATE POLICY p_service_agency_select ON public.catalogServiceAgency
    FOR SELECT TO sosp_runtime_role USING (true);

DROP POLICY IF EXISTS p_service_agency_modify ON public.catalogServiceAgency;
CREATE POLICY p_service_agency_modify ON public.catalogServiceAgency
    FOR ALL TO sosp_runtime_role
    USING (sosp_security.get_current_role() IN ('admin', 'superadmin', 'server'));

DROP POLICY IF EXISTS p_unit_service_select ON public.catalogUnitService;
CREATE POLICY p_unit_service_select ON public.catalogUnitService
    FOR SELECT TO sosp_runtime_role USING (true);

DROP POLICY IF EXISTS p_unit_service_modify ON public.catalogUnitService;
CREATE POLICY p_unit_service_modify ON public.catalogUnitService
    FOR ALL TO sosp_runtime_role
    USING (sosp_security.get_current_role() IN ('admin', 'superadmin', 'server'));

-- ------------------------------------------------------------------------------
-- 12. catalogServiceStep & catalogServiceDocument (Etapas e Documentos)
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS p_service_step_select ON public.catalogServiceStep;
CREATE POLICY p_service_step_select ON public.catalogServiceStep
    FOR SELECT TO sosp_runtime_role USING (true);

DROP POLICY IF EXISTS p_service_step_modify ON public.catalogServiceStep;
CREATE POLICY p_service_step_modify ON public.catalogServiceStep
    FOR ALL TO sosp_runtime_role
    USING (sosp_security.get_current_role() IN ('admin', 'superadmin', 'server'));

DROP POLICY IF EXISTS p_service_document_select ON public.catalogServiceDocument;
CREATE POLICY p_service_document_select ON public.catalogServiceDocument
    FOR SELECT TO sosp_runtime_role USING (true);

DROP POLICY IF EXISTS p_service_document_modify ON public.catalogServiceDocument;
CREATE POLICY p_service_document_modify ON public.catalogServiceDocument
    FOR ALL TO sosp_runtime_role
    USING (sosp_security.get_current_role() IN ('admin', 'superadmin', 'server'));

-- ------------------------------------------------------------------------------
-- 13. catalogFaq & catalogServiceVersion (FAQ e Versionamento)
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS p_faq_select ON public.catalogFaq;
CREATE POLICY p_faq_select ON public.catalogFaq
    FOR SELECT TO sosp_runtime_role
    USING (isActive = true OR sosp_security.get_current_role() IN ('server', 'admin', 'superadmin'));

DROP POLICY IF EXISTS p_faq_modify ON public.catalogFaq;
CREATE POLICY p_faq_modify ON public.catalogFaq
    FOR ALL TO sosp_runtime_role
    USING (sosp_security.get_current_role() IN ('admin', 'superadmin', 'server'));

DROP POLICY IF EXISTS p_service_version_select ON public.catalogServiceVersion;
CREATE POLICY p_service_version_select ON public.catalogServiceVersion
    FOR SELECT TO sosp_runtime_role
    USING (sosp_security.get_current_role() IN ('server', 'admin', 'superadmin'));

DROP POLICY IF EXISTS p_service_version_insert ON public.catalogServiceVersion;
CREATE POLICY p_service_version_insert ON public.catalogServiceVersion
    FOR INSERT TO sosp_runtime_role
    WITH CHECK (sosp_security.get_current_role() IN ('server', 'admin', 'superadmin'));

-- ------------------------------------------------------------------------------
-- 14. searchSynonym & searchQueryLog (Busca)
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS p_synonym_select ON public.searchSynonym;
CREATE POLICY p_synonym_select ON public.searchSynonym
    FOR SELECT TO sosp_runtime_role USING (true);

DROP POLICY IF EXISTS p_synonym_modify ON public.searchSynonym;
CREATE POLICY p_synonym_modify ON public.searchSynonym
    FOR ALL TO sosp_runtime_role
    USING (sosp_security.get_current_role() IN ('admin', 'superadmin'));

DROP POLICY IF EXISTS p_search_log_insert ON public.searchQueryLog;
CREATE POLICY p_search_log_insert ON public.searchQueryLog
    FOR INSERT TO sosp_runtime_role WITH CHECK (true);

DROP POLICY IF EXISTS p_search_log_select ON public.searchQueryLog;
CREATE POLICY p_search_log_select ON public.searchQueryLog
    FOR SELECT TO sosp_runtime_role
    USING (sosp_security.get_current_role() IN ('admin', 'superadmin'));

-- ------------------------------------------------------------------------------
-- 15. guidanceProgress & guidanceGeneratedPdf (Orientação)
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS p_guidance_all ON public.guidanceProgress;
CREATE POLICY p_guidance_all ON public.guidanceProgress
    FOR ALL TO sosp_runtime_role
    USING (
        citizenId = sosp_security.get_current_citizen_id()
        OR sosp_security.get_current_role() IN ('admin', 'superadmin')
    )
    WITH CHECK (
        citizenId = sosp_security.get_current_citizen_id()
        OR sosp_security.get_current_role() IN ('admin', 'superadmin')
    );

DROP POLICY IF EXISTS p_guidance_pdf_all ON public.guidanceGeneratedPdf;
CREATE POLICY p_guidance_pdf_all ON public.guidanceGeneratedPdf
    FOR ALL TO sosp_runtime_role
    USING (
        citizenId = sosp_security.get_current_citizen_id()
        OR sosp_security.get_current_role() IN ('admin', 'superadmin')
    )
    WITH CHECK (
        citizenId = sosp_security.get_current_citizen_id()
        OR sosp_security.get_current_role() IN ('admin', 'superadmin')
    );

-- ------------------------------------------------------------------------------
-- 16. schedulingSlot, schedulingAppointment & schedulingProtocol
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS p_slot_select ON public.schedulingSlot;
CREATE POLICY p_slot_select ON public.schedulingSlot
    FOR SELECT TO sosp_runtime_role USING (true);

DROP POLICY IF EXISTS p_slot_modify ON public.schedulingSlot;
CREATE POLICY p_slot_modify ON public.schedulingSlot
    FOR ALL TO sosp_runtime_role
    USING (sosp_security.get_current_role() IN ('server', 'admin', 'superadmin', 'citizen'));

DROP POLICY IF EXISTS p_appointment_select ON public.schedulingAppointment;
CREATE POLICY p_appointment_select ON public.schedulingAppointment
    FOR SELECT TO sosp_runtime_role
    USING (
        citizenId = sosp_security.get_current_citizen_id()
        OR (
            sosp_security.get_current_role() = 'server'
            AND unitId IN (SELECT id FROM public.catalogUnit WHERE agencyId = sosp_security.get_current_agency_id())
        )
        OR sosp_security.get_current_role() IN ('admin', 'superadmin')
    );

DROP POLICY IF EXISTS p_appointment_insert ON public.schedulingAppointment;
CREATE POLICY p_appointment_insert ON public.schedulingAppointment
    FOR INSERT TO sosp_runtime_role
    WITH CHECK (
        citizenId = sosp_security.get_current_citizen_id()
        OR sosp_security.get_current_role() IN ('server', 'admin', 'superadmin')
    );

DROP POLICY IF EXISTS p_appointment_update ON public.schedulingAppointment;
CREATE POLICY p_appointment_update ON public.schedulingAppointment
    FOR UPDATE TO sosp_runtime_role
    USING (
        citizenId = sosp_security.get_current_citizen_id()
        OR (
            sosp_security.get_current_role() = 'server'
            AND unitId IN (SELECT id FROM public.catalogUnit WHERE agencyId = sosp_security.get_current_agency_id())
        )
        OR sosp_security.get_current_role() IN ('admin', 'superadmin')
    )
    WITH CHECK (
        citizenId = sosp_security.get_current_citizen_id()
        OR (
            sosp_security.get_current_role() = 'server'
            AND unitId IN (SELECT id FROM public.catalogUnit WHERE agencyId = sosp_security.get_current_agency_id())
        )
        OR sosp_security.get_current_role() IN ('admin', 'superadmin')
    );

DROP POLICY IF EXISTS p_protocol_select ON public.schedulingProtocol;
CREATE POLICY p_protocol_select ON public.schedulingProtocol
    FOR SELECT TO sosp_runtime_role
    USING (
        citizenId = sosp_security.get_current_citizen_id()
        OR (
            sosp_security.get_current_role() = 'server'
            AND appointmentId IN (
                SELECT id FROM public.schedulingAppointment
                WHERE unitId IN (SELECT id FROM public.catalogUnit WHERE agencyId = sosp_security.get_current_agency_id())
            )
        )
        OR sosp_security.get_current_role() IN ('admin', 'superadmin')
    );

DROP POLICY IF EXISTS p_protocol_insert ON public.schedulingProtocol;
CREATE POLICY p_protocol_insert ON public.schedulingProtocol
    FOR INSERT TO sosp_runtime_role
    WITH CHECK (
        citizenId = sosp_security.get_current_citizen_id()
        OR sosp_security.get_current_role() IN ('server', 'admin', 'superadmin')
    );

DROP POLICY IF EXISTS p_protocol_update ON public.schedulingProtocol;
CREATE POLICY p_protocol_update ON public.schedulingProtocol
    FOR UPDATE TO sosp_runtime_role
    USING (
        citizenId = sosp_security.get_current_citizen_id()
        OR (
            sosp_security.get_current_role() = 'server'
            AND appointmentId IN (
                SELECT id FROM public.schedulingAppointment
                WHERE unitId IN (SELECT id FROM public.catalogUnit WHERE agencyId = sosp_security.get_current_agency_id())
            )
        )
        OR sosp_security.get_current_role() IN ('admin', 'superadmin')
    );

-- ------------------------------------------------------------------------------
-- 17. schedulingProtocolAttachment & schedulingProtocolTransition (Imutáveis)
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS p_protocol_att_select ON public.schedulingProtocolAttachment;
CREATE POLICY p_protocol_att_select ON public.schedulingProtocolAttachment
    FOR SELECT TO sosp_runtime_role
    USING (
        protocolId IN (SELECT id FROM public.schedulingProtocol WHERE citizenId = sosp_security.get_current_citizen_id())
        OR sosp_security.get_current_role() IN ('server', 'admin', 'superadmin')
    );

DROP POLICY IF EXISTS p_protocol_att_insert ON public.schedulingProtocolAttachment;
CREATE POLICY p_protocol_att_insert ON public.schedulingProtocolAttachment
    FOR INSERT TO sosp_runtime_role
    WITH CHECK (
        protocolId IN (SELECT id FROM public.schedulingProtocol WHERE citizenId = sosp_security.get_current_citizen_id())
        OR sosp_security.get_current_role() IN ('server', 'admin', 'superadmin')
    );

DROP POLICY IF EXISTS p_protocol_trans_select ON public.schedulingProtocolTransition;
CREATE POLICY p_protocol_trans_select ON public.schedulingProtocolTransition
    FOR SELECT TO sosp_runtime_role
    USING (
        protocolId IN (SELECT id FROM public.schedulingProtocol WHERE citizenId = sosp_security.get_current_citizen_id())
        OR sosp_security.get_current_role() IN ('server', 'admin', 'superadmin')
    );

DROP POLICY IF EXISTS p_protocol_trans_insert ON public.schedulingProtocolTransition;
CREATE POLICY p_protocol_trans_insert ON public.schedulingProtocolTransition
    FOR INSERT TO sosp_runtime_role
    WITH CHECK (sosp_security.get_current_role() IN ('server', 'admin', 'superadmin'));

-- ------------------------------------------------------------------------------
-- 18. feedbackReview, feedbackReviewReport & feedbackQuestion (Feedback)
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS p_feedback_review_select ON public.feedbackReview;
CREATE POLICY p_feedback_review_select ON public.feedbackReview
    FOR SELECT TO sosp_runtime_role USING (true);

DROP POLICY IF EXISTS p_feedback_review_insert ON public.feedbackReview;
CREATE POLICY p_feedback_review_insert ON public.feedbackReview
    FOR INSERT TO sosp_runtime_role
    WITH CHECK (citizenId = sosp_security.get_current_citizen_id());

DROP POLICY IF EXISTS p_feedback_review_update ON public.feedbackReview;
CREATE POLICY p_feedback_review_update ON public.feedbackReview
    FOR UPDATE TO sosp_runtime_role
    USING (sosp_security.get_current_role() IN ('admin', 'superadmin'));

DROP POLICY IF EXISTS p_feedback_report_all ON public.feedbackReviewReport;
CREATE POLICY p_feedback_report_all ON public.feedbackReviewReport
    FOR ALL TO sosp_runtime_role
    USING (sosp_security.get_current_role() IN ('admin', 'superadmin', 'server'))
    WITH CHECK (true);

DROP POLICY IF EXISTS p_feedback_question_select ON public.feedbackQuestion;
CREATE POLICY p_feedback_question_select ON public.feedbackQuestion
    FOR SELECT TO sosp_runtime_role USING (true);

DROP POLICY IF EXISTS p_feedback_question_modify ON public.feedbackQuestion;
CREATE POLICY p_feedback_question_modify ON public.feedbackQuestion
    FOR ALL TO sosp_runtime_role
    USING (sosp_security.get_current_role() IN ('admin', 'superadmin'));

-- ------------------------------------------------------------------------------
-- 19. Notificações (templates, preferences, delivery, push)
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS p_notif_tpl_select ON public.notificationsTemplate;
CREATE POLICY p_notif_tpl_select ON public.notificationsTemplate
    FOR SELECT TO sosp_runtime_role USING (true);

DROP POLICY IF EXISTS p_notif_tpl_modify ON public.notificationsTemplate;
CREATE POLICY p_notif_tpl_modify ON public.notificationsTemplate
    FOR ALL TO sosp_runtime_role
    USING (sosp_security.get_current_role() IN ('admin', 'superadmin'));

DROP POLICY IF EXISTS p_notif_pref_all ON public.notificationsPreference;
CREATE POLICY p_notif_pref_all ON public.notificationsPreference
    FOR ALL TO sosp_runtime_role
    USING (
        citizenId = sosp_security.get_current_citizen_id()
        OR sosp_security.get_current_role() IN ('admin', 'superadmin')
    )
    WITH CHECK (
        citizenId = sosp_security.get_current_citizen_id()
        OR sosp_security.get_current_role() IN ('admin', 'superadmin')
    );

DROP POLICY IF EXISTS p_notif_deliv_select ON public.notificationsDelivery;
CREATE POLICY p_notif_deliv_select ON public.notificationsDelivery
    FOR SELECT TO sosp_runtime_role
    USING (
        citizenId = sosp_security.get_current_citizen_id()
        OR sosp_security.get_current_role() IN ('admin', 'superadmin')
    );

DROP POLICY IF EXISTS p_notif_deliv_modify ON public.notificationsDelivery;
CREATE POLICY p_notif_deliv_modify ON public.notificationsDelivery
    FOR ALL TO sosp_runtime_role
    USING (sosp_security.get_current_role() IN ('server', 'admin', 'superadmin'));

DROP POLICY IF EXISTS p_notif_push_all ON public.notificationsPushSubscription;
CREATE POLICY p_notif_push_all ON public.notificationsPushSubscription
    FOR ALL TO sosp_runtime_role
    USING (
        citizenId = sosp_security.get_current_citizen_id()
        OR sosp_security.get_current_role() IN ('admin', 'superadmin')
    )
    WITH CHECK (
        citizenId = sosp_security.get_current_citizen_id()
        OR sosp_security.get_current_role() IN ('admin', 'superadmin')
    );

-- ------------------------------------------------------------------------------
-- 20. reportsExport (Relatórios)
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS p_reports_export_all ON public.reportsExport;
CREATE POLICY p_reports_export_all ON public.reportsExport
    FOR ALL TO sosp_runtime_role
    USING (sosp_security.get_current_role() IN ('server', 'admin', 'superadmin'))
    WITH CHECK (sosp_security.get_current_role() IN ('server', 'admin', 'superadmin'));

-- ------------------------------------------------------------------------------
-- 21. auditEvent (Trilha Imutável de Auditoria — Anti-Falsificação de Autoria)
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS p_audit_insert ON public.auditEvent;
CREATE POLICY p_audit_insert ON public.auditEvent
    FOR INSERT TO sosp_runtime_role
    WITH CHECK (
        -- Se cidadão: actorType DEVE ser 'citizen' e actorId idêntico ao do cidadão
        (sosp_security.get_current_role() = 'citizen'
         AND actorType = 'citizen'
         AND actorId = sosp_security.get_current_citizen_id())
        OR
        -- Se servidor: actorType DEVE ser 'servant' e actorId idêntico ao do servidor
        (sosp_security.get_current_role() = 'server'
         AND actorType = 'servant'
         AND actorId = sosp_security.get_current_internal_user_id())
        OR
        -- Se administrador: actorType pode ser de gestão
        (sosp_security.get_current_role() IN ('admin', 'superadmin'))
        OR
        -- Se anônimo: actorType deve ser 'anonymous' e actorId nulo
        (sosp_security.get_current_role() = 'anonymous'
         AND actorType = 'anonymous'
         AND actorId IS NULL)
    );

DROP POLICY IF EXISTS p_audit_select ON public.auditEvent;
CREATE POLICY p_audit_select ON public.auditEvent
    FOR SELECT TO sosp_runtime_role
    USING (
        sosp_security.get_current_role() IN ('admin', 'superadmin')
        OR (
            sosp_security.get_current_role() = 'server'
            AND actorId = sosp_security.get_current_internal_user_id()
        )
    );

-- ------------------------------------------------------------------------------
-- 22. auditDataSubjectRequest (LGPD)
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS p_lgpd_select ON public.auditDataSubjectRequest;
CREATE POLICY p_lgpd_select ON public.auditDataSubjectRequest
    FOR SELECT TO sosp_runtime_role
    USING (
        citizenId = sosp_security.get_current_citizen_id()
        OR sosp_security.get_current_role() IN ('admin', 'superadmin')
    );

DROP POLICY IF EXISTS p_lgpd_insert ON public.auditDataSubjectRequest;
CREATE POLICY p_lgpd_insert ON public.auditDataSubjectRequest
    FOR INSERT TO sosp_runtime_role
    WITH CHECK (
        citizenId = sosp_security.get_current_citizen_id()
        OR sosp_security.get_current_role() IN ('admin', 'superadmin')
    );

DROP POLICY IF EXISTS p_lgpd_update ON public.auditDataSubjectRequest;
CREATE POLICY p_lgpd_update ON public.auditDataSubjectRequest
    FOR UPDATE TO sosp_runtime_role
    USING (sosp_security.get_current_role() IN ('admin', 'superadmin'));

-- ------------------------------------------------------------------------------
-- 23. Tabelas Django (Somente Leitura)
-- ------------------------------------------------------------------------------
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'django_migrations') THEN
        DROP POLICY IF EXISTS p_django_migrations_select ON public.django_migrations;
        CREATE POLICY p_django_migrations_select ON public.django_migrations
            FOR SELECT TO sosp_runtime_role USING (true);
    END IF;
    IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public' AND tablename = 'django_content_type') THEN
        DROP POLICY IF EXISTS p_django_content_type_select ON public.django_content_type;
        CREATE POLICY p_django_content_type_select ON public.django_content_type
            FOR SELECT TO sosp_runtime_role USING (true);
    END IF;
END;
$$;

COMMIT;
