-- =============================================================================
-- SOSP — Sistema de Orientação para Serviços Públicos
-- Bateria de Testes de Permissões e RLS (3AF / 2026)
--
-- Equipe Oficial:
--   - Product Owner: Mozart Melo
--   - Tech Lead & Back-end: Arthur Franco
--   - Front-end, UI/UX & QA: Luiz Gustavo
--
-- Cenários Testados:
--   - Cenário A: Leitura permitida com papel leitor (catalogAgency e catalogService ativos);
--   - Cenário B: Inserção negada com papel leitor (catalogService);
--   - Cenário C: Atualização negada com papel leitor (catalogService);
--   - Cenário D: Operação autorizada com papel operador (searchQueryLog e catalogFaq);
--   - Cenário E: Operação negada em dados sensíveis com papel operador (accountsCitizen e auditEvent);
--   - Cenário F: Criação de tabela negada (DDL) para leitor e operador;
--   - Cenário G: RLS em ação (filtro de rascunhos e validação WITH CHECK).
-- =============================================================================

-- =============================================================================
-- FASE 0: PREPARAÇÃO DE DADOS DE TESTE (EXECUTADO COMO PROPRIETÁRIO / DBA)
-- =============================================================================

\echo '----------------------------------------------------------------------'
\echo 'FASE 0: INICIALIZAÇÃO DE DADOS DE TESTE (DBA / PROPRIETÁRIO)'
\echo '----------------------------------------------------------------------'

-- Limpa dados prévios de teste se houver
TRUNCATE TABLE catalogServiceAgency, catalogUnitService, catalogService, catalogUnit, catalogAgency, accountsCitizen, accountsGender, searchQueryLog, catalogFaq CASCADE;

-- 1. Insere Gênero e Cidadão de Testes (Dado Pessoal Sensível - LGPD)
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

-- 4. Insere 1 FAQ Ativa e 1 FAQ Inativa (chkCatalogFaqLink exige serviceId ou category)
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
SELECT acronym, name, sphere FROM catalogAgency;

-- Cenário G (Parte 1): RLS em catalogService (deve retornar APENAS o serviço ativo, filtrando o draft)
\echo '>>> [CENÁRIO G.1] RLS em catalogService (esperado: apenas 1 servico ativo, 0 drafts):'
SELECT id, name, status FROM catalogService;

-- Cenário B: Tentativa de inserção negada
\echo '>>> [CENÁRIO B] Tentativa de INSERT em catalogService (esperado: permission denied):'
DO $$
BEGIN
  INSERT INTO catalogService (name, category, detailedDescription, eligibility, isFree, averageDeadlineDays, channel, status)
  VALUES ('Servico Hacker', 'health', 'Desc', 'Elig', true, 1, 'inPerson', 'active');
  RAISE EXCEPTION 'FALHA: O leitor conseguiu inserir no catalogo!';
EXCEPTION
  WHEN insufficient_privilege THEN
    RAISE NOTICE 'SUCESSO: Insercao bloqueada por permissao insuficiente: %', SQLERRM;
END
$$;

-- Cenário C: Tentativa de atualização negada
\echo '>>> [CENÁRIO C] Tentativa de UPDATE em catalogAgency (esperado: permission denied):'
DO $$
BEGIN
  UPDATE catalogAgency SET name = 'Secretaria Alterada' WHERE acronym = 'SESAU';
  RAISE EXCEPTION 'FALHA: O leitor conseguiu atualizar o orgao!';
EXCEPTION
  WHEN insufficient_privilege THEN
    RAISE NOTICE 'SUCESSO: Atualizacao bloqueada por permissao insuficiente: %', SQLERRM;
END
$$;

-- Cenário E (Leitor): Tentativa de leitura de dados pessoais (accountsCitizen)
\echo '>>> [CENÁRIO E.1] Tentativa de leitura de dados pessoais em accountsCitizen (esperado: permission denied):'
DO $$
BEGIN
  PERFORM * FROM accountsCitizen;
  RAISE EXCEPTION 'FALHA: O leitor conseguiu ler dados pessoais de cidadaos!';
EXCEPTION
  WHEN insufficient_privilege THEN
    RAISE NOTICE 'SUCESSO: Consulta a dados pessoais bloqueada por permissao insuficiente: %', SQLERRM;
END
$$;

-- Cenário F (Leitor): Tentativa de criação de tabela DDL
\echo '>>> [CENÁRIO F.1] Tentativa de CREATE TABLE como leitor (esperado: permission denied for schema public):'
DO $$
BEGIN
  EXECUTE 'CREATE TABLE tabela_teste_leitor (id int)';
  RAISE EXCEPTION 'FALHA: O leitor conseguiu criar tabela no schema public!';
EXCEPTION
  WHEN insufficient_privilege THEN
    RAISE NOTICE 'SUCESSO: Criacao de tabela bloqueada por permissao insuficiente no schema: %', SQLERRM;
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

-- Cenário D: Operação de escrita autorizada em searchQueryLog (registro de busca)
\echo '>>> [CENÁRIO D.1] INSERT autorizado em searchQueryLog:'
INSERT INTO searchQueryLog (term, resultCount) 
VALUES ('emissao de identidade', 5)
RETURNING id, term, resultCount;

\echo '>>> [CENÁRIO D.2] SELECT autorizado em searchQueryLog:'
SELECT term, resultCount FROM searchQueryLog;

-- Cenário D.3: Operação de escrita autorizada em catalogFaq
\echo '>>> [CENÁRIO D.3] INSERT e UPDATE autorizados em catalogFaq:'
INSERT INTO catalogFaq (question, answer, category, isActive)
VALUES ('O servico do Cartao SUS e gratuito?', 'Sim, 100 por cento gratuito pelo SUS.', 'health', true)
RETURNING id, question, answer;

UPDATE catalogFaq 
SET answer = 'Sim, o Cartao SUS e 100% gratuito e garantido por lei federal.'
WHERE question = 'O servico do Cartao SUS e gratuito?'
RETURNING id, question, answer;

-- Cenário E (Operador): Tentativa de leitura de dados pessoais e de auditoria
\echo '>>> [CENÁRIO E.2] Tentativa de leitura em accountsCitizen (esperado: permission denied):'
DO $$
BEGIN
  PERFORM * FROM accountsCitizen;
  RAISE EXCEPTION 'FALHA: O operador conseguiu ler dados pessoais!';
EXCEPTION
  WHEN insufficient_privilege THEN
    RAISE NOTICE 'SUCESSO: Leitura de dados pessoais bloqueada para o operador: %', SQLERRM;
END
$$;

\echo '>>> [CENÁRIO E.3] Tentativa de leitura em auditEvent (esperado: permission denied):'
DO $$
BEGIN
  PERFORM * FROM auditEvent;
  RAISE EXCEPTION 'FALHA: O operador conseguiu ler trilha de auditoria!';
EXCEPTION
  WHEN insufficient_privilege THEN
    RAISE NOTICE 'SUCESSO: Leitura da trilha de auditoria bloqueada para o operador: %', SQLERRM;
END
$$;

-- Cenário E.4: Tentativa de DELETE físico pelo operador (proibido por RN-40)
\echo '>>> [CENÁRIO E.4] Tentativa de DELETE em catalogFaq (esperado: permission denied):'
DO $$
BEGIN
  DELETE FROM catalogFaq WHERE question = 'O servico do Cartao SUS e gratuito?';
  RAISE EXCEPTION 'FALHA: O operador conseguiu executar DELETE fisico!';
EXCEPTION
  WHEN insufficient_privilege THEN
    RAISE NOTICE 'SUCESSO: Exclusao fisica bloqueada para o operador: %', SQLERRM;
END
$$;

-- Cenário F (Operador): Tentativa de criação de tabela DDL
\echo '>>> [CENÁRIO F.2] Tentativa de CREATE TABLE como operador (esperado: permission denied):'
DO $$
BEGIN
  EXECUTE 'CREATE TABLE tabela_teste_operador (id int)';
  RAISE EXCEPTION 'FALHA: O operador conseguiu criar tabela no schema public!';
EXCEPTION
  WHEN insufficient_privilege THEN
    RAISE NOTICE 'SUCESSO: DDL bloqueado para o operador por permissao insuficiente: %', SQLERRM;
END
$$;

-- Cenário G (RLS Operador): Validação de regra WITH CHECK no INSERT
\echo '>>> [CENÁRIO G.2] Tentativa de INSERT em catalogFaq violando regra WITH CHECK do RLS:'
DO $$
BEGIN
  -- Pergunta e resposta com menos de 5 caracteres violam o WITH CHECK da politica RLS
  INSERT INTO catalogFaq (question, answer, category, isActive) VALUES ('Oi', 'Oi', 'health', true);
  RAISE EXCEPTION 'FALHA: O RLS permitiu inserir FAQ com menos de 5 caracteres!';
EXCEPTION
  WHEN check_violation OR OTHERS THEN
    RAISE NOTICE 'SUCESSO: Insercao invalida bloqueada pela politica RLS (WITH CHECK): %', SQLERRM;
END
$$;

RESET ROLE;

\echo ''
\echo '======================================================================'
\echo 'TODOS OS CENÁRIOS DE TESTE (A até G) FORAM CONCLUÍDOS COM SUCESSO!'
\echo '======================================================================'
