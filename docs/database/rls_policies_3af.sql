-- =============================================================================
-- SOSP — Sistema de Orientação para Serviços Públicos
-- Políticas de Row Level Security (RLS) para Demonstração (3AF / 2026)
--
-- Equipe Oficial:
--   - Product Owner: Mozart Melo
--   - Tech Lead & Back-end: Arthur Franco
--   - Front-end, UI/UX & QA: Luiz Gustavo
--
-- Contexto:
--   O arquivo `schema.sql` já habilitou RLS em todas as 36 tabelas (ENABLE ROW LEVEL SECURITY).
--   Sem políticas explícitas, o PostgreSQL adota "Default Deny" para roles não-owner.
--   Este arquivo complementa a autorização SQL, criando as políticas necessárias
--   para demonstrar os papéis `sosp_leitor_role` e `sosp_operador_role`, bem como
--   o endurecimento de Views com `security_invoker = true`.
--
-- Regras de Segurança:
--   - Nenhuma política permissiva aberta (USING true) sobre tabelas com dados pessoais;
--   - Isolamento de registros inativos e excluídos logicamente (Soft Delete / RN-40);
--   - Defesa em Profundidade: GRANT de tabela é pré-requisito, RLS filtra as linhas;
--   - Views configuradas com security_invoker = true para impedir bypass de RLS.
-- =============================================================================

BEGIN;

  -- ---------------------------------------------------------------------------
  -- 0. ENDURECIMENTO DE VIEWS CONTRA BYPASS DE RLS (security_invoker = true)
  -- ---------------------------------------------------------------------------
  -- No PostgreSQL 15+, views por padrão executam como o proprietário (security_definer),
  -- o que anularia o RLS das tabelas base para usuários leitores.
  -- Ao marcar security_invoker = true, o PostgreSQL avalia os privilégios e as
  -- políticas de RLS da sessão chamadora (invoker), bloqueando o vazamento de rascunhos.
  -- ---------------------------------------------------------------------------

  ALTER VIEW vw_catalogServiceSearch SET (security_invoker = true);
  ALTER VIEW vw_schedulingSlotAvailability SET (security_invoker = true);

  -- ---------------------------------------------------------------------------
  -- 1. POLÍTICAS DE RLS: CATÁLOGO DE SERVIÇOS (catalogService)
  -- ---------------------------------------------------------------------------

  -- O leitor público só enxerga serviços que estão ATIVOS e NÃO EXCLUÍDOS.
  DROP POLICY IF EXISTS p_leitor_catalog_service_select ON catalogService;
  CREATE POLICY p_leitor_catalog_service_select
    ON catalogService
    FOR SELECT
    TO sosp_leitor_role
    USING (status = 'active' AND deletedAt IS NULL);

  -- O operador operacional enxerga também serviços em rascunho (draft) para validação,
  -- mas nunca serviços excluídos logicamente (deletedAt IS NOT NULL).
  DROP POLICY IF EXISTS p_operador_catalog_service_select ON catalogService;
  CREATE POLICY p_operador_catalog_service_select
    ON catalogService
    FOR SELECT
    TO sosp_operador_role
    USING (deletedAt IS NULL);

  -- ---------------------------------------------------------------------------
  -- 2. POLÍTICAS DE RLS: ÓRGÃOS E UNIDADES (catalogAgency & catalogUnit)
  -- ---------------------------------------------------------------------------

  DROP POLICY IF EXISTS p_catalog_agency_select ON catalogAgency;
  CREATE POLICY p_catalog_agency_select
    ON catalogAgency
    FOR SELECT
    TO sosp_leitor_role, sosp_operador_role
    USING (isActive = true AND deletedAt IS NULL);

  DROP POLICY IF EXISTS p_catalog_unit_select ON catalogUnit;
  CREATE POLICY p_catalog_unit_select
    ON catalogUnit
    FOR SELECT
    TO sosp_leitor_role, sosp_operador_role
    USING (isActive = true AND deletedAt IS NULL);

  DROP POLICY IF EXISTS p_catalog_opening_hour_select ON catalogUnitOpeningHour;
  CREATE POLICY p_catalog_opening_hour_select
    ON catalogUnitOpeningHour
    FOR SELECT
    TO sosp_leitor_role, sosp_operador_role
    USING (true);

  DROP POLICY IF EXISTS p_catalog_non_working_day_select ON catalogNonWorkingDay;
  CREATE POLICY p_catalog_non_working_day_select
    ON catalogNonWorkingDay
    FOR SELECT
    TO sosp_leitor_role, sosp_operador_role
    USING (true);

  DROP POLICY IF EXISTS p_catalog_service_agency_select ON catalogServiceAgency;
  CREATE POLICY p_catalog_service_agency_select
    ON catalogServiceAgency
    FOR SELECT
    TO sosp_leitor_role, sosp_operador_role
    USING (true);

  DROP POLICY IF EXISTS p_catalog_unit_service_select ON catalogUnitService;
  CREATE POLICY p_catalog_unit_service_select
    ON catalogUnitService
    FOR SELECT
    TO sosp_leitor_role, sosp_operador_role
    USING (isActive = true);

  DROP POLICY IF EXISTS p_catalog_service_step_select ON catalogServiceStep;
  CREATE POLICY p_catalog_service_step_select
    ON catalogServiceStep
    FOR SELECT
    TO sosp_leitor_role, sosp_operador_role
    USING (true);

  DROP POLICY IF EXISTS p_catalog_service_document_select ON catalogServiceDocument;
  CREATE POLICY p_catalog_service_document_select
    ON catalogServiceDocument
    FOR SELECT
    TO sosp_leitor_role, sosp_operador_role
    USING (true);

  DROP POLICY IF EXISTS p_catalog_service_version_select ON catalogServiceVersion;
  CREATE POLICY p_catalog_service_version_select
    ON catalogServiceVersion
    FOR SELECT
    TO sosp_leitor_role, sosp_operador_role
    USING (true);

  -- ---------------------------------------------------------------------------
  -- 3. POLÍTICAS DE RLS: PERGUNTAS FREQUENTES (catalogFaq)
  -- ---------------------------------------------------------------------------

  -- O leitor só consulta FAQs ativas
  DROP POLICY IF EXISTS p_leitor_catalog_faq_select ON catalogFaq;
  CREATE POLICY p_leitor_catalog_faq_select
    ON catalogFaq
    FOR SELECT
    TO sosp_leitor_role
    USING (isActive = true);

  -- O operador consulta todas as FAQs e pode criar/atualizar com validação
  DROP POLICY IF EXISTS p_operador_catalog_faq_select ON catalogFaq;
  CREATE POLICY p_operador_catalog_faq_select
    ON catalogFaq
    FOR SELECT
    TO sosp_operador_role
    USING (true);

  DROP POLICY IF EXISTS p_operador_catalog_faq_insert ON catalogFaq;
  CREATE POLICY p_operador_catalog_faq_insert
    ON catalogFaq
    FOR INSERT
    TO sosp_operador_role
    WITH CHECK (char_length(question) >= 5 AND char_length(answer) >= 5);

  DROP POLICY IF EXISTS p_operador_catalog_faq_update ON catalogFaq;
  CREATE POLICY p_operador_catalog_faq_update
    ON catalogFaq
    FOR UPDATE
    TO sosp_operador_role
    USING (true)
    WITH CHECK (char_length(question) >= 5 AND char_length(answer) >= 5);

  -- ---------------------------------------------------------------------------
  -- 4. POLÍTICAS DE RLS: LOGS ANÔNIMOS DE BUSCA (searchQueryLog)
  -- ---------------------------------------------------------------------------

  DROP POLICY IF EXISTS p_operador_search_query_log_select ON searchQueryLog;
  CREATE POLICY p_operador_search_query_log_select
    ON searchQueryLog
    FOR SELECT
    TO sosp_operador_role
    USING (true);

  DROP POLICY IF EXISTS p_operador_search_query_log_insert ON searchQueryLog;
  CREATE POLICY p_operador_search_query_log_insert
    ON searchQueryLog
    FOR INSERT
    TO sosp_operador_role
    WITH CHECK (resultCount >= 0);

  -- ---------------------------------------------------------------------------
  -- 5. POLÍTICAS DE RLS: SINÔNIMOS DE BUSCA (searchSynonym)
  -- ---------------------------------------------------------------------------

  -- Leitor pode consultar sinônimos ativos (utilizado também pela view vw_catalogServiceSearch)
  DROP POLICY IF EXISTS p_leitor_search_synonym_select ON searchSynonym;
  CREATE POLICY p_leitor_search_synonym_select
    ON searchSynonym
    FOR SELECT
    TO sosp_leitor_role
    USING (isActive = true);

  DROP POLICY IF EXISTS p_operador_search_synonym_select ON searchSynonym;
  CREATE POLICY p_operador_search_synonym_select
    ON searchSynonym
    FOR SELECT
    TO sosp_operador_role
    USING (true);

  DROP POLICY IF EXISTS p_operador_search_synonym_insert ON searchSynonym;
  CREATE POLICY p_operador_search_synonym_insert
    ON searchSynonym
    FOR INSERT
    TO sosp_operador_role
    WITH CHECK (cardinality(synonyms) > 0);

  DROP POLICY IF EXISTS p_operador_search_synonym_update ON searchSynonym;
  CREATE POLICY p_operador_search_synonym_update
    ON searchSynonym
    FOR UPDATE
    TO sosp_operador_role
    USING (true)
    WITH CHECK (cardinality(synonyms) > 0);

  -- ---------------------------------------------------------------------------
  -- 6. POLÍTICAS DE RLS: SLOTS DE AGENDAMENTO (schedulingSlot)
  -- ---------------------------------------------------------------------------
  -- Necessário para consulta de disponibilidade pública na view vw_schedulingSlotAvailability
  -- sem expor dados nominais de agendamento do cidadão (que residem em schedulingAppointment).
  -- ---------------------------------------------------------------------------

  DROP POLICY IF EXISTS p_scheduling_slot_select ON schedulingSlot;
  CREATE POLICY p_scheduling_slot_select
    ON schedulingSlot
    FOR SELECT
    TO sosp_leitor_role, sosp_operador_role
    USING (true);

COMMIT;
