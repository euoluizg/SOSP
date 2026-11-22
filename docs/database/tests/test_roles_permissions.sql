-- =============================================================================
-- SOSP — Sistema de Orientação para Serviços Públicos
-- Bateria de Testes Automatizados de Permissões e RLS (3AF / 2026)
--
-- Equipe Oficial:
--   - Product Owner: Mozart Melo
--   - Tech Lead & Back-end: Arthur Franco
--   - Front-end, UI/UX & QA: Luiz Gustavo
--
-- Regras de Execução e Confiabilidade:
--   - ON_ERROR_STOP ativado para abortar imediatamente em caso de erro;
--   - Proteção estrita contra execução acidental em ambientes de produção/Supabase;
--   - Eliminação de manipuladores WHEN OTHERS genéricos: apenas exceções esperadas
--     específicas (insufficient_privilege, with_check_option_violation) são capturadas;
--   - Qualquer operação indevidamente permitida lança RAISE EXCEPTION e falha a suíte;
--   - Validação programática de contagem e visibilidade através de blocos PL/pgSQL;
--   - Teste de isolamento de rascunhos em Views com security_invoker = true;
--   - Teste de herança transitiva de privilégios (INHERIT) no operador.
-- =============================================================================

\set ON_ERROR_STOP on

-- =============================================================================
-- SALVAGUARDA DE SEGURANÇA: BLOQUEIO CONTRA EXECUÇÃO NO SUPABASE / PRODUÇÃO
-- =============================================================================
DO $$
DECLARE
  v_db text := current_database();
BEGIN
  -- Permite apenas bancos de teste descartáveis
  IF v_db NOT ILIKE '%test%' AND v_db NOT ILIKE '%local%' AND v_db NOT ILIKE '%sosp_isolated%' THEN
    RAISE EXCEPTION 'BLOQUEIO DE SEGURANÇA: Este script de teste contém TRUNCATE CASCADE e NÃO pode ser executado no banco "%"! Ele deve rodar exclusivamente em bancos locais ou descartáveis cujo nome contenha "test", "local" ou "sosp_isolated".', v_db;
  END IF;

  -- Impede execução com credenciais de administração remota Supabase
  IF current_user = 'supabase_admin' THEN
    RAISE EXCEPTION 'BLOQUEIO DE SEGURANÇA: Detectado usuário "supabase_admin". Execução abortada para prevenir perda de dados!';
  END IF;

  RAISE NOTICE 'Ambiente seguro validado com sucesso: banco "%" (descartável/local).', v_db;
END
$$;

-- =============================================================================
-- FASE 0: PREPARAÇÃO DE DADOS DE TESTE (EXECUTADO COMO PROPRIETÁRIO / DBA)
-- =============================================================================

\echo '----------------------------------------------------------------------'
\echo 'FASE 0: INICIALIZAÇÃO DE DADOS DE TESTE (DBA / PROPRIETÁRIO)'
\echo '----------------------------------------------------------------------'

-- Limpa dados prévios de teste de forma controlada
TRUNCATE TABLE 
  catalogServiceAgency, 
  catalogUnitService, 
  catalogService, 
  catalogUnit, 
  catalogAgency, 
  accountsCitizen, 
  accountsGender, 
  searchQueryLog, 
  catalogFaq, 
  searchSynonym, 
  schedulingSlot 
CASCADE;

-- 1. Insere Gênero e Cidadão de Testes (Dado Pessoal Sensível - LGPD / RS-01)
INSERT INTO accountsGender (id, name) 
VALUES ('11111111-1111-1111-1111-111111111111', 'Feminino');

INSERT INTO accountsCitizen (
  id, cpf, fullName, birthDate, email, phone, passwordHash, passwordSalt,
  genderId, motherName, zipCode, street, neighborhood, city, state, addressNumber
) VALUES (
  '22222222-2222-2222-2222-222222222222', '12345678901', 'Maria da Silva', '1990-05-15',
  'maria.silva@exemplo.com', '82999998888', 'argon2id_hash_teste', 'salt_teste',
  '11111111-1111-1111-1111-111111111111', 'Ana da Silva', '57000000',
  'Rua das Flores', 'Centro', 'Maceio', 'AL', '100'
);

-- 2. Insere Órgão e Unidade
INSERT INTO catalogAgency (id, name, acronym, sphere)
VALUES ('33333333-3333-3333-3333-333333333333', 'Secretaria de Saude', 'SESAU', 'state');

INSERT INTO catalogUnit (id, agencyId, name, zipCode, street, neighborhood, city, state, addressNumber)
VALUES ('44444444-4444-4444-4444-444444444444', '33333333-3333-3333-3333-333333333333', 'Central Ja Centro', '57000000', 'Rua do Comercio', 'Centro', 'Maceio', 'AL', '123');

-- 3. Insere 1 Serviço Ativo e 1 Serviço em Rascunho (Draft)
INSERT INTO catalogService (id, name, category, detailedDescription, eligibility, isFree, averageDeadlineDays, channel, status)
VALUES 
  ('55555555-5555-5555-5555-555555555551', 'Emissao de Cartao SUS', 'health', 'Descricao detalhada do servico', 'Todos os cidadaos', true, 1, 'inPerson', 'active'),
  ('55555555-5555-5555-5555-555555555552', 'Servico Piloto Rascunho', 'health', 'Rascunho interno nao publicado', 'Servidores apenas', true, 5, 'inPerson', 'draft');

-- Vínculo serviço-órgão
INSERT INTO catalogServiceAgency (serviceId, agencyId)
VALUES ('55555555-5555-5555-5555-555555555551', '33333333-3333-3333-3333-333333333333');

-- 4. Insere Sinônimo de Busca ativo
INSERT INTO searchSynonym (term, synonyms, isActive)
VALUES ('sus', ARRAY['cartao do sus', 'saude publica'], true);

-- 5. Insere Slot de Agendamento
INSERT INTO schedulingSlot (id, unitId, slotDate, startsAt, endsAt, capacity, bookedCount)
VALUES ('66666666-6666-6666-6666-666666666666', '44444444-4444-4444-4444-444444444444', CURRENT_DATE + INTERVAL '1 day', '08:00', '08:30', 10, 2);

-- 6. Insere 1 FAQ Ativa e 1 FAQ Inativa
INSERT INTO catalogFaq (question, answer, category, isActive)
VALUES 
  ('Quais documentos levar?', 'Documento oficial com foto e comprovante de residencia.', 'documents', true),
  ('Pergunta em revisao interna?', 'Resposta temporaria de homologacao.', 'health', false);

\echo '>> Dados de teste inseridos com sucesso.'
\echo ''

-- =============================================================================
-- FASE 1: TESTES COM A CONTA LEITOR (sosp_leitor_3af)
-- =============================================================================

\echo '----------------------------------------------------------------------'
\echo 'FASE 1: TESTES COM PAPEL LEITOR (sosp_leitor_3af)'
\echo '----------------------------------------------------------------------'
SET ROLE sosp_leitor_3af;
SELECT current_user AS usuario_atual, session_user AS usuario_sessao;

-- Cenário A: Leitura permitida em tabela de catálogo público
\echo '>>> [CENÁRIO A] Leitura permitida em catalogAgency:'
DO $$
DECLARE
  v_acronym varchar;
BEGIN
  SELECT acronym INTO v_acronym FROM catalogAgency WHERE id = '33333333-3333-3333-3333-333333333333';
  IF v_acronym <> 'SESAU' THEN
    RAISE EXCEPTION 'FALHA [Cenário A]: Leitor não conseguiu recuperar a sigla SESAU!';
  END IF;
  RAISE NOTICE 'SUCESSO: Leitor consultou catalogAgency com sucesso (sigla: %).', v_acronym;
END
$$;

-- Cenário G.1: RLS em catalogService (filtro de rascunhos direto na tabela)
\echo '>>> [CENÁRIO G.1] RLS em catalogService (esperado: exatamente 1 ativo, 0 drafts):'
DO $$
DECLARE
  v_total int;
  v_drafts int;
BEGIN
  SELECT count(*) INTO v_total FROM catalogService;
  SELECT count(*) INTO v_drafts FROM catalogService WHERE status = 'draft';
  IF v_drafts > 0 THEN
    RAISE EXCEPTION 'FALHA DE RLS [Cenário G.1]: Leitor visualizou % serviço(s) em rascunho!', v_drafts;
  END IF;
  IF v_total <> 1 THEN
    RAISE EXCEPTION 'FALHA DE RLS [Cenário G.1]: Esperado 1 serviço ativo, encontrados %!', v_total;
  END IF;
  RAISE NOTICE 'SUCESSO: RLS filtrou rascunhos diretamente na tabela (total visível: 1, drafts: 0).';
END
$$;

-- Cenário G.3: RLS em View com security_invoker = true (zero bypass de RLS)
\echo '>>> [CENÁRIO G.3] View vw_catalogServiceSearch com security_invoker = true:'
DO $$
DECLARE
  v_drafts_in_view int;
  v_total_in_view int;
BEGIN
  SELECT count(*) INTO v_total_in_view FROM vw_catalogServiceSearch;
  SELECT count(*) INTO v_drafts_in_view FROM vw_catalogServiceSearch WHERE status = 'draft';
  IF v_drafts_in_view > 0 THEN
    RAISE EXCEPTION 'FALHA DE SEGURANÇA EM VIEW: vw_catalogServiceSearch vazou % rascunho(s) para o leitor!', v_drafts_in_view;
  END IF;
  IF v_total_in_view <> 1 THEN
    RAISE EXCEPTION 'FALHA EM VIEW: Esperado 1 serviço ativo na view, encontrados %!', v_total_in_view;
  END IF;
  RAISE NOTICE 'SUCESSO: View com security_invoker respeitou RLS e não expôs serviços em rascunho.';
END
$$;

-- Cenário G.4: View vw_schedulingSlotAvailability com security_invoker = true
\echo '>>> [CENÁRIO G.4] View vw_schedulingSlotAvailability consultada com sucesso pelo leitor:'
DO $$
DECLARE
  v_slots_count int;
BEGIN
  SELECT count(*) INTO v_slots_count FROM vw_schedulingSlotAvailability;
  IF v_slots_count <> 1 THEN
    RAISE EXCEPTION 'FALHA EM VIEW [Cenário G.4]: Esperado 1 slot disponível, encontrados %!', v_slots_count;
  END IF;
  RAISE NOTICE 'SUCESSO: Leitor consultou disponibilidade de slots na view com security_invoker (total: %).', v_slots_count;
END
$$;

-- Cenário B: Tentativa de inserção negada
\echo '>>> [CENÁRIO B] Tentativa de INSERT em catalogService (esperado: permission denied):'
DO $$
BEGIN
  INSERT INTO catalogService (id, name, category, detailedDescription, eligibility, isFree, averageDeadlineDays, channel, status)
  VALUES ('55555555-5555-5555-5555-555555555599', 'Servico Proibido', 'health', 'Descricao', 'Ninguem', true, 1, 'inPerson', 'active');
  RAISE EXCEPTION 'FALHA DE SEGURANÇA [Cenário B]: O leitor conseguiu inserir serviço no catálogo!';
EXCEPTION
  WHEN insufficient_privilege THEN
    RAISE NOTICE 'SUCESSO [Cenário B]: Inserção bloqueada por permissão insuficiente: %', SQLERRM;
END
$$;

-- Cenário C: Tentativa de atualização negada
\echo '>>> [CENÁRIO C] Tentativa de UPDATE em catalogAgency (esperado: permission denied):'
DO $$
BEGIN
  UPDATE catalogAgency SET name = 'Nome Alterado Hacker' WHERE id = '33333333-3333-3333-3333-333333333333';
  RAISE EXCEPTION 'FALHA DE SEGURANÇA [Cenário C]: O leitor conseguiu atualizar órgão do catálogo!';
EXCEPTION
  WHEN insufficient_privilege THEN
    RAISE NOTICE 'SUCESSO [Cenário C]: Atualização bloqueada por permissão insuficiente: %', SQLERRM;
END
$$;

-- Cenário E.1: Tentativa de leitura de dados pessoais em accountsCitizen
\echo '>>> [CENÁRIO E.1] Tentativa de leitura de dados pessoais em accountsCitizen (esperado: permission denied):'
DO $$
BEGIN
  PERFORM * FROM accountsCitizen;
  RAISE EXCEPTION 'FALHA DE SEGURANÇA [Cenário E.1]: O leitor conseguiu ler dados pessoais de cidadãos!';
EXCEPTION
  WHEN insufficient_privilege THEN
    RAISE NOTICE 'SUCESSO [Cenário E.1]: Consulta a dados pessoais bloqueada por permissão insuficiente: %', SQLERRM;
END
$$;

-- Cenário F.1: Tentativa de criação de tabela DDL
\echo '>>> [CENÁRIO F.1] Tentativa de CREATE TABLE como leitor (esperado: permission denied for schema public):'
DO $$
BEGIN
  EXECUTE 'CREATE TABLE tabela_teste_leitor (id int)';
  RAISE EXCEPTION 'FALHA DE SEGURANÇA [Cenário F.1]: O leitor conseguiu criar tabela no schema public!';
EXCEPTION
  WHEN insufficient_privilege THEN
    RAISE NOTICE 'SUCESSO [Cenário F.1]: Criação de tabela bloqueada por permissão insuficiente no schema: %', SQLERRM;
END
$$;

RESET ROLE;

-- =============================================================================
-- FASE 2: TESTES COM A CONTA OPERADOR (sosp_operador_3af)
-- =============================================================================

\echo '----------------------------------------------------------------------'
\echo 'FASE 2: TESTES COM PAPEL OPERADOR (sosp_operador_3af)'
\echo '----------------------------------------------------------------------'
SET ROLE sosp_operador_3af;
SELECT current_user AS usuario_atual, session_user AS usuario_sessao;

-- Cenário H: Validação de Herança de Permissões (INHERIT)
\echo '>>> [CENÁRIO H] Leitura de catálogo herdada de sosp_leitor_role:'
DO $$
DECLARE
  v_services_count int;
  v_drafts_count int;
BEGIN
  -- O operador herda SELECT em catalogService e enxerga ativos E drafts (RLS do operador)
  SELECT count(*) INTO v_services_count FROM catalogService;
  SELECT count(*) INTO v_drafts_count FROM catalogService WHERE status = 'draft';
  IF v_services_count < 2 OR v_drafts_count < 1 THEN
    RAISE EXCEPTION 'FALHA DE HERANÇA [Cenário H]: O operador não herdou leitura de catálogo ou não vê rascunhos (total: %, drafts: %)!', v_services_count, v_drafts_count;
  END IF;
  RAISE NOTICE 'SUCESSO [Cenário H]: Herança confirmada. Operador lê catálogo e visualiza rascunhos para homologação (total: %, drafts: %).', v_services_count, v_drafts_count;
END
$$;

-- Cenário D: Operação de escrita autorizada em searchQueryLog
\echo '>>> [CENÁRIO D.1] INSERT autorizado em searchQueryLog:'
INSERT INTO searchQueryLog (term, resultCount) 
VALUES ('emissao de identidade', 5);

\echo '>>> [CENÁRIO D.2] SELECT autorizado em searchQueryLog:'
DO $$
DECLARE
  v_term text;
BEGIN
  SELECT term INTO v_term FROM searchQueryLog WHERE term = 'emissao de identidade' LIMIT 1;
  IF v_term IS NULL THEN
    RAISE EXCEPTION 'FALHA [Cenário D.2]: Operador não conseguiu ler termo gravado em searchQueryLog!';
  END IF;
  RAISE NOTICE 'SUCESSO [Cenário D.2]: Operador leu telemetria de busca com sucesso (termo: %).', v_term;
END
$$;

-- Cenário D.3: Operação de escrita autorizada em catalogFaq
\echo '>>> [CENÁRIO D.3] INSERT e UPDATE autorizados em catalogFaq:'
INSERT INTO catalogFaq (question, answer, category, isActive)
VALUES ('O servico do Cartao SUS e gratuito?', 'Sim, 100 por cento gratuito pelo SUS.', 'health', true);

UPDATE catalogFaq 
SET answer = 'Sim, o Cartao SUS e 100% gratuito e garantido por lei federal.'
WHERE question = 'O servico do Cartao SUS e gratuito?';

-- Cenário E.2: Tentativa de leitura em accountsCitizen
\echo '>>> [CENÁRIO E.2] Tentativa de leitura em accountsCitizen (esperado: permission denied):'
DO $$
BEGIN
  PERFORM * FROM accountsCitizen;
  RAISE EXCEPTION 'FALHA DE SEGURANÇA [Cenário E.2]: O operador conseguiu ler dados pessoais!';
EXCEPTION
  WHEN insufficient_privilege THEN
    RAISE NOTICE 'SUCESSO [Cenário E.2]: Leitura de dados pessoais bloqueada para o operador: %', SQLERRM;
END
$$;

-- Cenário E.3: Tentativa de leitura em auditEvent
\echo '>>> [CENÁRIO E.3] Tentativa de leitura em auditEvent (esperado: permission denied):'
DO $$
BEGIN
  PERFORM * FROM auditEvent;
  RAISE EXCEPTION 'FALHA DE SEGURANÇA [Cenário E.3]: O operador conseguiu ler trilha de auditoria!';
EXCEPTION
  WHEN insufficient_privilege THEN
    RAISE NOTICE 'SUCESSO [Cenário E.3]: Leitura da trilha de auditoria bloqueada para o operador: %', SQLERRM;
END
$$;

-- Cenário E.4: Tentativa de DELETE físico pelo operador (proibido por RN-40)
\echo '>>> [CENÁRIO E.4] Tentativa de DELETE em catalogFaq (esperado: permission denied):'
DO $$
BEGIN
  DELETE FROM catalogFaq WHERE question = 'O servico do Cartao SUS e gratuito?';
  RAISE EXCEPTION 'FALHA DE SEGURANÇA [Cenário E.4]: O operador conseguiu executar DELETE físico!';
EXCEPTION
  WHEN insufficient_privilege THEN
    RAISE NOTICE 'SUCESSO [Cenário E.4]: Exclusão física bloqueada para o operador: %', SQLERRM;
END
$$;

-- Cenário F.2: Tentativa de criação de tabela DDL
\echo '>>> [CENÁRIO F.2] Tentativa de CREATE TABLE como operador (esperado: permission denied):'
DO $$
BEGIN
  EXECUTE 'CREATE TABLE tabela_teste_operador (id int)';
  RAISE EXCEPTION 'FALHA DE SEGURANÇA [Cenário F.2]: O operador conseguiu criar tabela no schema public!';
EXCEPTION
  WHEN insufficient_privilege THEN
    RAISE NOTICE 'SUCESSO [Cenário F.2]: DDL bloqueado para o operador por permissão insuficiente: %', SQLERRM;
END
$$;

-- Cenário G.2: Tentativa de INSERT em catalogFaq violando regra WITH CHECK do RLS
\echo '>>> [CENÁRIO G.2] Tentativa de INSERT em catalogFaq violando regra WITH CHECK do RLS:'
DO $$
BEGIN
  -- Pergunta e resposta curtas (< 5 caracteres) violam a política RLS WITH CHECK
  INSERT INTO catalogFaq (question, answer, category, isActive) VALUES ('Oi', 'Oi', 'health', true);
  RAISE EXCEPTION 'FALHA DE RLS [Cenário G.2]: O RLS permitiu inserir FAQ com menos de 5 caracteres!';
EXCEPTION
  WHEN insufficient_privilege THEN
    IF SQLERRM NOT ILIKE '%violates row-level security policy%' THEN
      RAISE EXCEPTION 'FALHA INESPERADA: Esperava violação de RLS, mas ocorreu: %', SQLERRM;
    END IF;
    RAISE NOTICE 'SUCESSO [Cenário G.2]: Inserção inválida bloqueada pela política RLS (WITH CHECK): %', SQLERRM;
END
$$;

RESET ROLE;

\echo ''
\echo '======================================================================'
\echo 'TODOS OS CENÁRIOS DE TESTE (A até H) FORAM CONCLUÍDOS COM SUCESSO!'
\echo '======================================================================'
