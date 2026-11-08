-- ==============================================================================
-- SOSP — ETAPA 4D.2: ROLLBACK CIRÚRGICO DE POLÍTICAS RLS E CONTEXTO DE SEGURANÇA
-- Remoção Estrita Objeto a Objeto (SEM DROP SCHEMA CASCADE / USO DE RESTRICT)
-- ==============================================================================

BEGIN;

-- 1. Remoção de políticas RLS em accountsCitizen
DROP POLICY IF EXISTS p_citizen_select ON public.accountsCitizen;
DROP POLICY IF EXISTS p_citizen_insert ON public.accountsCitizen;
DROP POLICY IF EXISTS p_citizen_update ON public.accountsCitizen;

-- 2. accountsInternalUser
DROP POLICY IF EXISTS p_internal_user_select ON public.accountsInternalUser;
DROP POLICY IF EXISTS p_internal_user_insert ON public.accountsInternalUser;
DROP POLICY IF EXISTS p_internal_user_update ON public.accountsInternalUser;

-- 3. accountsSession, loginAttempt, passwordReset, gender
DROP POLICY IF EXISTS p_session_all ON public.accountsSession;
DROP POLICY IF EXISTS p_login_attempt_select ON public.accountsLoginAttempt;
DROP POLICY IF EXISTS p_login_attempt_insert ON public.accountsLoginAttempt;
DROP POLICY IF EXISTS p_password_reset_all ON public.accountsPasswordReset;
DROP POLICY IF EXISTS p_gender_select ON public.accountsGender;

-- 4. catalog (agency, unit, hours, nonworking, service, relations, steps, docs, faq, version)
DROP POLICY IF EXISTS p_agency_select ON public.catalogAgency;
DROP POLICY IF EXISTS p_agency_modify ON public.catalogAgency;
DROP POLICY IF EXISTS p_unit_select ON public.catalogUnit;
DROP POLICY IF EXISTS p_unit_modify ON public.catalogUnit;
DROP POLICY IF EXISTS p_opening_hour_select ON public.catalogUnitOpeningHour;
DROP POLICY IF EXISTS p_opening_hour_modify ON public.catalogUnitOpeningHour;
DROP POLICY IF EXISTS p_non_working_day_select ON public.catalogNonWorkingDay;
DROP POLICY IF EXISTS p_non_working_day_modify ON public.catalogNonWorkingDay;
DROP POLICY IF EXISTS p_service_select ON public.catalogService;
DROP POLICY IF EXISTS p_service_insert ON public.catalogService;
DROP POLICY IF EXISTS p_service_update ON public.catalogService;
DROP POLICY IF EXISTS p_service_agency_select ON public.catalogServiceAgency;
DROP POLICY IF EXISTS p_service_agency_modify ON public.catalogServiceAgency;
DROP POLICY IF EXISTS p_unit_service_select ON public.catalogUnitService;
DROP POLICY IF EXISTS p_unit_service_modify ON public.catalogUnitService;
DROP POLICY IF EXISTS p_service_step_select ON public.catalogServiceStep;
DROP POLICY IF EXISTS p_service_step_modify ON public.catalogServiceStep;
DROP POLICY IF EXISTS p_service_document_select ON public.catalogServiceDocument;
DROP POLICY IF EXISTS p_service_document_modify ON public.catalogServiceDocument;
DROP POLICY IF EXISTS p_faq_select ON public.catalogFaq;
DROP POLICY IF EXISTS p_faq_modify ON public.catalogFaq;
DROP POLICY IF EXISTS p_service_version_select ON public.catalogServiceVersion;
DROP POLICY IF EXISTS p_service_version_insert ON public.catalogServiceVersion;

-- 5. search (synonyms, query logs)
DROP POLICY IF EXISTS p_synonym_select ON public.searchSynonym;
DROP POLICY IF EXISTS p_synonym_modify ON public.searchSynonym;
DROP POLICY IF EXISTS p_search_log_insert ON public.searchQueryLog;
DROP POLICY IF EXISTS p_search_log_select ON public.searchQueryLog;

-- 6. guidance (progress, pdf)
DROP POLICY IF EXISTS p_guidance_all ON public.guidanceProgress;
DROP POLICY IF EXISTS p_guidance_pdf_all ON public.guidanceGeneratedPdf;

-- 7. scheduling (slots, appointments, protocols, attachments, transitions)
DROP POLICY IF EXISTS p_slot_select ON public.schedulingSlot;
DROP POLICY IF EXISTS p_slot_modify ON public.schedulingSlot;
DROP POLICY IF EXISTS p_appointment_select ON public.schedulingAppointment;
DROP POLICY IF EXISTS p_appointment_insert ON public.schedulingAppointment;
DROP POLICY IF EXISTS p_appointment_update ON public.schedulingAppointment;
DROP POLICY IF EXISTS p_protocol_select ON public.schedulingProtocol;
DROP POLICY IF EXISTS p_protocol_insert ON public.schedulingProtocol;
DROP POLICY IF EXISTS p_protocol_update ON public.schedulingProtocol;
DROP POLICY IF EXISTS p_protocol_att_select ON public.schedulingProtocolAttachment;
DROP POLICY IF EXISTS p_protocol_att_insert ON public.schedulingProtocolAttachment;
DROP POLICY IF EXISTS p_protocol_trans_select ON public.schedulingProtocolTransition;
DROP POLICY IF EXISTS p_protocol_trans_insert ON public.schedulingProtocolTransition;

-- 8. feedback
DROP POLICY IF EXISTS p_feedback_review_select ON public.feedbackReview;
DROP POLICY IF EXISTS p_feedback_review_insert ON public.feedbackReview;
DROP POLICY IF EXISTS p_feedback_review_update ON public.feedbackReview;
DROP POLICY IF EXISTS p_feedback_report_all ON public.feedbackReviewReport;
DROP POLICY IF EXISTS p_feedback_question_select ON public.feedbackQuestion;
DROP POLICY IF EXISTS p_feedback_question_modify ON public.feedbackQuestion;

-- 9. notifications
DROP POLICY IF EXISTS p_notif_tpl_select ON public.notificationsTemplate;
DROP POLICY IF EXISTS p_notif_tpl_modify ON public.notificationsTemplate;
DROP POLICY IF EXISTS p_notif_pref_all ON public.notificationsPreference;
DROP POLICY IF EXISTS p_notif_deliv_select ON public.notificationsDelivery;
DROP POLICY IF EXISTS p_notif_deliv_modify ON public.notificationsDelivery;
DROP POLICY IF EXISTS p_notif_push_all ON public.notificationsPushSubscription;

-- 10. reports
DROP POLICY IF EXISTS p_reports_export_all ON public.reportsExport;

-- 11. audit
DROP POLICY IF EXISTS p_audit_insert ON public.auditEvent;
DROP POLICY IF EXISTS p_audit_select ON public.auditEvent;
DROP POLICY IF EXISTS p_lgpd_select ON public.auditDataSubjectRequest;
DROP POLICY IF EXISTS p_lgpd_insert ON public.auditDataSubjectRequest;
DROP POLICY IF EXISTS p_lgpd_update ON public.auditDataSubjectRequest;

-- 12. django tables
DROP POLICY IF EXISTS p_django_migrations_select ON public.django_migrations;
DROP POLICY IF EXISTS p_django_content_type_select ON public.django_content_type;

-- 13. Remoção Explícita de Funções do Schema sosp_security (Sem Cascade)
DROP FUNCTION IF EXISTS sosp_security.get_current_role();
DROP FUNCTION IF EXISTS sosp_security.get_current_agency_id();
DROP FUNCTION IF EXISTS sosp_security.get_current_internal_user_id();
DROP FUNCTION IF EXISTS sosp_security.get_current_citizen_id();
DROP FUNCTION IF EXISTS sosp_security.is_context_valid();
DROP FUNCTION IF EXISTS sosp_security.clear_request_context();
DROP FUNCTION IF EXISTS sosp_security.set_request_context(UUID, VARCHAR, UUID, BIGINT, UUID, VARCHAR);
DROP FUNCTION IF EXISTS sosp_security.set_request_context(UUID, VARCHAR, UUID, BIGINT, VARCHAR);
DROP FUNCTION IF EXISTS sosp_security.compute_expected_hmac(TEXT, TEXT, TEXT, BIGINT, TEXT);
DROP FUNCTION IF EXISTS sosp_security.compute_expected_hmac(TEXT, TEXT, TEXT, BIGINT);
DROP FUNCTION IF EXISTS sosp_security.set_hmac_secret(TEXT);
DROP FUNCTION IF EXISTS sosp_security.compute_raw_hmac(TEXT, TEXT);

-- 14. Remoção Explícita das Tabelas de Segurança
DROP TABLE IF EXISTS sosp_security.used_nonces;
DROP TABLE IF EXISTS sosp_security.hmac_secret;

-- 15. Remoção do Schema com RESTRICT (Falha com erro se houver qualquer dependência inesperada)
DROP SCHEMA IF EXISTS sosp_security RESTRICT;

COMMIT;
