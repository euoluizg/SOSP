-- =============================================================================
-- SOSP — Sistema de Orientação para Serviços Públicos
-- Módulo de Segurança: Contas, Roles e Permissões PostgreSQL (3AF / 2026)
--
-- Equipe Oficial:
--   - Product Owner: Mozart Melo
--   - Tech Lead & Back-end: Arthur Franco
--   - Front-end, UI/UX & QA: Luiz Gustavo
--
-- Objetivo Acadêmico (3AF):
--   "Criação de Contas e Permissões para acessar a estrutura" (Critério 4 — 1,0 ponto)
--
-- Pré-requisito:
--   Execução prévia do DDL físico em `docs/database/schema.sql` (36 tabelas, PostgreSQL 17).
--
-- Princípios Arquiteturais Aplicados:
--   1. Princípio do Menor Privilégio (PoLP - Principle of Least Privilege);
--   2. Separação entre Roles de Grupo (NOLOGIN) e Contas de Usuário (LOGIN);
--   3. Herança declarativa entre papéis (INHERIT) no PostgreSQL 17;
--   4. Defesa em Profundidade: Privilégios SQL (GRANT/REVOKE) + RLS (Row Level Security);
--   5. Suporte a Views com `security_invoker = true` (zero bypass de RLS);
--   6. Proteção Estrita de Dados Pessoais (LGPD / RS-01 a RS-05);
--   7. Eliminação de permissões amplas desnecessárias (zero sequences em schema UUID);
--   8. Segurança de Credenciais: Nenhuma senha fixa ou real versionada em código.
-- =============================================================================

BEGIN;

  -- ---------------------------------------------------------------------------
  -- 1. CRIAÇÃO DE ROLES DE GRUPO (NOLOGIN) COM HERANÇA ATIVADA (INHERIT)
  -- ---------------------------------------------------------------------------
  -- Roles de grupo encapsulam permissões e não permitem autenticação direta.
  -- Usam INHERIT para permitir propagação transitiva de privilégios aos membros.
  -- ---------------------------------------------------------------------------

  DO $$
  BEGIN
    -- Role de Consulta Pública (Leitor)
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sosp_leitor_role') THEN
      CREATE ROLE sosp_leitor_role NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT;
      COMMENT ON ROLE sosp_leitor_role IS 'Papel de grupo para consultas públicas de catálogo e serviços no SOSP.';
    ELSE
      ALTER ROLE sosp_leitor_role INHERIT;
    END IF;

    -- Role de Operação Controlada (Operador)
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sosp_operador_role') THEN
      CREATE ROLE sosp_operador_role NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT;
      COMMENT ON ROLE sosp_operador_role IS 'Papel de grupo para operações de registro de logs de busca e gestão de FAQs.';
    ELSE
      ALTER ROLE sosp_operador_role INHERIT;
    END IF;
  END
  $$;

  -- ---------------------------------------------------------------------------
  -- 2. CRIAÇÃO DE CONTAS DE DEMONSTRAÇÃO (LOGIN)
  -- ---------------------------------------------------------------------------
  -- Contas reais de banco que herdam permissões de suas respectivas roles de grupo.
  -- NOTA DE SEGURANÇA:
  --   Em conformidade com as regras de segurança e o prompt mestre da 3AF, nenhuma
  --   senha em texto claro é versionada no repositório. Em ambientes reais (Supabase/CI),
  --   a senha é definida via comando isolado ou variável de ambiente segura:
  --     ALTER ROLE sosp_leitor_3af WITH PASSWORD '<SENHA_SEGURA_FORNECIDA_PELO_COFRE>';
  -- ---------------------------------------------------------------------------

  DO $$
  BEGIN
    -- Conta de Demonstração: Leitor Acadêmico
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sosp_leitor_3af') THEN
      CREATE ROLE sosp_leitor_3af WITH LOGIN INHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE;
      COMMENT ON ROLE sosp_leitor_3af IS 'Conta de demonstração acadêmica 3AF para auditoria de leitura no SOSP.';
    ELSE
      ALTER ROLE sosp_leitor_3af WITH LOGIN INHERIT;
    END IF;

    -- Conta de Demonstração: Operador Acadêmico
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sosp_operador_3af') THEN
      CREATE ROLE sosp_operador_3af WITH LOGIN INHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE;
      COMMENT ON ROLE sosp_operador_3af IS 'Conta de demonstração acadêmica 3AF para auditoria de operações no SOSP.';
    ELSE
      ALTER ROLE sosp_operador_3af WITH LOGIN INHERIT;
    END IF;
  END
  $$;

  -- ---------------------------------------------------------------------------
  -- 3. ASSOCIAÇÃO DAS CONTAS ÀS RESPECTIVAS ROLES DE GRUPO
  -- ---------------------------------------------------------------------------
  GRANT sosp_leitor_role TO sosp_leitor_3af;
  GRANT sosp_operador_role TO sosp_operador_3af;

  -- ---------------------------------------------------------------------------
  -- 4. HARDENING DO SCHEMA PUBLIC (REVOGAÇÃO DE PRIVILÉGIOS INDISCRIMINADOS)
  -- ---------------------------------------------------------------------------
  -- Por padrão no PostgreSQL, o papel PUBLIC possui privilégios de conexão e criação.
  -- Removemos explicitamente para garantir que apenas papéis autorizados operem.
  -- ---------------------------------------------------------------------------
  REVOKE CREATE ON SCHEMA public FROM PUBLIC;

  -- Concede acesso de navegação no schema public exclusivamente às roles do SOSP
  GRANT USAGE ON SCHEMA public TO sosp_leitor_role, sosp_operador_role;

  -- ---------------------------------------------------------------------------
  -- 5. CONCESSÃO DE PRIVILÉGIOS PARA O PAPEL LEITOR (`sosp_leitor_role`)
  -- ---------------------------------------------------------------------------
  -- O papel leitor tem acesso ESTRITAMENTE DE LEITURA (SELECT) sobre o catálogo
  -- público de serviços, unidades, horários, sinônimos, disponibilidade de slots
  -- e views informativas com security_invoker = true.
  -- PROIBIDO: INSERT, UPDATE, DELETE, DDL ou acesso a dados pessoais (accountsCitizen, etc).
  -- ---------------------------------------------------------------------------

  GRANT SELECT ON TABLE
    catalogAgency,
    catalogUnit,
    catalogUnitOpeningHour,
    catalogNonWorkingDay,
    catalogService,
    catalogServiceAgency,
    catalogUnitService,
    catalogServiceStep,
    catalogServiceDocument,
    catalogFaq,
    catalogServiceVersion,
    searchSynonym,
    schedulingSlot
  TO sosp_leitor_role;

  -- Concessão sobre as views de catálogo público
  GRANT SELECT ON TABLE
    vw_catalogServiceSearch,
    vw_schedulingSlotAvailability
  TO sosp_leitor_role;

  -- ---------------------------------------------------------------------------
  -- 6. CONCESSÃO DE PRIVILÉGIOS PARA O PAPEL OPERADOR (`sosp_operador_role`)
  -- ---------------------------------------------------------------------------
  -- O operador herda as permissões de leitura do leitor via herança transitiva
  -- e recebe privilégios controlados de escrita sobre um subconjunto estrito
  -- de tabelas operacionais:
  --   - `searchQueryLog`: registro e leitura de buscas anonimizadas (RF-04);
  --   - `catalogFaq`: cadastro e atualização de perguntas frequentes públicas (RF-06);
  --   - `searchSynonym`: consulta e cadastro de sinônimos de busca (RN-04).
  --
  -- ISOLAMENTO LGPD / SEGURANÇA:
  --   O operador NUNCA possui acesso de escrita ou leitura em:
  --   - accountsCitizen (dados pessoais, CPF, endereço, senhas);
  --   - accountsInternalUser (senhas e matrículas de servidores);
  --   - accountsCitizenSession e accountsLoginAttempt (sessões e auditoria);
  --   - auditEvent e auditDataSubjectRequest (trilha de auditoria imutável);
  --   - schedulingAppointment e schedulingProtocolAttachment (dados sigilosos de agendamentos).
  -- ---------------------------------------------------------------------------

  -- O operador herda o catálogo de leitura com herança ativada
  GRANT sosp_leitor_role TO sosp_operador_role WITH INHERIT TRUE;

  -- Privilégios de inserção de logs anônimos de busca
  GRANT SELECT, INSERT ON TABLE searchQueryLog TO sosp_operador_role;

  -- Privilégios de gestão operacional de FAQ
  GRANT SELECT, INSERT, UPDATE ON TABLE catalogFaq TO sosp_operador_role;

  -- Privilégios de gestão operacional de sinônimos
  GRANT SELECT, INSERT, UPDATE ON TABLE searchSynonym TO sosp_operador_role;

  -- Bloqueio estrito de DELETE para o leitor e operador (exclusão física proibida - RN-40)
  REVOKE DELETE ON ALL TABLES IN SCHEMA public FROM sosp_leitor_role, sosp_operador_role;

  -- NOTA: O schema adota identificadores UUID (gen_random_uuid()) em todas as tabelas.
  -- Nenhuma SEQUENCE existe no schema; permissões genéricas de SEQUENCE foram eliminadas.

COMMIT;
