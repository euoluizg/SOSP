-- =============================================================================
-- SOSP — Sistema de Orientação para Serviços Públicos
-- Schema DDL — PostgreSQL 17+
--
-- Convenção: identificadores em camelCase, SEM aspas duplas.
-- O PostgreSQL dobra identificadores não citados para minúsculas; portanto o
-- nome físico no catálogo é a versão minúscula (catalogservice, userid).
-- Ver ADR-002. Nunca crie identificador com aspas.
--
-- Produção: PostgreSQL 17 gerenciado no Supabase (região sa-east-1), schema
-- `public`. O Supabase é usado SOMENTE como banco: Auth, Data API e Realtime
-- ficam desabilitados e o Django é a única porta de escrita (ADR-008). A RLS
-- é defesa em profundidade, não o mecanismo principal de autorização.
--
-- Execução:
--   createdb sosp
--   psql -d sosp -v ON_ERROR_STOP=1 -f docs/database/schema.sql
-- =============================================================================

BEGIN;

CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Configuração de busca em português sem acento.
-- "certidão" e "certidao" passam a produzir o mesmo lexema.
DROP TEXT SEARCH CONFIGURATION IF EXISTS sospPortuguese;
CREATE TEXT SEARCH CONFIGURATION sospPortuguese (COPY = portuguese);
ALTER TEXT SEARCH CONFIGURATION sospPortuguese
  ALTER MAPPING FOR hword, hword_part, word
  WITH unaccent, portuguese_stem;

-- -----------------------------------------------------------------------------
-- Função de atualização de updatedAt
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION setUpdatedAt()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updatedAt = now();
  RETURN NEW;
END;
$$;

-- =============================================================================
-- MÓDULO accounts
-- =============================================================================

CREATE TABLE accountsGender (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name        varchar(40) NOT NULL,
  sortOrder   smallint NOT NULL DEFAULT 0,
  isActive    boolean NOT NULL DEFAULT true,
  createdAt   timestamptz NOT NULL DEFAULT now(),
  updatedAt   timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uqAccountsGenderName UNIQUE (name)
);

CREATE TABLE accountsCitizen (
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

CREATE UNIQUE INDEX uqAccountsCitizenCpf ON accountsCitizen (cpf) WHERE deletedAt IS NULL;
CREATE UNIQUE INDEX uqAccountsCitizenEmail ON accountsCitizen (lower(email)) WHERE deletedAt IS NULL;
-- v2.0: índice único desligado até FEATURE_GOVBR_INTEGRATION_ENABLED ser ativada
-- CREATE UNIQUE INDEX uqAccountsCitizenGovbr ON accountsCitizen (govbrSubjectId) WHERE govbrSubjectId IS NOT NULL;
CREATE INDEX idxAccountsCitizenCity ON accountsCitizen (city, state);

CREATE TABLE accountsInternalUser (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  cpf                 varchar(11) NOT NULL,
  fullName            varchar(120) NOT NULL,
  email               varchar(200) NOT NULL,
  registrationNumber  varchar(20) NOT NULL,
  agencyId            uuid,
  role                varchar(20) NOT NULL,
  canManageCatalog    boolean NOT NULL DEFAULT false,
  passwordHash        varchar(255) NOT NULL,
  mustChangePassword  boolean NOT NULL DEFAULT true,
  isActive            boolean NOT NULL DEFAULT true,
  lastLoginAt         timestamptz,
  createdAt           timestamptz NOT NULL DEFAULT now(),
  updatedAt           timestamptz NOT NULL DEFAULT now(),
  deletedAt           timestamptz,
  CONSTRAINT chkAccountsInternalUserRole CHECK (role IN ('administrator', 'servant')),
  CONSTRAINT chkAccountsInternalUserCpf CHECK (cpf ~ '^[0-9]{11}$'),
  CONSTRAINT chkAccountsInternalUserRegistration CHECK (registrationNumber ~ '^[A-Za-z0-9]{1,20}$')
);

CREATE UNIQUE INDEX uqAccountsInternalUserCpf ON accountsInternalUser (cpf) WHERE deletedAt IS NULL;
CREATE UNIQUE INDEX uqAccountsInternalUserEmail ON accountsInternalUser (lower(email)) WHERE deletedAt IS NULL;
CREATE UNIQUE INDEX uqAccountsInternalUserRegistration ON accountsInternalUser (registrationNumber) WHERE deletedAt IS NULL;
CREATE INDEX idxAccountsInternalUserAgency ON accountsInternalUser (agencyId);

CREATE TABLE accountsSession (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  subjectType  varchar(20) NOT NULL,
  subjectId    uuid NOT NULL,
  tokenHash    varchar(64) NOT NULL,
  ipAddress    inet,
  userAgent    varchar(500),
  expiresAt    timestamptz NOT NULL,
  revokedAt    timestamptz,
  createdAt    timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT chkAccountsSessionSubjectType CHECK (subjectType IN ('citizen', 'internal')),
  CONSTRAINT uqAccountsSessionToken UNIQUE (tokenHash)
);

CREATE INDEX idxAccountsSessionSubject ON accountsSession (subjectType, subjectId);
CREATE INDEX idxAccountsSessionExpiresAt ON accountsSession (expiresAt) WHERE revokedAt IS NULL;

CREATE TABLE accountsLoginAttempt (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  cpf           varchar(11) NOT NULL,
  ipAddress     inet,
  wasSuccessful boolean NOT NULL DEFAULT false,
  attemptedAt   timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT chkAccountsLoginAttemptCpf CHECK (cpf ~ '^[0-9]{11}$')
);

CREATE INDEX idxAccountsLoginAttemptCpf ON accountsLoginAttempt (cpf, attemptedAt DESC);

CREATE TABLE accountsPasswordReset (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  internalUserId uuid NOT NULL,
  codeHash       varchar(255) NOT NULL,
  expiresAt      timestamptz NOT NULL,
  usedAt         timestamptz,
  createdAt      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT fkAccountsPasswordResetUser FOREIGN KEY (internalUserId) REFERENCES accountsInternalUser (id) ON DELETE CASCADE
);

CREATE INDEX idxAccountsPasswordResetUser ON accountsPasswordReset (internalUserId, expiresAt DESC);

-- =============================================================================
-- MÓDULO catalog
-- =============================================================================

CREATE TABLE catalogAgency (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name        varchar(120) NOT NULL,
  acronym     varchar(10) NOT NULL,
  sphere      varchar(20) NOT NULL,
  description varchar(500),
  isActive    boolean NOT NULL DEFAULT true,
  createdAt   timestamptz NOT NULL DEFAULT now(),
  updatedAt   timestamptz NOT NULL DEFAULT now(),
  deletedAt   timestamptz,
  CONSTRAINT chkCatalogAgencySphere CHECK (sphere IN ('municipal', 'state', 'federal'))
);

CREATE UNIQUE INDEX uqCatalogAgencyAcronymSphere ON catalogAgency (acronym, sphere) WHERE deletedAt IS NULL;
CREATE INDEX idxCatalogAgencyNameTrgm ON catalogAgency USING GIN (name gin_trgm_ops);

CREATE TABLE catalogUnit (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  agencyId            uuid NOT NULL,
  name                varchar(120) NOT NULL,
  zipCode             varchar(8) NOT NULL,
  street              varchar(120) NOT NULL,
  neighborhood        varchar(80) NOT NULL,
  city                varchar(80) NOT NULL,
  state               varchar(2) NOT NULL,
  addressNumber       varchar(10) NOT NULL,
  phone               varchar(11),
  email               varchar(200),
  latitude            numeric(9,6),
  longitude           numeric(9,6),
  isAccessible        boolean NOT NULL DEFAULT false,
  hasPriorityService  boolean NOT NULL DEFAULT false,
  dailyLimit          integer NOT NULL DEFAULT 40,
  isActive            boolean NOT NULL DEFAULT true,
  createdAt           timestamptz NOT NULL DEFAULT now(),
  updatedAt           timestamptz NOT NULL DEFAULT now(),
  deletedAt           timestamptz,
  CONSTRAINT fkCatalogUnitAgency FOREIGN KEY (agencyId) REFERENCES catalogAgency (id),
  CONSTRAINT chkCatalogUnitZip CHECK (zipCode ~ '^[0-9]{8}$'),
  CONSTRAINT chkCatalogUnitState CHECK (state ~ '^[A-Z]{2}$'),
  CONSTRAINT chkCatalogUnitLatitude CHECK (latitude IS NULL OR latitude BETWEEN -90 AND 90),
  CONSTRAINT chkCatalogUnitLongitude CHECK (longitude IS NULL OR longitude BETWEEN -180 AND 180),
  CONSTRAINT chkCatalogUnitDailyLimit CHECK (dailyLimit > 0)
);

CREATE UNIQUE INDEX uqCatalogUnitNameCity ON catalogUnit (agencyId, name, city) WHERE deletedAt IS NULL;
CREATE INDEX idxCatalogUnitCity ON catalogUnit (city, state);
CREATE INDEX idxCatalogUnitAgency ON catalogUnit (agencyId);

CREATE TABLE catalogUnitOpeningHour (
  id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  unitId    uuid NOT NULL,
  weekday   smallint NOT NULL,
  opensAt   time NOT NULL,
  closesAt  time NOT NULL,
  CONSTRAINT fkCatalogUnitOpeningHourUnit FOREIGN KEY (unitId) REFERENCES catalogUnit (id) ON DELETE CASCADE,
  CONSTRAINT chkCatalogUnitOpeningHourWeekday CHECK (weekday BETWEEN 0 AND 6),
  CONSTRAINT chkCatalogUnitOpeningHourRange CHECK (opensAt < closesAt),
  CONSTRAINT uqCatalogUnitOpeningHour UNIQUE (unitId, weekday)
);

CREATE TABLE catalogNonWorkingDay (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  unitId      uuid,
  dayDate     date NOT NULL,
  description varchar(120) NOT NULL,
  scope       varchar(20) NOT NULL,
  createdAt   timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT fkCatalogNonWorkingDayUnit FOREIGN KEY (unitId) REFERENCES catalogUnit (id) ON DELETE CASCADE,
  CONSTRAINT chkCatalogNonWorkingDayScope CHECK (scope IN ('national', 'state', 'municipal', 'unit')),
  CONSTRAINT chkCatalogNonWorkingDayUnit CHECK (scope <> 'unit' OR unitId IS NOT NULL)
);

CREATE INDEX idxCatalogNonWorkingDayDate ON catalogNonWorkingDay (dayDate);
CREATE INDEX idxCatalogNonWorkingDayUnit ON catalogNonWorkingDay (unitId);

CREATE TABLE catalogService (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name                varchar(150) NOT NULL,
  category            varchar(30) NOT NULL,
  detailedDescription text NOT NULL,
  eligibility         text NOT NULL,
  prerequisites       text,
  isFree              boolean NOT NULL DEFAULT true,
  costAmount          numeric(10,2),
  averageDeadlineDays integer NOT NULL,
  channel             varchar(20) NOT NULL,
  externalUrl         varchar(300),
  status              varchar(20) NOT NULL DEFAULT 'draft',
  currentVersion      integer NOT NULL DEFAULT 1,
  createdBy           uuid,
  createdAt           timestamptz NOT NULL DEFAULT now(),
  updatedAt           timestamptz NOT NULL DEFAULT now(),
  deletedAt           timestamptz,
  searchVector        tsvector GENERATED ALWAYS AS (
    to_tsvector(
      'sospPortuguese',
      coalesce(name, '') || ' ' ||
      coalesce(detailedDescription, '') || ' ' ||
      coalesce(eligibility, '')
    )
  ) STORED,
  CONSTRAINT fkCatalogServiceCreatedBy FOREIGN KEY (createdBy) REFERENCES accountsInternalUser (id),
  CONSTRAINT chkCatalogServiceCategory CHECK (
    category IN ('health', 'education', 'documents', 'transport', 'socialAssistance', 'taxes', 'work')
  ),
  CONSTRAINT chkCatalogServiceChannel CHECK (channel IN ('online', 'inPerson', 'hybrid')),
  CONSTRAINT chkCatalogServiceStatus CHECK (status IN ('draft', 'active', 'inactive')),
  CONSTRAINT chkCatalogServiceCost CHECK (
    (isFree = true AND costAmount IS NULL)
    OR (isFree = false AND costAmount BETWEEN 0.01 AND 99999.99)
  ),
  CONSTRAINT chkCatalogServiceDeadline CHECK (averageDeadlineDays BETWEEN 0 AND 365),
  CONSTRAINT chkCatalogServiceExternalUrl CHECK (
    channel = 'inPerson' OR (externalUrl IS NOT NULL AND externalUrl LIKE 'https://%')
  )
);

CREATE INDEX idxCatalogServiceSearchVector ON catalogService USING GIN (searchVector);
CREATE INDEX idxCatalogServiceNameTrgm ON catalogService USING GIN (name gin_trgm_ops);
CREATE INDEX idxCatalogServiceCategory ON catalogService (category) WHERE status = 'active';
CREATE INDEX idxCatalogServiceChannel ON catalogService (channel) WHERE status = 'active';

CREATE TABLE catalogServiceAgency (
  serviceId uuid NOT NULL,
  agencyId  uuid NOT NULL,
  PRIMARY KEY (serviceId, agencyId),
  CONSTRAINT fkCatalogServiceAgencyService FOREIGN KEY (serviceId) REFERENCES catalogService (id) ON DELETE CASCADE,
  CONSTRAINT fkCatalogServiceAgencyAgency FOREIGN KEY (agencyId) REFERENCES catalogAgency (id) ON DELETE CASCADE
);

CREATE INDEX idxCatalogServiceAgencyAgency ON catalogServiceAgency (agencyId);

CREATE TABLE catalogServiceStep (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  serviceId     uuid NOT NULL,
  stepOrder     integer NOT NULL,
  title         varchar(100) NOT NULL,
  description   varchar(1000) NOT NULL,
  estimatedTime varchar(30),
  createdAt     timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT fkCatalogServiceStepService FOREIGN KEY (serviceId) REFERENCES catalogService (id) ON DELETE CASCADE,
  CONSTRAINT chkCatalogServiceStepOrder CHECK (stepOrder > 0),
  CONSTRAINT uqCatalogServiceStepOrder UNIQUE (serviceId, stepOrder)
);

CREATE TABLE catalogServiceDocument (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  serviceId    uuid NOT NULL,
  name         varchar(120) NOT NULL,
  isMandatory  boolean NOT NULL DEFAULT true,
  templateUrl  varchar(500),
  createdAt    timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT fkCatalogServiceDocumentService FOREIGN KEY (serviceId) REFERENCES catalogService (id) ON DELETE CASCADE,
  CONSTRAINT uqCatalogServiceDocumentName UNIQUE (serviceId, name)
);

CREATE TABLE catalogFaq (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  question   varchar(300) NOT NULL,
  answer     varchar(2000) NOT NULL,
  serviceId  uuid,
  category   varchar(30),
  isActive   boolean NOT NULL DEFAULT true,
  createdAt  timestamptz NOT NULL DEFAULT now(),
  updatedAt  timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT fkCatalogFaqService FOREIGN KEY (serviceId) REFERENCES catalogService (id) ON DELETE CASCADE,
  CONSTRAINT chkCatalogFaqLink CHECK (serviceId IS NOT NULL OR category IS NOT NULL),
  CONSTRAINT chkCatalogFaqCategory CHECK (
    category IS NULL OR category IN ('health', 'education', 'documents', 'transport', 'socialAssistance', 'taxes', 'work')
  )
);

CREATE INDEX idxCatalogFaqService ON catalogFaq (serviceId) WHERE isActive = true;
CREATE INDEX idxCatalogFaqCategory ON catalogFaq (category) WHERE isActive = true;
CREATE INDEX idxCatalogFaqQuestionTrgm ON catalogFaq USING GIN (question gin_trgm_ops);

CREATE TABLE catalogServiceVersion (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  serviceId  uuid NOT NULL,
  version    integer NOT NULL,
  snapshot   jsonb NOT NULL,
  createdBy  uuid,
  createdAt  timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT fkCatalogServiceVersionService FOREIGN KEY (serviceId) REFERENCES catalogService (id) ON DELETE CASCADE,
  CONSTRAINT fkCatalogServiceVersionCreatedBy FOREIGN KEY (createdBy) REFERENCES accountsInternalUser (id),
  CONSTRAINT uqCatalogServiceVersion UNIQUE (serviceId, version),
  CONSTRAINT chkCatalogServiceVersionNumber CHECK (version > 0)
);

-- =============================================================================
-- MÓDULO search
-- =============================================================================

CREATE TABLE searchQueryLog (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  term         varchar(200) NOT NULL,
  filters      jsonb NOT NULL DEFAULT '{}'::jsonb,
  resultCount  integer NOT NULL DEFAULT 0,
  sessionHash  varchar(64),
  createdAt    timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT chkSearchQueryLogCount CHECK (resultCount >= 0)
);

CREATE INDEX idxSearchQueryLogCreatedAt ON searchQueryLog (createdAt DESC);
CREATE INDEX idxSearchQueryLogTermTrgm ON searchQueryLog USING GIN (term gin_trgm_ops);
CREATE INDEX idxSearchQueryLogZero ON searchQueryLog (createdAt DESC) WHERE resultCount = 0;

CREATE TABLE searchSynonym (
  id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  term      varchar(100) NOT NULL,
  synonyms  text[] NOT NULL,
  isActive  boolean NOT NULL DEFAULT true,
  createdAt timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uqSearchSynonymTerm UNIQUE (term),
  CONSTRAINT chkSearchSynonymNotEmpty CHECK (array_length(synonyms, 1) >= 1)
);

-- =============================================================================
-- MÓDULO guidance
-- =============================================================================

CREATE TABLE guidanceProgress (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  citizenId          uuid NOT NULL,
  serviceId          uuid NOT NULL,
  checkedDocumentIds uuid[] NOT NULL DEFAULT '{}'::uuid[],
  startedAt          timestamptz NOT NULL DEFAULT now(),
  completedAt        timestamptz,
  updatedAt          timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT fkGuidanceProgressCitizen FOREIGN KEY (citizenId) REFERENCES accountsCitizen (id) ON DELETE CASCADE,
  CONSTRAINT fkGuidanceProgressService FOREIGN KEY (serviceId) REFERENCES catalogService (id) ON DELETE CASCADE,
  CONSTRAINT uqGuidanceProgress UNIQUE (citizenId, serviceId)
);

CREATE TABLE guidanceGeneratedPdf (
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

CREATE INDEX idxGuidancePdfCitizen ON guidanceGeneratedPdf (citizenId, serviceId, createdAt DESC);

-- =============================================================================
-- MÓDULO scheduling
-- =============================================================================

CREATE TABLE schedulingSlot (
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
  CONSTRAINT uqSchedulingSlot UNIQUE (unitId, slotDate, startsAt),
  CONSTRAINT chkSchedulingSlotRange CHECK (startsAt < endsAt),
  CONSTRAINT chkSchedulingSlotCapacity CHECK (capacity > 0),
  CONSTRAINT chkSchedulingSlotBooked CHECK (bookedCount >= 0 AND bookedCount <= capacity)
);

CREATE INDEX idxSchedulingSlotUnitDate ON schedulingSlot (unitId, slotDate);

CREATE TABLE schedulingAppointment (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  protocolNumber     varchar(13) NOT NULL,
  citizenId          uuid NOT NULL,
  serviceId          uuid NOT NULL,
  unitId             uuid NOT NULL,
  scheduledDate      date NOT NULL,
  scheduledTime      time NOT NULL,
  status             varchar(20) NOT NULL DEFAULT 'scheduled',
  cancellationReason varchar(500),
  rescheduledFromId  uuid,
  createdAt          timestamptz NOT NULL DEFAULT now(),
  updatedAt          timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT fkSchedulingAppointmentCitizen FOREIGN KEY (citizenId) REFERENCES accountsCitizen (id),
  CONSTRAINT fkSchedulingAppointmentService FOREIGN KEY (serviceId) REFERENCES catalogService (id),
  CONSTRAINT fkSchedulingAppointmentUnit FOREIGN KEY (unitId) REFERENCES catalogUnit (id),
  CONSTRAINT fkSchedulingAppointmentRescheduled FOREIGN KEY (rescheduledFromId) REFERENCES schedulingAppointment (id),
  CONSTRAINT uqSchedulingAppointmentProtocol UNIQUE (protocolNumber),
  CONSTRAINT chkSchedulingAppointmentProtocol CHECK (protocolNumber ~ '^[0-9]{8}-[0-9]{4}$'),
  CONSTRAINT chkSchedulingAppointmentStatus CHECK (
    status IN ('scheduled', 'confirmed', 'completed', 'cancelled', 'noShow')
  ),
  CONSTRAINT chkSchedulingAppointmentCancel CHECK (
    status <> 'cancelled' OR cancellationReason IS NOT NULL
  )
);

CREATE UNIQUE INDEX uqSchedulingAppointmentActive
  ON schedulingAppointment (citizenId, serviceId)
  WHERE status IN ('scheduled', 'confirmed');

CREATE INDEX idxSchedulingAppointmentCitizen ON schedulingAppointment (citizenId, scheduledDate DESC);
CREATE INDEX idxSchedulingAppointmentUnitDate ON schedulingAppointment (unitId, scheduledDate);

CREATE TABLE schedulingProtocol (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  protocolNumber varchar(13) NOT NULL,
  protocolType   varchar(20) NOT NULL,
  citizenId      uuid NOT NULL,
  appointmentId  uuid,
  status         varchar(30) NOT NULL DEFAULT 'received',
  openedAt       timestamptz NOT NULL DEFAULT now(),
  closedAt       timestamptz,
  createdAt      timestamptz NOT NULL DEFAULT now(),
  updatedAt      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT fkSchedulingProtocolCitizen FOREIGN KEY (citizenId) REFERENCES accountsCitizen (id),
  CONSTRAINT fkSchedulingProtocolAppointment FOREIGN KEY (appointmentId) REFERENCES schedulingAppointment (id),
  CONSTRAINT uqSchedulingProtocolNumber UNIQUE (protocolNumber),
  CONSTRAINT uqSchedulingProtocolAppointment UNIQUE (appointmentId),
  CONSTRAINT chkSchedulingProtocolType CHECK (protocolType IN ('appointment', 'question')),
  CONSTRAINT chkSchedulingProtocolStatus CHECK (
    status IN ('received', 'inReview', 'waitingDocument', 'scheduled', 'completed', 'cancelled')
  ),
  CONSTRAINT chkSchedulingProtocolLink CHECK (
    (protocolType = 'appointment' AND appointmentId IS NOT NULL)
    OR (protocolType = 'question' AND appointmentId IS NULL)
  )
);

CREATE INDEX idxSchedulingProtocolCitizen ON schedulingProtocol (citizenId, openedAt DESC);
CREATE INDEX idxSchedulingProtocolStatus ON schedulingProtocol (status, openedAt DESC);

CREATE TABLE schedulingProtocolTransition (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  protocolId uuid NOT NULL,
  fromStatus varchar(30),
  toStatus   varchar(30) NOT NULL,
  actorType  varchar(20) NOT NULL,
  actorId    uuid,
  note       varchar(1000),
  createdAt  timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT fkSchedulingTransitionProtocol FOREIGN KEY (protocolId) REFERENCES schedulingProtocol (id) ON DELETE CASCADE,
  CONSTRAINT chkSchedulingTransitionActor CHECK (actorType IN ('citizen', 'servant', 'system')),
  CONSTRAINT chkSchedulingTransitionStatus CHECK (
    toStatus IN ('received', 'inReview', 'waitingDocument', 'scheduled', 'completed', 'cancelled')
  )
);

CREATE INDEX idxSchedulingTransitionProtocol ON schedulingProtocolTransition (protocolId, createdAt);

-- =============================================================================
-- MÓDULO feedback
-- =============================================================================

CREATE TABLE feedbackReview (
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

CREATE INDEX idxFeedbackReviewService ON feedbackReview (serviceId, createdAt DESC);

CREATE TABLE feedbackReviewReport (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  reviewId   uuid NOT NULL,
  reportedBy uuid NOT NULL,
  reason     varchar(500) NOT NULL,
  status     varchar(20) NOT NULL DEFAULT 'pending',
  createdAt  timestamptz NOT NULL DEFAULT now(),
  resolvedAt timestamptz,
  CONSTRAINT fkFeedbackReportReview FOREIGN KEY (reviewId) REFERENCES feedbackReview (id) ON DELETE CASCADE,
  CONSTRAINT fkFeedbackReportUser FOREIGN KEY (reportedBy) REFERENCES accountsInternalUser (id),
  CONSTRAINT chkFeedbackReportStatus CHECK (status IN ('pending', 'accepted', 'rejected'))
);

CREATE TABLE feedbackQuestion (
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
  CONSTRAINT fkFeedbackQuestionAnsweredBy FOREIGN KEY (answeredBy) REFERENCES accountsInternalUser (id),
  CONSTRAINT uqFeedbackQuestionProtocol UNIQUE (protocolId)
);

-- =============================================================================
-- MÓDULO notifications
-- =============================================================================

CREATE TABLE notificationsTemplate (
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

CREATE TABLE notificationsPreference (
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

CREATE TABLE notificationsDelivery (
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

CREATE INDEX idxNotificationsDeliveryStatus ON notificationsDelivery (status, createdAt);

CREATE TABLE notificationsPushSubscription (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  citizenId  uuid NOT NULL,
  endpoint   varchar(500) NOT NULL,
  p256dh     varchar(255) NOT NULL,
  auth       varchar(255) NOT NULL,
  createdAt  timestamptz NOT NULL DEFAULT now(),
  revokedAt  timestamptz,
  CONSTRAINT fkNotificationsPushCitizen FOREIGN KEY (citizenId) REFERENCES accountsCitizen (id) ON DELETE CASCADE,
  CONSTRAINT uqNotificationsPushEndpoint UNIQUE (endpoint)
);

-- =============================================================================
-- MÓDULO reports
-- =============================================================================

CREATE TABLE reportsExport (
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

CREATE INDEX idxReportsExportUser ON reportsExport (requestedBy, createdAt DESC);

-- =============================================================================
-- MÓDULO audit
-- =============================================================================

CREATE TABLE auditEvent (
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

CREATE INDEX idxAuditEventEntity ON auditEvent (entityType, entityId, createdAt DESC);
CREATE INDEX idxAuditEventCreatedAt ON auditEvent (createdAt DESC);
CREATE INDEX idxAuditEventActor ON auditEvent (actorType, actorId, createdAt DESC);

CREATE TABLE auditDataSubjectRequest (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  citizenId   uuid NOT NULL,
  requestType varchar(20) NOT NULL,
  status      varchar(20) NOT NULL DEFAULT 'open',
  requestedAt timestamptz NOT NULL DEFAULT now(),
  completedAt timestamptz,
  notes       varchar(2000),
  CONSTRAINT fkAuditSubjectRequestCitizen FOREIGN KEY (citizenId) REFERENCES accountsCitizen (id),
  CONSTRAINT chkAuditSubjectRequestType CHECK (requestType IN ('access', 'correction', 'deletion', 'portability')),
  CONSTRAINT chkAuditSubjectRequestStatus CHECK (status IN ('open', 'inProgress', 'done', 'rejected'))
);

-- =============================================================================
-- CHAVES ESTRANGEIRAS ENTRE MÓDULOS
-- Declaradas após a criação de todas as tabelas para preservar a ordem de
-- dependência e deixar explícita a fronteira entre accounts e catalog.
-- =============================================================================

ALTER TABLE accountsInternalUser
  ADD CONSTRAINT fkAccountsInternalUserAgency
  FOREIGN KEY (agencyId) REFERENCES catalogAgency (id);

-- =============================================================================
-- TRIGGERS DE updatedAt
-- =============================================================================

CREATE TRIGGER trgAccountsCitizenUpdatedAt BEFORE UPDATE ON accountsCitizen
  FOR EACH ROW EXECUTE FUNCTION setUpdatedAt();
CREATE TRIGGER trgAccountsInternalUserUpdatedAt BEFORE UPDATE ON accountsInternalUser
  FOR EACH ROW EXECUTE FUNCTION setUpdatedAt();
CREATE TRIGGER trgCatalogAgencyUpdatedAt BEFORE UPDATE ON catalogAgency
  FOR EACH ROW EXECUTE FUNCTION setUpdatedAt();
CREATE TRIGGER trgCatalogUnitUpdatedAt BEFORE UPDATE ON catalogUnit
  FOR EACH ROW EXECUTE FUNCTION setUpdatedAt();
CREATE TRIGGER trgCatalogServiceUpdatedAt BEFORE UPDATE ON catalogService
  FOR EACH ROW EXECUTE FUNCTION setUpdatedAt();
CREATE TRIGGER trgCatalogFaqUpdatedAt BEFORE UPDATE ON catalogFaq
  FOR EACH ROW EXECUTE FUNCTION setUpdatedAt();
CREATE TRIGGER trgGuidanceProgressUpdatedAt BEFORE UPDATE ON guidanceProgress
  FOR EACH ROW EXECUTE FUNCTION setUpdatedAt();
CREATE TRIGGER trgSchedulingSlotUpdatedAt BEFORE UPDATE ON schedulingSlot
  FOR EACH ROW EXECUTE FUNCTION setUpdatedAt();
CREATE TRIGGER trgSchedulingAppointmentUpdatedAt BEFORE UPDATE ON schedulingAppointment
  FOR EACH ROW EXECUTE FUNCTION setUpdatedAt();
CREATE TRIGGER trgSchedulingProtocolUpdatedAt BEFORE UPDATE ON schedulingProtocol
  FOR EACH ROW EXECUTE FUNCTION setUpdatedAt();
CREATE TRIGGER trgFeedbackReviewUpdatedAt BEFORE UPDATE ON feedbackReview
  FOR EACH ROW EXECUTE FUNCTION setUpdatedAt();
CREATE TRIGGER trgNotificationsTemplateUpdatedAt BEFORE UPDATE ON notificationsTemplate
  FOR EACH ROW EXECUTE FUNCTION setUpdatedAt();
CREATE TRIGGER trgNotificationsPreferenceUpdatedAt BEFORE UPDATE ON notificationsPreference
  FOR EACH ROW EXECUTE FUNCTION setUpdatedAt();

-- =============================================================================
-- DADOS INICIAIS
-- =============================================================================

INSERT INTO accountsGender (name, sortOrder) VALUES
  ('Feminino', 1),
  ('Masculino', 2),
  ('Não binário', 3),
  ('Outro', 4),
  ('Prefiro não informar', 5);

INSERT INTO notificationsTemplate (code, channel, subject, body) VALUES
  ('accountCreated', 'email', 'Sua conta no SOSP foi criada',
   'Olá, {nome}! Seu cadastro foi realizado com sucesso. Use seu CPF e senha para acessar o sistema.'),
  ('appointmentCreated', 'email', 'Agendamento confirmado',
   'Agendamento confirmado! Protocolo {protocolo}: {serviço}, em {unidade}, no dia {data} às {hora}. Leve os documentos originais.'),
  ('appointmentReminder', 'email', 'Lembrete do seu atendimento',
   'Lembrete: seu atendimento ({serviço}) é amanhã, {data} às {hora}, em {unidade}. Protocolo {protocolo}.'),
  ('protocolStatusChanged', 'email', 'Seu protocolo foi atualizado',
   'Seu protocolo {protocolo} mudou para: {status}. Acesse o sistema para ver os detalhes.'),
  ('questionAnswered', 'email', 'Sua dúvida foi respondida',
   'Sua dúvida (protocolo {protocolo}) foi respondida. Acesse o sistema para ler a resposta.');

INSERT INTO searchSynonym (term, synonyms) VALUES
  ('rg', ARRAY['carteira de identidade', 'documento de identidade', 'identidade']),
  ('cpf', ARRAY['cadastro de pessoa física', 'documento cpf']),
  ('sus', ARRAY['sistema único de saúde', 'saúde pública']),
  ('inss', ARRAY['instituto nacional do seguro social', 'aposentadoria', 'benefício']),
  ('detran', ARRAY['departamento estadual de trânsito', 'habilitação', 'cnh']),
  ('crás', ARRAY['centro de referência de assistência social', 'assistência social']),
  ('certidão', ARRAY['certidao', 'nascimento', 'casamento', 'óbito']);

COMMIT;

-- =============================================================================
-- VERIFICAÇÃO DE CONVENÇÃO (deve retornar zero linhas)
-- =============================================================================
-- SELECT table_schema, table_name, column_name
-- FROM information_schema.columns
-- WHERE table_schema = 'public'
--   AND (table_name ~ '[A-Z]' OR column_name ~ '[A-Z]');
