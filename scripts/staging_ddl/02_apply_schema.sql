-- =============================================================================
-- SOSP — Sistema de Orientação para Serviços Públicos
-- Schema DDL Idempotente, Não-Destrutivo e Alinhado ao ORM — PostgreSQL 17+
--
-- Regras de Governança:
-- 1. Identificadores em camelCase SEM aspas duplas (ADR-002).
-- 2. Idempotência estrita: CREATE TABLE IF NOT EXISTS, CREATE INDEX IF NOT EXISTS.
-- 3. Exclusão lógica: nenhum DROP TABLE ou TRUNCATE permitido (RN-40, RS-05).
-- 4. Funções com SECURITY DEFINER e search_path restrito a pg_catalog, public.
-- 5. Menor privilégio: REVOKE ALL FROM PUBLIC em funções de segurança.
-- 6. Defesa em profundidade: Row Level Security (RLS) habilitado em todas as tabelas.
-- 7. Alinhamento exato de 100% das 36 tabelas e colunas com Pilar 4 e Django ORM.
-- =============================================================================

BEGIN;

  -- -----------------------------------------------------------------------------
  -- 1. EXTENSÕES POSTGRESQL E CONFIGURAÇÃO TEXT SEARCH
  -- -----------------------------------------------------------------------------
  CREATE EXTENSION IF NOT EXISTS pg_trgm;
  CREATE EXTENSION IF NOT EXISTS unaccent;
  CREATE EXTENSION IF NOT EXISTS pgcrypto;

  -- Configuração de busca em português sem acentos (FTS)
  DO $$
  BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_ts_config WHERE cfgname = 'sospportuguese') THEN
      CREATE TEXT SEARCH CONFIGURATION sospPortuguese (COPY = portuguese);
      ALTER TEXT SEARCH CONFIGURATION sospPortuguese
        ALTER MAPPING FOR hword, hword_part, word
        WITH unaccent, portuguese_stem;
    END IF;
  END $$;

  -- -----------------------------------------------------------------------------
  -- 2. FUNÇÃO UTILITÁRIA DE ATUALIZAÇÃO AUTOMÁTICA DE UPDATEDAT
  -- -----------------------------------------------------------------------------
  CREATE OR REPLACE FUNCTION setUpdatedAt()
  RETURNS trigger
  LANGUAGE plpgsql
  SET search_path = pg_catalog, public
  AS $$
  BEGIN
    NEW.updatedAt = now();
    RETURN NEW;
  END;
  $$;

  -- -----------------------------------------------------------------------------
  -- 3. SCHEMA DE SEGURANÇA E AUTENTICAÇÃO DE MENOR PRIVILÉGIO
  -- -----------------------------------------------------------------------------
  CREATE SCHEMA IF NOT EXISTS sosp_security;
  REVOKE ALL ON SCHEMA sosp_security FROM PUBLIC;

  -- =============================================================================
  -- MÓDULO 1: ACCOUNTS
  -- =============================================================================

  CREATE TABLE IF NOT EXISTS accountsGender (
    id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name      varchar(40) NOT NULL,
    sortOrder smallint NOT NULL DEFAULT 0,
    isActive  boolean NOT NULL DEFAULT true,
    createdAt timestamptz NOT NULL DEFAULT now(),
    updatedAt timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uqAccountsGenderName UNIQUE (name)
  );

  CREATE TABLE IF NOT EXISTS accountsCitizen (
    id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    cpf                   varchar(11) NOT NULL,
    fullName              varchar(120) NOT NULL,
    birthDate             date NOT NULL,
    email                 varchar(200) NOT NULL,
    phone                 varchar(11) NOT NULL,
    passwordHash          text NOT NULL,
    passwordSalt          text NOT NULL,
    recoveryCodeHash      text,
    recoveryCodeExpiresAt timestamptz,
    loginAttempts         integer NOT NULL DEFAULT 0,
    blockedUntil          timestamptz,
    genderId              uuid NOT NULL,
    genderDescription     varchar(120),
    isPcd                 boolean NOT NULL DEFAULT false,
    disabilityDescription varchar(120),
    motherName            varchar(120) NOT NULL,
    fatherName            varchar(120),
    zipCode               varchar(8) NOT NULL,
    street                varchar(120) NOT NULL,
    neighborhood          varchar(80) NOT NULL,
    city                  varchar(80) NOT NULL,
    state                 varchar(2) NOT NULL,
    addressNumber         varchar(10) NOT NULL,
    addressComplement     varchar(60),
    avatarUrl             varchar(500),
    govbrSubjectId        varchar(255),
    emailVerifiedAt       timestamptz,
    lastLoginAt           timestamptz,
    isActive              boolean NOT NULL DEFAULT true,
    createdAt             timestamptz NOT NULL DEFAULT now(),
    updatedAt             timestamptz NOT NULL DEFAULT now(),
    deletedAt             timestamptz,
    CONSTRAINT fkAccountsCitizenGender FOREIGN KEY (genderId) REFERENCES accountsGender (id),
    CONSTRAINT chkAccountsCitizenCpf CHECK (cpf ~ '^[0-9]{11}$'),
    CONSTRAINT chkAccountsCitizenZip CHECK (zipCode ~ '^[0-9]{8}$'),
    CONSTRAINT chkAccountsCitizenState CHECK (state ~ '^[A-Z]{2}$'),
    CONSTRAINT chkAccountsCitizenPhone CHECK (phone ~ '^[0-9]{10,11}$'),
    CONSTRAINT chkAccountsCitizenEmail CHECK (email ~* '^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$'),
    CONSTRAINT chkAccountsCitizenPcd CHECK (isPcd = false OR disabilityDescription IS NOT NULL),
    CONSTRAINT chkAccountsCitizenName CHECK (char_length(fullName) >= 3)
  );

  CREATE UNIQUE INDEX IF NOT EXISTS uqAccountsCitizenCpf ON accountsCitizen (cpf) WHERE deletedAt IS NULL;
  CREATE UNIQUE INDEX IF NOT EXISTS uqAccountsCitizenEmail ON accountsCitizen (lower(email)) WHERE deletedAt IS NULL;
  CREATE INDEX IF NOT EXISTS idxAccountsCitizenCity ON accountsCitizen (city, state);

  -- Função de autenticação cirúrgica de menor privilégio (sosp_security)
  CREATE OR REPLACE FUNCTION sosp_security.authenticate_citizen_by_cpf(p_cpf VARCHAR)
  RETURNS TABLE (
      citizen_id UUID,
      full_name VARCHAR,
      email VARCHAR,
      password_hash TEXT,
      is_active BOOLEAN,
      blocked_until TIMESTAMPTZ,
      login_attempts INT,
      role VARCHAR
  )
  LANGUAGE plpgsql
  SECURITY DEFINER
  SET search_path = pg_catalog, public
  AS $$
  BEGIN
      -- Validação estrita de entrada: exatamente 11 dígitos numéricos
      IF p_cpf IS NULL OR p_cpf !~ '^[0-9]{11}$' THEN
          RETURN;
      END IF;

      -- Retorna estritamente o cidadão correspondente ao CPF se ativo e não excluído logicamente
      -- Se a conta estiver bloqueada por força bruta (RN-29), não expõe o hash (retorna NULL)
      RETURN QUERY
      SELECT
          c.id AS citizen_id,
          c.fullName AS full_name,
          c.email AS email,
          CASE
              WHEN (c.blockedUntil IS NOT NULL AND c.blockedUntil > clock_timestamp()) THEN NULL::TEXT
              ELSE c.passwordHash
          END AS password_hash,
          c.isActive AS is_active,
          c.blockedUntil AS blocked_until,
          c.loginAttempts AS login_attempts,
          'citizen'::VARCHAR AS role
      FROM public.accountsCitizen c
      WHERE c.cpf = p_cpf
        AND c.isActive = true
        AND c.deletedAt IS NULL
      LIMIT 1;
  END;
  $$;

  REVOKE ALL ON FUNCTION sosp_security.authenticate_citizen_by_cpf(VARCHAR) FROM PUBLIC;
  DO $$
  BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sosp_runtime_role') THEN
      GRANT EXECUTE ON FUNCTION sosp_security.authenticate_citizen_by_cpf(VARCHAR) TO sosp_runtime_role;
    END IF;
  END;
  $$;
  COMMENT ON FUNCTION sosp_security.authenticate_citizen_by_cpf(VARCHAR) IS
  'SOSP: Autenticação de menor privilégio. Retorna credenciais do CPF exato sob LIMIT 1, sem elevar a role da sessão.';

  CREATE TABLE IF NOT EXISTS accountsInternalUser (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    cpf                 varchar(11) NOT NULL,
    fullName            varchar(120) NOT NULL,
    email               varchar(200) NOT NULL,
    registrationNumber  varchar(20) NOT NULL,
    agencyId            uuid,
    unitId              uuid,
    role                varchar(20) NOT NULL DEFAULT 'servant',
    canManageCatalog    boolean NOT NULL DEFAULT false,
    passwordHash        text NOT NULL,
    mustChangePassword  boolean NOT NULL DEFAULT true,
    isActive            boolean NOT NULL DEFAULT true,
    lastLoginAt         timestamptz,
    createdAt           timestamptz NOT NULL DEFAULT now(),
    updatedAt           timestamptz NOT NULL DEFAULT now(),
    deletedAt           timestamptz,
    CONSTRAINT chkAccountsInternalCpf CHECK (cpf ~ '^[0-9]{11}$'),
    CONSTRAINT chkAccountsInternalEmail CHECK (email ~* '^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$'),
    CONSTRAINT chkAccountsInternalRole CHECK (role IN ('superadmin', 'admin', 'gestor', 'manager', 'servant')),
    CONSTRAINT chkAccountsInternalName CHECK (char_length(fullName) >= 3)
  );

  CREATE UNIQUE INDEX IF NOT EXISTS uqAccountsInternalUserCpf ON accountsInternalUser (cpf) WHERE deletedAt IS NULL;
  CREATE UNIQUE INDEX IF NOT EXISTS uqAccountsInternalUserEmail ON accountsInternalUser (lower(email)) WHERE deletedAt IS NULL;
  CREATE UNIQUE INDEX IF NOT EXISTS uqAccountsInternalUserRegistration ON accountsInternalUser (registrationNumber) WHERE deletedAt IS NULL;
  CREATE INDEX IF NOT EXISTS idxAccountsInternalUserAgency ON accountsInternalUser (agencyId);
  CREATE INDEX IF NOT EXISTS idxAccountsInternalUserUnit ON accountsInternalUser (unitId);

  -- Função de autenticação cirúrgica de menor privilégio para usuários internos (sosp_security)
  CREATE OR REPLACE FUNCTION sosp_security.authenticate_internal_user_by_cpf(p_cpf VARCHAR)
  RETURNS TABLE (
      user_id UUID,
      full_name VARCHAR,
      email VARCHAR,
      registration_number VARCHAR,
      agency_id UUID,
      unit_id UUID,
      role VARCHAR,
      can_manage_catalog BOOLEAN,
      password_hash TEXT,
      is_active BOOLEAN
  )
  LANGUAGE plpgsql
  SECURITY DEFINER
  SET search_path = pg_catalog, public
  AS $$
  BEGIN
      IF p_cpf IS NULL OR p_cpf !~ '^[0-9]{11}$' THEN
          RETURN;
      END IF;

      RETURN QUERY
      SELECT
          u.id AS user_id,
          u.fullName AS full_name,
          u.email AS email,
          u.registrationNumber AS registration_number,
          u.agencyId AS agency_id,
          u.unitId AS unit_id,
          u.role AS role,
          u.canManageCatalog AS can_manage_catalog,
          u.passwordHash::TEXT AS password_hash,
          u.isActive AS is_active
      FROM public.accountsInternalUser u
      WHERE u.cpf = p_cpf
        AND u.isActive = true
        AND u.deletedAt IS NULL
      LIMIT 1;
  END;
  $$;

  REVOKE ALL ON FUNCTION sosp_security.authenticate_internal_user_by_cpf(VARCHAR) FROM PUBLIC;
  DO $$
  BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sosp_runtime_role') THEN
      GRANT EXECUTE ON FUNCTION sosp_security.authenticate_internal_user_by_cpf(VARCHAR) TO sosp_runtime_role;
    END IF;
  END;
  $$;
  COMMENT ON FUNCTION sosp_security.authenticate_internal_user_by_cpf(VARCHAR) IS
  'SOSP: Autenticação de usuários internos com menor privilégio (SECURITY DEFINER) sob RLS.';

  CREATE TABLE IF NOT EXISTS accountsSession (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    subjectType varchar(20) NOT NULL,
    subjectId   uuid NOT NULL,
    tokenHash   varchar(64) NOT NULL,
    ipAddress   inet,
    userAgent   varchar(500),
    expiresAt   timestamptz NOT NULL,
    revokedAt   timestamptz,
    createdAt   timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uqAccountsSessionToken UNIQUE (tokenHash),
    CONSTRAINT chkAccountsSessionSubject CHECK (subjectType IN ('citizen', 'internal'))
  );

  CREATE INDEX IF NOT EXISTS idxAccountsSessionSubject ON accountsSession (subjectType, subjectId);
  CREATE INDEX IF NOT EXISTS idxAccountsSessionExpiresAt ON accountsSession (expiresAt) WHERE revokedAt IS NULL;

  CREATE TABLE IF NOT EXISTS accountsLoginAttempt (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    cpf           varchar(11) NOT NULL,
    ipAddress     inet,
    wasSuccessful boolean NOT NULL DEFAULT false,
    attemptedAt   timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chkAccountsLoginAttemptCpf CHECK (cpf ~ '^[0-9]{11}$')
  );

  CREATE INDEX IF NOT EXISTS idxAccountsLoginAttemptCpf ON accountsLoginAttempt (cpf, attemptedAt DESC);

  CREATE TABLE IF NOT EXISTS accountsPasswordReset (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    internalUserId uuid NOT NULL,
    codeHash       varchar(255) NOT NULL,
    expiresAt      timestamptz NOT NULL,
    usedAt         timestamptz,
    createdAt      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT fkAccountsResetUser FOREIGN KEY (internalUserId) REFERENCES accountsInternalUser (id) ON DELETE CASCADE
  );

  CREATE INDEX IF NOT EXISTS idxAccountsPasswordResetUser ON accountsPasswordReset (internalUserId, expiresAt DESC);

  -- =============================================================================
  -- MÓDULO 2: CATALOG
  -- =============================================================================

  CREATE TABLE IF NOT EXISTS catalogAgency (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name        varchar(120) NOT NULL,
    acronym     varchar(10) NOT NULL,
    sphere      varchar(20) NOT NULL,
    description varchar(500),
    isActive    boolean NOT NULL DEFAULT true,
    createdAt   timestamptz NOT NULL DEFAULT now(),
    updatedAt   timestamptz NOT NULL DEFAULT now(),
    deletedAt   timestamptz,
    CONSTRAINT chkCatalogAgencySphere CHECK (sphere IN ('municipal', 'state', 'federal')),
    CONSTRAINT chkCatalogAgencyName CHECK (char_length(name) >= 2)
  );

  CREATE UNIQUE INDEX IF NOT EXISTS uqCatalogAgencyAcronymSphere ON catalogAgency (acronym, sphere) WHERE deletedAt IS NULL;
  CREATE INDEX IF NOT EXISTS idxCatalogAgencyNameTrgm ON catalogAgency USING GIN (name gin_trgm_ops);

  -- Adiciona FK de órgão em accountsInternalUser agora que catalogAgency existe
  DO $$
  BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fkaccountsinternalagency') THEN
      ALTER TABLE accountsInternalUser
        ADD CONSTRAINT fkAccountsInternalAgency FOREIGN KEY (agencyId) REFERENCES catalogAgency (id);
    END IF;
  END $$;

  CREATE TABLE IF NOT EXISTS catalogUnit (
    id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    agencyId           uuid NOT NULL,
    name               varchar(120) NOT NULL,
    zipCode            varchar(8) NOT NULL,
    street             varchar(120) NOT NULL,
    neighborhood       varchar(80) NOT NULL,
    city               varchar(80) NOT NULL,
    state              varchar(2) NOT NULL,
    addressNumber      varchar(10) NOT NULL,
    phone              varchar(11),
    email              varchar(200),
    latitude           numeric(9,6),
    longitude          numeric(9,6),
    isAccessible       boolean NOT NULL DEFAULT false,
    hasPriorityService boolean NOT NULL DEFAULT false,
    dailyLimit         integer NOT NULL DEFAULT 40,
    isActive           boolean NOT NULL DEFAULT true,
    createdAt          timestamptz NOT NULL DEFAULT now(),
    updatedAt          timestamptz NOT NULL DEFAULT now(),
    deletedAt          timestamptz,
    CONSTRAINT fkCatalogUnitAgency FOREIGN KEY (agencyId) REFERENCES catalogAgency (id),
    CONSTRAINT chkCatalogUnitZip CHECK (zipCode ~ '^[0-9]{8}$'),
    CONSTRAINT chkCatalogUnitState CHECK (state ~ '^[A-Z]{2}$'),
    CONSTRAINT chkCatalogUnitDailyLimit CHECK (dailyLimit > 0),
    CONSTRAINT chkCatalogUnitLat CHECK (latitude IS NULL OR (latitude BETWEEN -90 AND 90)),
    CONSTRAINT chkCatalogUnitLng CHECK (longitude IS NULL OR (longitude BETWEEN -180 AND 180))
  );

  CREATE UNIQUE INDEX IF NOT EXISTS uqCatalogUnitNameCity ON catalogUnit (agencyId, name, city) WHERE deletedAt IS NULL;
  CREATE INDEX IF NOT EXISTS idxCatalogUnitCity ON catalogUnit (city, state);
  CREATE INDEX IF NOT EXISTS idxCatalogUnitAgency ON catalogUnit (agencyId);

  -- Adiciona FK de unidade em accountsInternalUser agora que catalogUnit existe
  DO $$
  BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fkAccountsInternalUserUnit') THEN
      ALTER TABLE accountsInternalUser
        ADD CONSTRAINT fkAccountsInternalUserUnit FOREIGN KEY (unitId) REFERENCES catalogUnit (id) ON DELETE SET NULL;
    END IF;
  END;
  $$;

  CREATE TABLE IF NOT EXISTS catalogUnitOpeningHour (
    id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    unitId    uuid NOT NULL,
    weekday   smallint NOT NULL,
    opensAt   time NOT NULL,
    closesAt  time NOT NULL,
    CONSTRAINT fkCatalogHoursUnit FOREIGN KEY (unitId) REFERENCES catalogUnit (id) ON DELETE CASCADE,
    CONSTRAINT chkCatalogHoursWeekday CHECK (weekday BETWEEN 0 AND 6),
    CONSTRAINT chkCatalogHoursInterval CHECK (opensAt < closesAt),
    CONSTRAINT uqCatalogUnitWeekday UNIQUE (unitId, weekday)
  );

  CREATE TABLE IF NOT EXISTS catalogNonWorkingDay (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    unitId      uuid,
    dayDate     date NOT NULL,
    description varchar(120) NOT NULL,
    scope       varchar(20) NOT NULL DEFAULT 'national',
    createdAt   timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT fkCatalogNonWorkingUnit FOREIGN KEY (unitId) REFERENCES catalogUnit (id) ON DELETE CASCADE,
    CONSTRAINT chkCatalogNonWorkingScope CHECK (scope IN ('national', 'state', 'municipal', 'unit')),
    CONSTRAINT uqCatalogNonWorkingDay UNIQUE (unitId, dayDate)
  );

  CREATE INDEX IF NOT EXISTS idxCatalogNonWorkingDayDate ON catalogNonWorkingDay (dayDate);
  CREATE INDEX IF NOT EXISTS idxCatalogNonWorkingDayUnit ON catalogNonWorkingDay (unitId);

  CREATE TABLE IF NOT EXISTS catalogService (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name                varchar(150) NOT NULL,
    category            varchar(30) NOT NULL,
    detailedDescription text NOT NULL,
    eligibility         text NOT NULL,
    prerequisites       text,
    isFree              boolean NOT NULL DEFAULT true,
    costAmount          numeric(10,2),
    averageDeadlineDays integer NOT NULL DEFAULT 0,
    channel             varchar(20) NOT NULL DEFAULT 'inPerson',
    externalUrl         varchar(300),
    status              varchar(20) NOT NULL DEFAULT 'draft',
    currentVersion      integer NOT NULL DEFAULT 1,
    createdBy           uuid,
    createdAt           timestamptz NOT NULL DEFAULT now(),
    updatedAt           timestamptz NOT NULL DEFAULT now(),
    deletedAt           timestamptz,
    searchVector        tsvector,
    CONSTRAINT fkCatalogServiceCreatedBy FOREIGN KEY (createdBy) REFERENCES accountsInternalUser (id),
    CONSTRAINT chkCatalogServiceCost CHECK (
      (isFree = true AND costAmount IS NULL)
      OR (isFree = false AND costAmount BETWEEN 0.01 AND 99999.99)
    ),
    CONSTRAINT chkCatalogServiceDeadline CHECK (averageDeadlineDays >= 0),
    CONSTRAINT chkCatalogServiceChannel CHECK (channel IN ('online', 'inPerson', 'hybrid')),
    CONSTRAINT chkCatalogServiceStatus CHECK (status IN ('draft', 'active', 'inactive', 'archived')),
    CONSTRAINT chkCatalogServiceCategory CHECK (category IN (
      'health', 'education', 'documents', 'transport', 'socialAssistance', 'taxes', 'work', 'housing', 'environment', 'business', 'transit', 'general'
    ))
  );

  CREATE INDEX IF NOT EXISTS idxCatalogServiceSearchVector ON catalogService USING GIN (searchVector);
  CREATE INDEX IF NOT EXISTS idxCatalogServiceNameTrgm ON catalogService USING GIN (name gin_trgm_ops);
  CREATE INDEX IF NOT EXISTS idxCatalogServiceCategory ON catalogService (category) WHERE status = 'active';
  CREATE INDEX IF NOT EXISTS idxCatalogServiceChannel ON catalogService (channel) WHERE status = 'active';

  CREATE TABLE IF NOT EXISTS catalogServiceAgency (
    serviceId uuid NOT NULL,
    agencyId  uuid NOT NULL,
    CONSTRAINT pkCatalogServiceAgency PRIMARY KEY (serviceId, agencyId),
    CONSTRAINT fkServiceAgencyService FOREIGN KEY (serviceId) REFERENCES catalogService (id) ON DELETE CASCADE,
    CONSTRAINT fkServiceAgencyAgency FOREIGN KEY (agencyId) REFERENCES catalogAgency (id) ON DELETE CASCADE
  );

  CREATE INDEX IF NOT EXISTS idxCatalogServiceAgencyAgency ON catalogServiceAgency (agencyId);

  CREATE TABLE IF NOT EXISTS catalogUnitService (
    unitId    uuid NOT NULL,
    serviceId uuid NOT NULL,
    isActive  boolean NOT NULL DEFAULT true,
    createdAt timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT pkCatalogUnitService PRIMARY KEY (unitId, serviceId),
    CONSTRAINT fkUnitServiceUnit FOREIGN KEY (unitId) REFERENCES catalogUnit (id) ON DELETE CASCADE,
    CONSTRAINT fkUnitServiceService FOREIGN KEY (serviceId) REFERENCES catalogService (id) ON DELETE CASCADE
  );

  CREATE INDEX IF NOT EXISTS idxCatalogUnitServiceService ON catalogUnitService (serviceId);

  CREATE TABLE IF NOT EXISTS catalogServiceStep (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    serviceId     uuid NOT NULL,
    stepOrder     integer NOT NULL,
    title         varchar(100) NOT NULL,
    description   varchar(1000) NOT NULL,
    estimatedTime varchar(30),
    createdAt     timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT fkCatalogStepService FOREIGN KEY (serviceId) REFERENCES catalogService (id) ON DELETE CASCADE,
    CONSTRAINT uqCatalogStepOrder UNIQUE (serviceId, stepOrder),
    CONSTRAINT chkCatalogStepOrder CHECK (stepOrder > 0)
  );

  CREATE TABLE IF NOT EXISTS catalogServiceDocument (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    serviceId   uuid NOT NULL,
    name        varchar(120) NOT NULL,
    isMandatory boolean NOT NULL DEFAULT true,
    templateUrl varchar(500),
    createdAt   timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT fkCatalogDocService FOREIGN KEY (serviceId) REFERENCES catalogService (id) ON DELETE CASCADE,
    CONSTRAINT uqCatalogDocName UNIQUE (serviceId, name)
  );

  CREATE TABLE IF NOT EXISTS catalogFaq (
    id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    question  varchar(300) NOT NULL,
    answer    varchar(2000) NOT NULL,
    serviceId uuid,
    category  varchar(30),
    isActive  boolean NOT NULL DEFAULT true,
    createdAt timestamptz NOT NULL DEFAULT now(),
    updatedAt timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT fkCatalogFaqService FOREIGN KEY (serviceId) REFERENCES catalogService (id) ON DELETE SET NULL,
    CONSTRAINT chkCatalogFaqCategory CHECK (
      category IS NULL OR category IN ('health', 'education', 'documents', 'transport', 'socialAssistance', 'taxes', 'work', 'housing', 'environment', 'business', 'transit', 'general')
    )
  );

  CREATE INDEX IF NOT EXISTS idxCatalogFaqService ON catalogFaq (serviceId) WHERE isActive = true;
  CREATE INDEX IF NOT EXISTS idxCatalogFaqCategory ON catalogFaq (category) WHERE isActive = true;
  CREATE INDEX IF NOT EXISTS idxCatalogFaqQuestionTrgm ON catalogFaq USING GIN (question gin_trgm_ops);

  CREATE TABLE IF NOT EXISTS catalogServiceVersion (
    id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    serviceId uuid NOT NULL,
    version   integer NOT NULL,
    snapshot  jsonb NOT NULL,
    createdBy uuid,
    createdAt timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT fkCatalogVersionService FOREIGN KEY (serviceId) REFERENCES catalogService (id) ON DELETE CASCADE,
    CONSTRAINT fkCatalogVersionUser FOREIGN KEY (createdBy) REFERENCES accountsInternalUser (id),
    CONSTRAINT uqCatalogVersion UNIQUE (serviceId, version),
    CONSTRAINT chkCatalogVersionNumber CHECK (version > 0)
  );

  -- =============================================================================
  -- MÓDULO 3: SEARCH
  -- =============================================================================

  CREATE TABLE IF NOT EXISTS searchQueryLog (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    term        varchar(200) NOT NULL,
    filters     jsonb NOT NULL DEFAULT '{}'::jsonb,
    resultCount integer NOT NULL DEFAULT 0,
    sessionHash varchar(64),
    createdAt   timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chkSearchQueryLogCount CHECK (resultCount >= 0)
  );

  CREATE INDEX IF NOT EXISTS idxSearchQueryLogCreatedAt ON searchQueryLog (createdAt DESC);
  CREATE INDEX IF NOT EXISTS idxSearchQueryLogTermTrgm ON searchQueryLog USING GIN (term gin_trgm_ops);
  CREATE INDEX IF NOT EXISTS idxSearchQueryLogZero ON searchQueryLog (createdAt DESC) WHERE resultCount = 0;

  CREATE TABLE IF NOT EXISTS searchSynonym (
    id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    term      varchar(100) NOT NULL,
    synonyms  text NOT NULL,
    isActive  boolean NOT NULL DEFAULT true,
    createdAt timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uqSearchSynonymTerm UNIQUE (term)
  );

  -- =============================================================================
  -- MÓDULO 4: GUIDANCE
  -- =============================================================================

  CREATE TABLE IF NOT EXISTS guidanceProgress (
    id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    citizenId          uuid NOT NULL,
    serviceId          uuid NOT NULL,
    checkedDocumentIds jsonb NOT NULL DEFAULT '[]'::jsonb,
    startedAt          timestamptz NOT NULL DEFAULT now(),
    completedAt        timestamptz,
    updatedAt          timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT fkGuidanceProgressCitizen FOREIGN KEY (citizenId) REFERENCES accountsCitizen (id) ON DELETE CASCADE,
    CONSTRAINT fkGuidanceProgressService FOREIGN KEY (serviceId) REFERENCES catalogService (id) ON DELETE CASCADE,
    CONSTRAINT uqGuidanceCitizenService UNIQUE (citizenId, serviceId)
  );

  CREATE TABLE IF NOT EXISTS guidanceGeneratedPdf (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    citizenId     uuid NOT NULL,
    serviceId     uuid NOT NULL,
    fileUrl       varchar(500) NOT NULL,
    checklistHash varchar(64) NOT NULL,
    createdAt     timestamptz NOT NULL DEFAULT now(),
    expiresAt     timestamptz NOT NULL,
    CONSTRAINT fkGuidancePdfCitizen FOREIGN KEY (citizenId) REFERENCES accountsCitizen (id) ON DELETE CASCADE,
    CONSTRAINT fkGuidancePdfService FOREIGN KEY (serviceId) REFERENCES catalogService (id) ON DELETE CASCADE
  );

  CREATE INDEX IF NOT EXISTS idxGuidancePdfCitizen ON guidanceGeneratedPdf (citizenId, serviceId, createdAt DESC);

  -- =============================================================================
  -- MÓDULO 5: SCHEDULING
  -- =============================================================================

  CREATE TABLE IF NOT EXISTS schedulingSlot (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    unitId      uuid NOT NULL,
    slotDate    date NOT NULL,
    startsAt    time NOT NULL,
    endsAt      time NOT NULL,
    capacity    integer NOT NULL DEFAULT 1,
    bookedCount integer NOT NULL DEFAULT 0,
    createdAt   timestamptz NOT NULL DEFAULT now(),
    updatedAt   timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT fkSchedulingSlotUnit FOREIGN KEY (unitId) REFERENCES catalogUnit (id) ON DELETE CASCADE,
    CONSTRAINT uqSchedulingSlotUnitTime UNIQUE (unitId, slotDate, startsAt),
    CONSTRAINT chkSchedulingSlotCapacity CHECK (capacity > 0),
    CONSTRAINT chkSchedulingSlotBooked CHECK (bookedCount >= 0 AND bookedCount <= capacity),
    CONSTRAINT chkSchedulingSlotInterval CHECK (startsAt < endsAt)
  );

  CREATE INDEX IF NOT EXISTS idxSchedulingSlotUnitDate ON schedulingSlot (unitId, slotDate);

  CREATE TABLE IF NOT EXISTS schedulingAppointment (
    id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    protocolNumber     varchar(13) NOT NULL,
    citizenId          uuid NOT NULL,
    serviceId          uuid NOT NULL,
    unitId             uuid NOT NULL,
    slotId             uuid NOT NULL,
    scheduledDate      date NOT NULL,
    scheduledTime      time NOT NULL,
    status             varchar(20) NOT NULL DEFAULT 'scheduled',
    cancellationReason varchar(500),
    rescheduledFromId  uuid,
    createdAt          timestamptz NOT NULL DEFAULT now(),
    updatedAt          timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT fkSchedulingApptSlot FOREIGN KEY (slotId) REFERENCES schedulingSlot (id),
    CONSTRAINT fkSchedulingApptCitizen FOREIGN KEY (citizenId) REFERENCES accountsCitizen (id),
    CONSTRAINT fkSchedulingApptService FOREIGN KEY (serviceId) REFERENCES catalogService (id),
    CONSTRAINT fkSchedulingApptUnit FOREIGN KEY (unitId) REFERENCES catalogUnit (id),
    CONSTRAINT fkSchedulingApptRescheduled FOREIGN KEY (rescheduledFromId) REFERENCES schedulingAppointment (id),
    CONSTRAINT uqSchedulingApptProtocol UNIQUE (protocolNumber),
    CONSTRAINT chkSchedulingApptProtocol CHECK (protocolNumber ~ '^[0-9]{8}-[0-9]{4}$'),
    CONSTRAINT chkSchedulingApptStatus CHECK (status IN ('scheduled', 'confirmed', 'completed', 'cancelled', 'noShow'))
  );

  CREATE UNIQUE INDEX IF NOT EXISTS uqSchedulingAppointmentActive
    ON schedulingAppointment (citizenId, serviceId)
    WHERE status IN ('scheduled', 'confirmed');

  CREATE INDEX IF NOT EXISTS idxSchedulingAppointmentCitizen ON schedulingAppointment (citizenId, scheduledDate DESC);
  CREATE INDEX IF NOT EXISTS idxSchedulingAppointmentUnitDate ON schedulingAppointment (unitId, scheduledDate);
  CREATE INDEX IF NOT EXISTS idxSchedulingAppointmentSlot ON schedulingAppointment (slotId);

  CREATE TABLE IF NOT EXISTS schedulingProtocol (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    protocolNumber varchar(13) NOT NULL,
    protocolType   varchar(20) NOT NULL DEFAULT 'appointment',
    citizenId      uuid NOT NULL,
    appointmentId  uuid,
    status         varchar(30) NOT NULL DEFAULT 'received',
    openedAt       timestamptz NOT NULL DEFAULT now(),
    closedAt       timestamptz,
    createdAt      timestamptz NOT NULL DEFAULT now(),
    updatedAt      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uqSchedulingProtocolNumber UNIQUE (protocolNumber),
    CONSTRAINT fkSchedulingProtCitizen FOREIGN KEY (citizenId) REFERENCES accountsCitizen (id),
    CONSTRAINT fkSchedulingProtAppt FOREIGN KEY (appointmentId) REFERENCES schedulingAppointment (id),
    CONSTRAINT chkSchedulingProtType CHECK (protocolType IN ('appointment', 'question')),
    CONSTRAINT chkSchedulingProtNumber CHECK (protocolNumber ~ '^[0-9]{8}-[0-9]{4}$'),
    CONSTRAINT chkSchedulingProtStatus CHECK (status IN ('received', 'inReview', 'waitingDocument', 'scheduled', 'completed', 'cancelled'))
  );

  CREATE INDEX IF NOT EXISTS idxSchedulingProtocolCitizen ON schedulingProtocol (citizenId, openedAt DESC);
  CREATE INDEX IF NOT EXISTS idxSchedulingProtocolStatus ON schedulingProtocol (status, openedAt DESC);

  CREATE TABLE IF NOT EXISTS schedulingProtocolAttachment (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    protocolId      uuid NOT NULL,
    citizenId       uuid,
    filename        varchar(255) NOT NULL,
    storageKey      varchar(500) NOT NULL,
    mimeType        varchar(100) NOT NULL,
    fileSize        integer NOT NULL,
    antivirusStatus varchar(20) NOT NULL DEFAULT 'pending',
    createdAt       timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT fkSchedulingAttachmentProtocol FOREIGN KEY (protocolId) REFERENCES schedulingProtocol (id) ON DELETE CASCADE,
    CONSTRAINT chkSchedulingAttachmentMime CHECK (mimeType IN ('image/jpeg', 'image/png', 'application/pdf')),
    CONSTRAINT chkSchedulingAttachmentSize CHECK (fileSize BETWEEN 1024 AND 10485760)
  );

  CREATE INDEX IF NOT EXISTS idxSchedulingAttachmentProtocol ON schedulingProtocolAttachment (protocolId);

  CREATE TABLE IF NOT EXISTS schedulingProtocolTransition (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    protocolId uuid NOT NULL,
    fromStatus varchar(30),
    toStatus   varchar(30) NOT NULL,
    actorType  varchar(20) NOT NULL,
    actorId    uuid,
    note       varchar(1000),
    createdAt  timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT fkSchedulingTransitionProtocol FOREIGN KEY (protocolId) REFERENCES schedulingProtocol (id) ON DELETE CASCADE,
    CONSTRAINT chkSchedulingTransFrom CHECK (fromStatus IS NULL OR fromStatus IN ('received', 'inReview', 'waitingDocument', 'scheduled', 'completed', 'cancelled')),
    CONSTRAINT chkSchedulingTransTo CHECK (toStatus IN ('received', 'inReview', 'waitingDocument', 'scheduled', 'completed', 'cancelled')),
    CONSTRAINT chkSchedulingTransActor CHECK (actorType IN ('citizen', 'servant', 'system'))
  );

  CREATE INDEX IF NOT EXISTS idxSchedulingTransitionProtocol ON schedulingProtocolTransition (protocolId, createdAt);

  -- =============================================================================
  -- MÓDULO 6: FEEDBACK
  -- =============================================================================

  CREATE TABLE IF NOT EXISTS feedbackReview (
    id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    protocolId       uuid NOT NULL,
    citizenId        uuid NOT NULL,
    serviceId        uuid NOT NULL,
    unitId           uuid NOT NULL,
    rating           smallint NOT NULL,
    reviewComment    varchar(500),
    moderationStatus varchar(20) NOT NULL DEFAULT 'pending',
    createdAt        timestamptz NOT NULL DEFAULT now(),
    updatedAt        timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT fkFeedbackReviewProtocol FOREIGN KEY (protocolId) REFERENCES schedulingProtocol (id),
    CONSTRAINT fkFeedbackReviewCitizen FOREIGN KEY (citizenId) REFERENCES accountsCitizen (id),
    CONSTRAINT fkFeedbackReviewService FOREIGN KEY (serviceId) REFERENCES catalogService (id),
    CONSTRAINT fkFeedbackReviewUnit FOREIGN KEY (unitId) REFERENCES catalogUnit (id),
    CONSTRAINT uqFeedbackReviewProtocol UNIQUE (protocolId),
    CONSTRAINT chkFeedbackReviewRating CHECK (rating BETWEEN 1 AND 5),
    CONSTRAINT chkFeedbackReviewModeration CHECK (moderationStatus IN ('pending', 'approved', 'rejected'))
  );

  CREATE INDEX IF NOT EXISTS idxFeedbackReviewService ON feedbackReview (serviceId, createdAt DESC);

  CREATE TABLE IF NOT EXISTS feedbackReviewReport (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    reviewId   uuid NOT NULL,
    reportedBy uuid NOT NULL,
    reason     varchar(500) NOT NULL,
    status     varchar(20) NOT NULL DEFAULT 'pending',
    createdAt  timestamptz NOT NULL DEFAULT now(),
    resolvedAt timestamptz,
    CONSTRAINT fkFeedbackReportReview FOREIGN KEY (reviewId) REFERENCES feedbackReview (id) ON DELETE CASCADE,
    CONSTRAINT chkFeedbackReportStatus CHECK (status IN ('pending', 'accepted', 'rejected'))
  );

  CREATE TABLE IF NOT EXISTS feedbackQuestion (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    protocolId    uuid NOT NULL,
    citizenId     uuid NOT NULL,
    serviceId     uuid,
    subject       varchar(200) NOT NULL,
    message       varchar(2000) NOT NULL,
    attachmentUrl varchar(500),
    answer        varchar(2000),
    answeredBy    uuid,
    answeredAt    timestamptz,
    createdAt     timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT fkFeedbackQuestionProtocol FOREIGN KEY (protocolId) REFERENCES schedulingProtocol (id),
    CONSTRAINT fkFeedbackQuestionCitizen FOREIGN KEY (citizenId) REFERENCES accountsCitizen (id),
    CONSTRAINT fkFeedbackQuestionService FOREIGN KEY (serviceId) REFERENCES catalogService (id),
    CONSTRAINT uqFeedbackQuestionProtocol UNIQUE (protocolId)
  );

  -- =============================================================================
  -- MÓDULO 7: NOTIFICATIONS
  -- =============================================================================

  CREATE TABLE IF NOT EXISTS notificationsTemplate (
    id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code      varchar(60) NOT NULL,
    channel   varchar(20) NOT NULL,
    subject   varchar(200),
    body      text NOT NULL,
    isActive  boolean NOT NULL DEFAULT true,
    createdAt timestamptz NOT NULL DEFAULT now(),
    updatedAt timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uqNotificationsTemplateCode UNIQUE (code),
    CONSTRAINT chkNotificationsTemplateChannel CHECK (channel IN ('email', 'push', 'sms', 'whatsapp'))
  );

  CREATE TABLE IF NOT EXISTS notificationsPreference (
    id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    citizenId        uuid NOT NULL,
    notificationType varchar(40) NOT NULL,
    channel          varchar(20) NOT NULL,
    isOptIn          boolean NOT NULL DEFAULT true,
    updatedAt        timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT fkNotificationsPreferenceCitizen FOREIGN KEY (citizenId) REFERENCES accountsCitizen (id) ON DELETE CASCADE,
    CONSTRAINT uqNotificationsPreference UNIQUE (citizenId, notificationType, channel),
    CONSTRAINT chkNotificationsPreferenceChannel CHECK (channel IN ('email', 'push', 'sms', 'whatsapp'))
  );

  CREATE TABLE IF NOT EXISTS notificationsDelivery (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    citizenId    uuid NOT NULL,
    channel      varchar(20) NOT NULL,
    templateCode varchar(60) NOT NULL,
    status       varchar(20) NOT NULL DEFAULT 'queued',
    payload      jsonb NOT NULL DEFAULT '{}'::jsonb,
    errorMessage varchar(500),
    sentAt       timestamptz,
    createdAt    timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT fkNotificationsDeliveryCitizen FOREIGN KEY (citizenId) REFERENCES accountsCitizen (id) ON DELETE CASCADE,
    CONSTRAINT chkNotificationsDeliveryChannel CHECK (channel IN ('email', 'push', 'sms', 'whatsapp')),
    CONSTRAINT chkNotificationsDeliveryStatus CHECK (status IN ('queued', 'sent', 'failed'))
  );

  CREATE INDEX IF NOT EXISTS idxNotificationsDeliveryStatus ON notificationsDelivery (status, createdAt);

  CREATE TABLE IF NOT EXISTS notificationsPushSubscription (
    id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    citizenId uuid NOT NULL,
    endpoint  varchar(500) NOT NULL,
    p256dh    varchar(255) NOT NULL,
    auth      varchar(255) NOT NULL,
    createdAt timestamptz NOT NULL DEFAULT now(),
    revokedAt timestamptz,
    CONSTRAINT fkNotificationsPushCitizen FOREIGN KEY (citizenId) REFERENCES accountsCitizen (id) ON DELETE CASCADE,
    CONSTRAINT uqNotificationsPushEndpoint UNIQUE (endpoint)
  );

  -- =============================================================================
  -- MÓDULO 8: REPORTS
  -- =============================================================================

  CREATE TABLE IF NOT EXISTS reportsExport (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    requestedBy uuid NOT NULL,
    reportType  varchar(40) NOT NULL,
    filters     jsonb NOT NULL DEFAULT '{}'::jsonb,
    status      varchar(20) NOT NULL DEFAULT 'queued',
    fileUrl     varchar(500),
    createdAt   timestamptz NOT NULL DEFAULT now(),
    completedAt timestamptz,
    CONSTRAINT fkReportsExportUser FOREIGN KEY (requestedBy) REFERENCES accountsInternalUser (id),
    CONSTRAINT chkReportsExportStatus CHECK (status IN ('queued', 'processing', 'done', 'failed'))
  );

  CREATE INDEX IF NOT EXISTS idxReportsExportUser ON reportsExport (requestedBy, createdAt DESC);

  -- =============================================================================
  -- MÓDULO 9: AUDIT
  -- =============================================================================

  CREATE TABLE IF NOT EXISTS auditEvent (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    actorType  varchar(20) NOT NULL,
    actorId    uuid,
    action     varchar(80) NOT NULL,
    entityType varchar(80) NOT NULL,
    entityId   uuid,
    beforeData jsonb,
    afterData  jsonb,
    ipAddress  inet,
    userAgent  varchar(500),
    createdAt  timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT chkAuditEventActorType CHECK (actorType IN ('citizen', 'servant', 'system', 'anonymous'))
  );

  CREATE INDEX IF NOT EXISTS idxAuditEventEntity ON auditEvent (entityType, entityId, createdAt DESC);
  CREATE INDEX IF NOT EXISTS idxAuditEventCreatedAt ON auditEvent (createdAt DESC);
  CREATE INDEX IF NOT EXISTS idxAuditEventActor ON auditEvent (actorType, actorId, createdAt DESC);

  CREATE TABLE IF NOT EXISTS auditDataSubjectRequest (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    citizenId   uuid NOT NULL,
    requestType varchar(20) NOT NULL,
    status      varchar(20) NOT NULL DEFAULT 'open',
    notes       text,
    requestedAt timestamptz NOT NULL DEFAULT now(),
    completedAt timestamptz,
    CONSTRAINT fkAuditDataSubjectCitizen FOREIGN KEY (citizenId) REFERENCES accountsCitizen (id),
    CONSTRAINT chkAuditDataSubjectType CHECK (requestType IN ('access', 'correction', 'deletion', 'portability')),
    CONSTRAINT chkAuditDataSubjectStatus CHECK (status IN ('open', 'inProgress', 'done', 'rejected'))
  );

  CREATE INDEX IF NOT EXISTS idxAuditDataSubjectCitizen ON auditDataSubjectRequest (citizenId, requestedAt DESC);

  -- =============================================================================
  -- VISTAS (VIEWS)
  -- =============================================================================

  -- View 1: Busca Unificada de Serviços no Catálogo
  CREATE OR REPLACE VIEW vw_catalogServiceSearch WITH (security_invoker = true) AS
  SELECT 
    s.id AS serviceId,
    s.name AS serviceName,
    s.category,
    s.detailedDescription,
    s.eligibility,
    s.channel,
    s.status,
    s.searchVector,
    a.id AS agencyId,
    a.name AS agencyName,
    a.acronym AS agencyAcronym,
    coalesce(string_agg(DISTINCT syn.term, ' '), '') AS synonymsList
  FROM catalogService s
  LEFT JOIN catalogServiceAgency csa ON s.id = csa.serviceId
  LEFT JOIN catalogAgency a ON csa.agencyId = a.id
  LEFT JOIN searchSynonym syn ON syn.isActive = true AND syn.term ILIKE '%' || s.category || '%'
  WHERE s.deletedAt IS NULL AND (a.deletedAt IS NULL OR a.id IS NULL)
  GROUP BY s.id, a.id;

  -- View 2: Disponibilidade em Tempo Real de Slots de Agendamento por Unidade
  CREATE OR REPLACE VIEW vw_schedulingSlotAvailability WITH (security_invoker = true) AS
  SELECT 
    slot.id AS slotId,
    slot.unitId,
    u.name AS unitName,
    u.city,
    u.state,
    slot.slotDate,
    slot.startsAt,
    slot.endsAt,
    slot.capacity,
    slot.bookedCount,
    (slot.capacity - slot.bookedCount) AS availableSlots,
    CASE WHEN (slot.capacity - slot.bookedCount) > 0 THEN true ELSE false END AS isAvailable
  FROM schedulingSlot slot
  JOIN catalogUnit u ON slot.unitId = u.id
  WHERE u.isActive = true AND u.deletedAt IS NULL;

  -- =============================================================================
  -- TRIGGERS PARA ATUALIZAÇÃO AUTOMÁTICA DE UPDATEDAT
  -- =============================================================================

  DROP TRIGGER IF EXISTS trgSetUpdatedAtAccountsGender ON accountsGender;
  CREATE TRIGGER trgSetUpdatedAtAccountsGender BEFORE UPDATE ON accountsGender FOR EACH ROW EXECUTE FUNCTION setUpdatedAt();

  DROP TRIGGER IF EXISTS trgSetUpdatedAtAccountsCitizen ON accountsCitizen;
  CREATE TRIGGER trgSetUpdatedAtAccountsCitizen BEFORE UPDATE ON accountsCitizen FOR EACH ROW EXECUTE FUNCTION setUpdatedAt();

  DROP TRIGGER IF EXISTS trgSetUpdatedAtAccountsInternalUser ON accountsInternalUser;
  CREATE TRIGGER trgSetUpdatedAtAccountsInternalUser BEFORE UPDATE ON accountsInternalUser FOR EACH ROW EXECUTE FUNCTION setUpdatedAt();

  DROP TRIGGER IF EXISTS trgSetUpdatedAtCatalogAgency ON catalogAgency;
  CREATE TRIGGER trgSetUpdatedAtCatalogAgency BEFORE UPDATE ON catalogAgency FOR EACH ROW EXECUTE FUNCTION setUpdatedAt();

  DROP TRIGGER IF EXISTS trgSetUpdatedAtCatalogUnit ON catalogUnit;
  CREATE TRIGGER trgSetUpdatedAtCatalogUnit BEFORE UPDATE ON catalogUnit FOR EACH ROW EXECUTE FUNCTION setUpdatedAt();

  DROP TRIGGER IF EXISTS trgSetUpdatedAtCatalogService ON catalogService;
  CREATE TRIGGER trgSetUpdatedAtCatalogService BEFORE UPDATE ON catalogService FOR EACH ROW EXECUTE FUNCTION setUpdatedAt();

  DROP TRIGGER IF EXISTS trgSetUpdatedAtCatalogFaq ON catalogFaq;
  CREATE TRIGGER trgSetUpdatedAtCatalogFaq BEFORE UPDATE ON catalogFaq FOR EACH ROW EXECUTE FUNCTION setUpdatedAt();

  DROP TRIGGER IF EXISTS trgSetUpdatedAtGuidanceProgress ON guidanceProgress;
  CREATE TRIGGER trgSetUpdatedAtGuidanceProgress BEFORE UPDATE ON guidanceProgress FOR EACH ROW EXECUTE FUNCTION setUpdatedAt();

  DROP TRIGGER IF EXISTS trgSetUpdatedAtSchedulingSlot ON schedulingSlot;
  CREATE TRIGGER trgSetUpdatedAtSchedulingSlot BEFORE UPDATE ON schedulingSlot FOR EACH ROW EXECUTE FUNCTION setUpdatedAt();

  DROP TRIGGER IF EXISTS trgSetUpdatedAtSchedulingAppointment ON schedulingAppointment;
  CREATE TRIGGER trgSetUpdatedAtSchedulingAppointment BEFORE UPDATE ON schedulingAppointment FOR EACH ROW EXECUTE FUNCTION setUpdatedAt();

  DROP TRIGGER IF EXISTS trgSetUpdatedAtSchedulingProtocol ON schedulingProtocol;
  CREATE TRIGGER trgSetUpdatedAtSchedulingProtocol BEFORE UPDATE ON schedulingProtocol FOR EACH ROW EXECUTE FUNCTION setUpdatedAt();

  DROP TRIGGER IF EXISTS trgSetUpdatedAtFeedbackReview ON feedbackReview;
  CREATE TRIGGER trgSetUpdatedAtFeedbackReview BEFORE UPDATE ON feedbackReview FOR EACH ROW EXECUTE FUNCTION setUpdatedAt();

  DROP TRIGGER IF EXISTS trgSetUpdatedAtNotificationsTemplate ON notificationsTemplate;
  CREATE TRIGGER trgSetUpdatedAtNotificationsTemplate BEFORE UPDATE ON notificationsTemplate FOR EACH ROW EXECUTE FUNCTION setUpdatedAt();

  DROP TRIGGER IF EXISTS trgSetUpdatedAtNotificationsPreference ON notificationsPreference;
  CREATE TRIGGER trgSetUpdatedAtNotificationsPreference BEFORE UPDATE ON notificationsPreference FOR EACH ROW EXECUTE FUNCTION setUpdatedAt();

  -- =============================================================================
  -- SEGURANÇA: HABILITAÇÃO DO ROW LEVEL SECURITY (RLS - DEFESA EM PROFUNDIDADE)
  -- =============================================================================

  ALTER TABLE accountsGender ENABLE ROW LEVEL SECURITY;
  ALTER TABLE accountsCitizen ENABLE ROW LEVEL SECURITY;
  ALTER TABLE accountsInternalUser ENABLE ROW LEVEL SECURITY;
  ALTER TABLE accountsSession ENABLE ROW LEVEL SECURITY;
  ALTER TABLE accountsLoginAttempt ENABLE ROW LEVEL SECURITY;
  ALTER TABLE accountsPasswordReset ENABLE ROW LEVEL SECURITY;
  ALTER TABLE catalogAgency ENABLE ROW LEVEL SECURITY;
  ALTER TABLE catalogUnit ENABLE ROW LEVEL SECURITY;
  ALTER TABLE catalogUnitOpeningHour ENABLE ROW LEVEL SECURITY;
  ALTER TABLE catalogNonWorkingDay ENABLE ROW LEVEL SECURITY;
  ALTER TABLE catalogService ENABLE ROW LEVEL SECURITY;
  ALTER TABLE catalogServiceAgency ENABLE ROW LEVEL SECURITY;
  ALTER TABLE catalogUnitService ENABLE ROW LEVEL SECURITY;
  ALTER TABLE catalogServiceStep ENABLE ROW LEVEL SECURITY;
  ALTER TABLE catalogServiceDocument ENABLE ROW LEVEL SECURITY;
  ALTER TABLE catalogFaq ENABLE ROW LEVEL SECURITY;
  ALTER TABLE catalogServiceVersion ENABLE ROW LEVEL SECURITY;
  ALTER TABLE searchQueryLog ENABLE ROW LEVEL SECURITY;
  ALTER TABLE searchSynonym ENABLE ROW LEVEL SECURITY;
  ALTER TABLE guidanceProgress ENABLE ROW LEVEL SECURITY;
  ALTER TABLE guidanceGeneratedPdf ENABLE ROW LEVEL SECURITY;
  ALTER TABLE schedulingSlot ENABLE ROW LEVEL SECURITY;
  ALTER TABLE schedulingAppointment ENABLE ROW LEVEL SECURITY;
  ALTER TABLE schedulingProtocol ENABLE ROW LEVEL SECURITY;
  ALTER TABLE schedulingProtocolAttachment ENABLE ROW LEVEL SECURITY;
  ALTER TABLE schedulingProtocolTransition ENABLE ROW LEVEL SECURITY;
  ALTER TABLE feedbackReview ENABLE ROW LEVEL SECURITY;
  ALTER TABLE feedbackReviewReport ENABLE ROW LEVEL SECURITY;
  ALTER TABLE feedbackQuestion ENABLE ROW LEVEL SECURITY;
  ALTER TABLE notificationsTemplate ENABLE ROW LEVEL SECURITY;
  ALTER TABLE notificationsPreference ENABLE ROW LEVEL SECURITY;
  ALTER TABLE notificationsDelivery ENABLE ROW LEVEL SECURITY;
  ALTER TABLE notificationsPushSubscription ENABLE ROW LEVEL SECURITY;
  ALTER TABLE reportsExport ENABLE ROW LEVEL SECURITY;
  ALTER TABLE auditEvent ENABLE ROW LEVEL SECURITY;
  ALTER TABLE auditDataSubjectRequest ENABLE ROW LEVEL SECURITY;

COMMIT;
