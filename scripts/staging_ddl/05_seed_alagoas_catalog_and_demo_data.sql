-- ==============================================================================
-- SOSP — Seed Idempotente de Catálogo Alagoas, Unidades, Serviços, Sinônimos,
--        FAQs e Lotação Operacional do Servidor (Supabase Staging / PostgreSQL 17)
-- ==============================================================================
-- Garantias:
--   - 100% aditivo e idempotente (zero DROP / TRUNCATE / DELETE físico).
--   - Conformidade integral com ADR-002 (camelCase sem aspas) e CHECK constraints.
--   - Destrava a jornada completa da Demo de 7 Minutos (busca "tirar rg" -> ficha
--     -> guia/checklist -> agendamento -> protocolo -> painel do servidor -> relatório).
-- ==============================================================================

BEGIN;

-- ------------------------------------------------------------------------------
-- 1. Órgãos Complementares (preservando os 8 órgãos estaduais já existentes)
-- ------------------------------------------------------------------------------
INSERT INTO public.catalogAgency (name, acronym, sphere, description, isActive)
SELECT 'Secretaria de Estado da Segurança Pública', 'SSP', 'state',
       'Responsável pela segurança pública, identificação civil (CIN/RG) e atendimento nas Centrais Já! de Alagoas.', true
WHERE NOT EXISTS (
    SELECT 1 FROM public.catalogAgency WHERE acronym = 'SSP' AND sphere = 'state' AND deletedAt IS NULL
);

INSERT INTO public.catalogAgency (name, acronym, sphere, description, isActive)
SELECT 'Secretaria de Estado da Assistência e Desenvolvimento Social', 'SEADES', 'state',
       'Coordenação de programas sociais, Cadastro Único (CadÚnico) e proteção social em Alagoas.', true
WHERE NOT EXISTS (
    SELECT 1 FROM public.catalogAgency WHERE acronym = 'SEADES' AND sphere = 'state' AND deletedAt IS NULL
);

-- ------------------------------------------------------------------------------
-- 2. Unidades Presenciais de Atendimento (catalogUnit) + Horários (Seg–Sex 08–17)
-- ------------------------------------------------------------------------------
DO $$
DECLARE
    v_ssp_id    uuid;
    v_detran_id uuid;
    v_seades_id uuid;
    v_sefaz_id  uuid;
    v_sesau_id  uuid;
    v_casal_id  uuid;

    v_unit_centro      uuid;
    v_unit_shopping    uuid;
    v_unit_detran      uuid;
    v_unit_arapiraca   uuid;

    v_svc_cin       uuid;
    v_svc_cnh       uuid;
    v_svc_cadunico  uuid;
    v_svc_sefaz     uuid;
    v_svc_sus       uuid;
    v_svc_casal     uuid;

    v_wd smallint;
BEGIN
    SELECT id INTO v_ssp_id    FROM public.catalogAgency WHERE acronym = 'SSP'    AND deletedAt IS NULL LIMIT 1;
    SELECT id INTO v_detran_id FROM public.catalogAgency WHERE acronym = 'DETRAN' AND deletedAt IS NULL LIMIT 1;
    SELECT id INTO v_seades_id FROM public.catalogAgency WHERE acronym = 'SEADES' AND deletedAt IS NULL LIMIT 1;
    SELECT id INTO v_sefaz_id  FROM public.catalogAgency WHERE acronym = 'SEFAZ'  AND deletedAt IS NULL LIMIT 1;
    SELECT id INTO v_sesau_id  FROM public.catalogAgency WHERE acronym = 'SESAU'  AND deletedAt IS NULL LIMIT 1;
    SELECT id INTO v_casal_id  FROM public.catalogAgency WHERE acronym = 'CASAL'  AND deletedAt IS NULL LIMIT 1;

    -- Unidade 1: Central Já! Centro (Maceió)
    SELECT id INTO v_unit_centro FROM public.catalogUnit
    WHERE agencyId = v_ssp_id AND name = 'Central Já! Centro' AND city = 'Maceió' AND deletedAt IS NULL LIMIT 1;
    IF v_unit_centro IS NULL THEN
        INSERT INTO public.catalogUnit (
            agencyId, name, zipCode, street, neighborhood, city, state, addressNumber,
            phone, email, latitude, longitude, isAccessible, hasPriorityService, dailyLimit, isActive
        ) VALUES (
            v_ssp_id, 'Central Já! Centro', '57020100', 'Rua do Comércio', 'Centro', 'Maceió', 'AL', '123',
            '8233151000', 'central.centro@ssp.al.gov.br', -9.665800, -35.735300, true, true, 120, true
        ) RETURNING id INTO v_unit_centro;
    END IF;

    -- Unidade 2: Central Já! Maceió Shopping
    SELECT id INTO v_unit_shopping FROM public.catalogUnit
    WHERE agencyId = v_ssp_id AND name = 'Central Já! Maceió Shopping' AND city = 'Maceió' AND deletedAt IS NULL LIMIT 1;
    IF v_unit_shopping IS NULL THEN
        INSERT INTO public.catalogUnit (
            agencyId, name, zipCode, street, neighborhood, city, state, addressNumber,
            phone, email, latitude, longitude, isAccessible, hasPriorityService, dailyLimit, isActive
        ) VALUES (
            v_ssp_id, 'Central Já! Maceió Shopping', '57037901', 'Av. Comendador Gustavo Paiva', 'Mangabeiras', 'Maceió', 'AL', '2990',
            '8233153000', 'central.shopping@ssp.al.gov.br', -9.643200, -35.708800, true, true, 160, true
        ) RETURNING id INTO v_unit_shopping;
    END IF;

    -- Unidade 3: DETRAN-AL Sede / Central Já! Farol
    IF v_detran_id IS NOT NULL THEN
        SELECT id INTO v_unit_detran FROM public.catalogUnit
        WHERE agencyId = v_detran_id AND name = 'DETRAN-AL Sede (Farol)' AND city = 'Maceió' AND deletedAt IS NULL LIMIT 1;
        IF v_unit_detran IS NULL THEN
            INSERT INTO public.catalogUnit (
                agencyId, name, zipCode, street, neighborhood, city, state, addressNumber,
                phone, email, latitude, longitude, isAccessible, hasPriorityService, dailyLimit, isActive
            ) VALUES (
                v_detran_id, 'DETRAN-AL Sede (Farol)', '57055000', 'Av. Fernandes Lima', 'Farol', 'Maceió', 'AL', '500',
                '8233151533', 'atendimento@detran.al.gov.br', -9.645000, -35.728000, true, true, 140, true
            ) RETURNING id INTO v_unit_detran;
        END IF;
    END IF;

    -- Unidade 4: Central Já! Arapiraca
    SELECT id INTO v_unit_arapiraca FROM public.catalogUnit
    WHERE agencyId = v_ssp_id AND name = 'Central Já! Arapiraca' AND city = 'Arapiraca' AND deletedAt IS NULL LIMIT 1;
    IF v_unit_arapiraca IS NULL THEN
        INSERT INTO public.catalogUnit (
            agencyId, name, zipCode, street, neighborhood, city, state, addressNumber,
            phone, email, latitude, longitude, isAccessible, hasPriorityService, dailyLimit, isActive
        ) VALUES (
            v_ssp_id, 'Central Já! Arapiraca', '57300000', 'Rua São Francisco', 'Centro', 'Arapiraca', 'AL', '450',
            '8235211234', 'central.arapiraca@ssp.al.gov.br', -9.751700, -36.660300, true, true, 100, true
        ) RETURNING id INTO v_unit_arapiraca;
    END IF;

    -- Horários de funcionamento (Seg=1 a Sex=5, 08:00 às 17:00)
    FOR v_wd IN 1..5 LOOP
        INSERT INTO public.catalogUnitOpeningHour (unitId, weekday, opensAt, closesAt)
        VALUES (v_unit_centro, v_wd, '08:00', '17:00')
        ON CONFLICT (unitId, weekday) DO NOTHING;

        INSERT INTO public.catalogUnitOpeningHour (unitId, weekday, opensAt, closesAt)
        VALUES (v_unit_shopping, v_wd, '08:00', '17:00')
        ON CONFLICT (unitId, weekday) DO NOTHING;

        INSERT INTO public.catalogUnitOpeningHour (unitId, weekday, opensAt, closesAt)
        VALUES (v_unit_arapiraca, v_wd, '08:00', '17:00')
        ON CONFLICT (unitId, weekday) DO NOTHING;

        IF v_unit_detran IS NOT NULL THEN
            INSERT INTO public.catalogUnitOpeningHour (unitId, weekday, opensAt, closesAt)
            VALUES (v_unit_detran, v_wd, '08:00', '17:00')
            ON CONFLICT (unitId, weekday) DO NOTHING;
        END IF;
    END LOOP;

    -- --------------------------------------------------------------------------
    -- 3. Catálogo de Serviços Públicos Oficiais de Alagoas (6 serviços completos)
    -- --------------------------------------------------------------------------

    -- Serviço 1: Emitir Carteira de Identidade Nacional (CIN / RG)
    SELECT id INTO v_svc_cin FROM public.catalogService
    WHERE name = 'Emitir Carteira de Identidade Nacional (CIN)' AND deletedAt IS NULL LIMIT 1;
    IF v_svc_cin IS NULL THEN
        INSERT INTO public.catalogService (
            name, category, detailedDescription, eligibility, prerequisites,
            isFree, costAmount, averageDeadlineDays, channel, status
        ) VALUES (
            'Emitir Carteira de Identidade Nacional (CIN)',
            'documents',
            'Emissão da 1ª ou 2ª via da Carteira de Identidade Nacional (CIN / RG) em formato físico e digital, adotando o CPF como número único de identificação civil em todo o Brasil.',
            'Cidadãos brasileiros natos ou naturalizados residentes em Alagoas.',
            'Possuir CPF regularizado na Receita Federal e Certidão de Nascimento ou Casamento legível.',
            true, NULL, 10, 'inPerson', 'active'
        ) RETURNING id INTO v_svc_cin;
    END IF;

    INSERT INTO public.catalogServiceAgency (serviceId, agencyId) VALUES (v_svc_cin, v_ssp_id) ON CONFLICT DO NOTHING;
    INSERT INTO public.catalogUnitService (unitId, serviceId, isActive) VALUES (v_unit_centro, v_svc_cin, true) ON CONFLICT DO NOTHING;
    INSERT INTO public.catalogUnitService (unitId, serviceId, isActive) VALUES (v_unit_shopping, v_svc_cin, true) ON CONFLICT DO NOTHING;
    INSERT INTO public.catalogUnitService (unitId, serviceId, isActive) VALUES (v_unit_arapiraca, v_svc_cin, true) ON CONFLICT DO NOTHING;

    INSERT INTO public.catalogServiceStep (serviceId, stepOrder, title, description, estimatedTime) VALUES
      (v_svc_cin, 1, 'Agendamento Prévio no SOSP', 'Escolha a unidade Central Já!, a data e um horário disponível em slots de 30 minutos.', '5 min'),
      (v_svc_cin, 2, 'Separação dos Documentos Originais', 'Conferir a Certidão original (Nascimento ou Casamento), CPF e comprovante de residência atualizado.', '10 min'),
      (v_svc_cin, 3, 'Coleta Biométrica Presencial', 'Compareça com 15 minutos de antecedência para captura de foto digital e impressões digitais.', '20 min'),
      (v_svc_cin, 4, 'Retirada da CIN', 'Acompanhe seu protocolo no SOSP e retire o documento na unidade escolhida.', 'Até 10 dias úteis')
    ON CONFLICT (serviceId, stepOrder) DO NOTHING;

    INSERT INTO public.catalogServiceDocument (serviceId, name, isMandatory, templateUrl) VALUES
      (v_svc_cin, 'Certidão de Nascimento ou Casamento (Original)', true, NULL),
      (v_svc_cin, 'Comprovante de Inscrição no CPF', true, NULL),
      (v_svc_cin, 'Comprovante de Residência Atualizado (últimos 90 dias)', true, NULL),
      (v_svc_cin, 'Comprovante de Pagamento da Taxa DARE (apenas 2ª via)', false, NULL)
    ON CONFLICT (serviceId, name) DO NOTHING;

    -- Serviço 2: Renovação da CNH (DETRAN-AL)
    IF v_detran_id IS NOT NULL THEN
        SELECT id INTO v_svc_cnh FROM public.catalogService
        WHERE name = 'Renovação da Carteira Nacional de Habilitação (CNH)' AND deletedAt IS NULL LIMIT 1;
        IF v_svc_cnh IS NULL THEN
            INSERT INTO public.catalogService (
                name, category, detailedDescription, eligibility, prerequisites,
                isFree, costAmount, averageDeadlineDays, channel, status
            ) VALUES (
                'Renovação da Carteira Nacional de Habilitação (CNH)',
                'transit',
                'Renovação periódica da Carteira Nacional de Habilitação (CNH) vencida ou a vencer nos próximos 30 dias, com emissão da versão digital (CDT) e física.',
                'Condutores habilitados com registro ativo no DETRAN-AL.',
                'CNH anterior legível e aprovação em exame de aptidão física e mental em clínica credenciada.',
                false, 138.50, 5, 'hybrid', 'active'
            ) RETURNING id INTO v_svc_cnh;
        END IF;

        INSERT INTO public.catalogServiceAgency (serviceId, agencyId) VALUES (v_svc_cnh, v_detran_id) ON CONFLICT DO NOTHING;
        IF v_unit_detran IS NOT NULL THEN
            INSERT INTO public.catalogUnitService (unitId, serviceId, isActive) VALUES (v_unit_detran, v_svc_cnh, true) ON CONFLICT DO NOTHING;
        END IF;
        INSERT INTO public.catalogUnitService (unitId, serviceId, isActive) VALUES (v_unit_centro, v_svc_cnh, true) ON CONFLICT DO NOTHING;

        INSERT INTO public.catalogServiceStep (serviceId, stepOrder, title, description, estimatedTime) VALUES
          (v_svc_cnh, 1, 'Agendamento e Emissão da Guia', 'Agende o atendimento e emita a guia de taxa de renovação do DETRAN-AL.', '10 min'),
          (v_svc_cnh, 2, 'Exame Médico e Coleta Biométrica', 'Realize o exame de aptidão física e mental na clínica indicada e valide a biometria.', '30 min'),
          (v_svc_cnh, 3, 'Emissão e Retirada da CNH', 'Acompanhe o protocolo até a disponibilização digital no aplicativo CDT e retirada física.', '5 dias úteis')
        ON CONFLICT (serviceId, stepOrder) DO NOTHING;

        INSERT INTO public.catalogServiceDocument (serviceId, name, isMandatory, templateUrl) VALUES
          (v_svc_cnh, 'CNH Anterior ou Documento Oficial com Foto', true, NULL),
          (v_svc_cnh, 'Comprovante de Residência Atualizado', true, NULL),
          (v_svc_cnh, 'Comprovante de Quitação da Guia DETRAN', true, NULL)
        ON CONFLICT (serviceId, name) DO NOTHING;
    END IF;

    -- Serviço 3: Cadastro Único (CadÚnico)
    SELECT id INTO v_svc_cadunico FROM public.catalogService
    WHERE name = 'Cadastro Único para Programas Sociais (CadÚnico)' AND deletedAt IS NULL LIMIT 1;
    IF v_svc_cadunico IS NULL THEN
        INSERT INTO public.catalogService (
            name, category, detailedDescription, eligibility, prerequisites,
            isFree, costAmount, averageDeadlineDays, channel, status
        ) VALUES (
            'Cadastro Único para Programas Sociais (CadÚnico)',
            'socialAssistance',
            'Inscrição e atualização cadastral no Cadastro Único do Governo Federal para acesso a benefícios sociais como Bolsa Família, Tarifa Social de Energia e BPC.',
            'Famílias de baixa renda com renda mensal de até meio salário mínimo por pessoa.',
            'O responsável familiar deve ter mais de 16 anos e apresentar documentos de todos os membros da residência.',
            true, NULL, 15, 'inPerson', 'active'
        ) RETURNING id INTO v_svc_cadunico;
    END IF;

    INSERT INTO public.catalogServiceAgency (serviceId, agencyId) VALUES (v_svc_cadunico, v_seades_id) ON CONFLICT DO NOTHING;
    INSERT INTO public.catalogUnitService (unitId, serviceId, isActive) VALUES (v_unit_centro, v_svc_cadunico, true) ON CONFLICT DO NOTHING;
    INSERT INTO public.catalogUnitService (unitId, serviceId, isActive) VALUES (v_unit_arapiraca, v_svc_cadunico, true) ON CONFLICT DO NOTHING;

    INSERT INTO public.catalogServiceStep (serviceId, stepOrder, title, description, estimatedTime) VALUES
      (v_svc_cadunico, 1, 'Agendamento Presencial', 'Reserve o horário mais próximo na Central Já! ou CRAS de referência.', '5 min'),
      (v_svc_cadunico, 2, 'Entrevista Socioeconômica', 'Compareça com os documentos de todos os moradores da casa para preenchimento do cadastro.', '30 min'),
      (v_svc_cadunico, 3, 'Emissão do NIS', 'Acompanhe a validação e geração do Número de Identificação Social (NIS).', 'Até 15 dias')
    ON CONFLICT (serviceId, stepOrder) DO NOTHING;

    INSERT INTO public.catalogServiceDocument (serviceId, name, isMandatory, templateUrl) VALUES
      (v_svc_cadunico, 'CPF ou Título de Eleitor do Responsável Familiar', true, NULL),
      (v_svc_cadunico, 'Documento com Foto ou Certidão de todos os Moradores', true, NULL),
      (v_svc_cadunico, 'Comprovante de Residência', false, NULL)
    ON CONFLICT (serviceId, name) DO NOTHING;

    -- Serviço 4: Certidão Negativa de Débitos Estaduais (SEFAZ)
    IF v_sefaz_id IS NOT NULL THEN
        SELECT id INTO v_svc_sefaz FROM public.catalogService
        WHERE name = 'Certidão Negativa de Débitos Estaduais (SEFAZ)' AND deletedAt IS NULL LIMIT 1;
        IF v_svc_sefaz IS NULL THEN
            INSERT INTO public.catalogService (
                name, category, detailedDescription, eligibility, prerequisites,
                isFree, costAmount, averageDeadlineDays, channel, externalUrl, status
            ) VALUES (
                'Certidão Negativa de Débitos Estaduais (SEFAZ)',
                'taxes',
                'Emissão gratuita de certidão que comprova regularidade fiscal de pessoas físicas e jurídicas perante a Secretaria da Fazenda de Alagoas (IPVA, ICMS, ITCD).',
                'Pessoas físicas e jurídicas inscritas no CPF ou CNPJ sem pendências fiscais em Alagoas.',
                'Informar CPF ou CNPJ válido.',
                true, NULL, 0, 'online', 'https://www.sefaz.al.gov.br', 'active'
            ) RETURNING id INTO v_svc_sefaz;
        END IF;

        INSERT INTO public.catalogServiceAgency (serviceId, agencyId) VALUES (v_svc_sefaz, v_sefaz_id) ON CONFLICT DO NOTHING;
        INSERT INTO public.catalogServiceStep (serviceId, stepOrder, title, description, estimatedTime) VALUES
          (v_svc_sefaz, 1, 'Informar CPF ou CNPJ', 'Acesse o portal online da SEFAZ-AL e informe o documento do contribuinte.', '2 min'),
          (v_svc_sefaz, 2, 'Emitir e Salvar Certidão PDF', 'Gere imediatamente o documento com código de autenticidade válido por 60 dias.', 'Imediato')
        ON CONFLICT (serviceId, stepOrder) DO NOTHING;

        INSERT INTO public.catalogServiceDocument (serviceId, name, isMandatory, templateUrl) VALUES
          (v_svc_sefaz, 'Número do CPF ou CNPJ', true, NULL),
          (v_svc_sefaz, 'Inscrição Estadual (se Pessoa Jurídica)', false, NULL)
        ON CONFLICT (serviceId, name) DO NOTHING;
    END IF;

    -- Serviço 5: Cartão Nacional de Saúde (Cartão SUS)
    IF v_sesau_id IS NOT NULL THEN
        SELECT id INTO v_svc_sus FROM public.catalogService
        WHERE name = 'Emissão e Atualização do Cartão SUS' AND deletedAt IS NULL LIMIT 1;
        IF v_svc_sus IS NULL THEN
            INSERT INTO public.catalogService (
                name, category, detailedDescription, eligibility, prerequisites,
                isFree, costAmount, averageDeadlineDays, channel, status
            ) VALUES (
                'Emissão e Atualização do Cartão SUS',
                'health',
                'Cadastro e emissão imediata do Cartão Nacional de Saúde (CNS) para acesso a consultas, exames e medicamentos na rede pública de Alagoas.',
                'Todos os cidadãos brasileiros e estrangeiros residentes no país.',
                'Apresentar CPF e documento oficial com foto.',
                true, NULL, 0, 'inPerson', 'active'
            ) RETURNING id INTO v_svc_sus;
        END IF;

        INSERT INTO public.catalogServiceAgency (serviceId, agencyId) VALUES (v_svc_sus, v_sesau_id) ON CONFLICT DO NOTHING;
        INSERT INTO public.catalogUnitService (unitId, serviceId, isActive) VALUES (v_unit_centro, v_svc_sus, true) ON CONFLICT DO NOTHING;
        INSERT INTO public.catalogUnitService (unitId, serviceId, isActive) VALUES (v_unit_shopping, v_svc_sus, true) ON CONFLICT DO NOTHING;

        INSERT INTO public.catalogServiceStep (serviceId, stepOrder, title, description, estimatedTime) VALUES
          (v_svc_sus, 1, 'Agendamento ou Comparecimento', 'Agende na Central Já! mais próxima.', '5 min'),
          (v_svc_sus, 2, 'Emissão Imediata no Balcão', 'Apresente os documentos originais e receba o cartão atualizado na hora.', '15 min')
        ON CONFLICT (serviceId, stepOrder) DO NOTHING;

        INSERT INTO public.catalogServiceDocument (serviceId, name, isMandatory, templateUrl) VALUES
          (v_svc_sus, 'Documento Oficial com Foto (RG ou CNH)', true, NULL),
          (v_svc_sus, 'CPF e Comprovante de Residência', true, NULL)
        ON CONFLICT (serviceId, name) DO NOTHING;
    END IF;

    -- Serviço 6: Segunda Via e Negociação CASAL
    IF v_casal_id IS NOT NULL THEN
        SELECT id INTO v_svc_casal FROM public.catalogService
        WHERE name = 'Segunda Via de Fatura e Negociação CASAL' AND deletedAt IS NULL LIMIT 1;
        IF v_svc_casal IS NULL THEN
            INSERT INTO public.catalogService (
                name, category, detailedDescription, eligibility, prerequisites,
                isFree, costAmount, averageDeadlineDays, channel, status
            ) VALUES (
                'Segunda Via de Fatura e Negociação CASAL',
                'general',
                'Emissão de 2ª via de conta de água/esgoto, atualização de titularidade e parcelamento de débitos junto à Companhia de Saneamento de Alagoas (CASAL).',
                'Titulares ou moradores de imóveis atendidos pela CASAL.',
                'Número de matrícula do imóvel ou CPF do titular.',
                true, NULL, 1, 'hybrid', 'active'
            ) RETURNING id INTO v_svc_casal;
        END IF;

        INSERT INTO public.catalogServiceAgency (serviceId, agencyId) VALUES (v_svc_casal, v_casal_id) ON CONFLICT DO NOTHING;
        INSERT INTO public.catalogUnitService (unitId, serviceId, isActive) VALUES (v_unit_centro, v_svc_casal, true) ON CONFLICT DO NOTHING;

        INSERT INTO public.catalogServiceStep (serviceId, stepOrder, title, description, estimatedTime) VALUES
          (v_svc_casal, 1, 'Identificação da Matrícula', 'Tenha em mãos o número da matrícula do imóvel ou conta anterior.', '5 min'),
          (v_svc_casal, 2, 'Emissão ou Acordo de Parcelamento', 'Emita o boleto atualizado ou formalize acordo na Central Já!.', '15 min')
        ON CONFLICT (serviceId, stepOrder) DO NOTHING;

        INSERT INTO public.catalogServiceDocument (serviceId, name, isMandatory, templateUrl) VALUES
          (v_svc_casal, 'Documento com Foto e CPF', true, NULL),
          (v_svc_casal, 'Número da Matrícula do Imóvel ou Fatura Anterior', true, NULL)
        ON CONFLICT (serviceId, name) DO NOTHING;
    END IF;

    -- --------------------------------------------------------------------------
    -- 4. Vinculação de Lotação Operacional do Servidor João Servidor Central (RN-36)
    -- --------------------------------------------------------------------------
    UPDATE public.accountsInternalUser
       SET agencyId  = v_ssp_id,
           unitId    = v_unit_centro,
           updatedAt = now()
     WHERE cpf = '33366699957'
       AND deletedAt IS NULL;

END;
$$;

-- ------------------------------------------------------------------------------
-- 5. Sinônimos Oficiais de Busca Semântica (searchSynonym — Demo "tirar rg")
-- Nota: literais '{"a","b"}' funcionam tanto em coluna text quanto text[]/varchar[]
-- ------------------------------------------------------------------------------
INSERT INTO public.searchSynonym (term, synonyms, isActive) VALUES
  ('tirar rg',   '{"identidade","cin","carteira de identidade","rg"}', true),
  ('rg',         '{"identidade","cin","carteira de identidade"}', true),
  ('identidade', '{"rg","cin","carteira de identidade"}', true),
  ('cnh',        '{"carteira nacional de habilitacao","habilitacao","renovacao","detran"}', true),
  ('iptu',       '{"tributos","certidao","sefaz","debitos"}', true),
  ('certidao',   '{"sefaz","debitos","negativa","identidade"}', true),
  ('cadunico',   '{"cadastro unico","bolsa familia","assistencia social"}', true),
  ('sus',        '{"cartao sus","saude","sesau"}', true),
  ('agua',       '{"casal","fatura","segunda via","saneamento"}', true)
ON CONFLICT (term) DO UPDATE
  SET synonyms = EXCLUDED.synonyms,
      isActive = true;

-- ------------------------------------------------------------------------------
-- 6. Perguntas Frequentes Oficiais (catalogFaq)
-- ------------------------------------------------------------------------------
INSERT INTO public.catalogFaq (question, answer, category, isActive)
SELECT 'Como agendar um atendimento presencial no SOSP?',
       'Busque o serviço desejado no catálogo, consulte a ficha orientativa de 8 blocos, escolha a unidade de atendimento, a data e o slot de 30 minutos disponível. Ao confirmar, seu protocolo AAAAMMDD-XXXX será gerado imediatamente.',
       'general', true
WHERE NOT EXISTS (SELECT 1 FROM public.catalogFaq WHERE question = 'Como agendar um atendimento presencial no SOSP?');

INSERT INTO public.catalogFaq (question, answer, category, isActive)
SELECT 'Por que o botão Entrar com Gov.br abre uma mensagem de atualização?',
       'A integração federada OIDC com a conta Gov.br pertence à versão 2.0 (ADR-003). No MVP, cidadãos, servidores e administradores acessam com CPF e senha locais protegidos por Argon2id.',
       'general', true
WHERE NOT EXISTS (SELECT 1 FROM public.catalogFaq WHERE question = 'Por que o botão Entrar com Gov.br abre uma mensagem de atualização?');

INSERT INTO public.catalogFaq (question, answer, category, isActive)
SELECT 'Posso remarcar ou cancelar meu agendamento?',
       'Sim. Conforme a regra RN-22, o cancelamento pode ser feito diretamente na área Meus Agendamentos com antecedência mínima de 24 horas em relação ao horário reservado.',
       'general', true
WHERE NOT EXISTS (SELECT 1 FROM public.catalogFaq WHERE question = 'Posso remarcar ou cancelar meu agendamento?');

INSERT INTO public.catalogFaq (question, answer, category, isActive)
SELECT 'Quais arquivos são aceitos para anexar documentos a um protocolo?',
       'O SOSP aceita arquivos nos formatos PDF, JPG e PNG com tamanho máximo de 10 MB por arquivo (regra RS-04).',
       'documents', true
WHERE NOT EXISTS (SELECT 1 FROM public.catalogFaq WHERE question = 'Quais arquivos são aceitos para anexar documentos a um protocolo?');

COMMIT;

-- Consulta de conferência pós-seed (Somente Leitura)
SELECT
  (SELECT count(*) FROM public.catalogAgency  WHERE isActive = true AND deletedAt IS NULL) AS agencies_active,
  (SELECT count(*) FROM public.catalogUnit    WHERE isActive = true AND deletedAt IS NULL) AS units_active,
  (SELECT count(*) FROM public.catalogService WHERE status = 'active' AND deletedAt IS NULL) AS services_active,
  (SELECT count(*) FROM public.searchSynonym  WHERE isActive = true) AS synonyms_active,
  (SELECT count(*) FROM public.catalogFaq     WHERE isActive = true) AS faqs_active;
