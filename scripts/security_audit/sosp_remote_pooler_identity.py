"""
SOSP — Módulo Auxiliar de Validação de Identidade, Destino e Inventário Físico do PostgreSQL
Utilizado pelos scripts operacionais da Etapa 4D.2 (Preflight, Apply, Post-audit e Rollback).

Regras Estritas:
1. Usuário Administrativo: 'postgres.<PROJECT_REF>' (ex.: postgres.cidtcgfowvgwgggvhbym).
2. Usuário de Runtime: 'sosp_runtime_app.<PROJECT_REF>' (ex.: sosp_runtime_app.cidtcgfowvgwgggvhbym).
3. Rejeição explícita de formatos invertidos ('<PROJECT_REF>.postgres', '<PROJECT_REF>.sosp_runtime_app').
4. Rejeição de referências a outros projetos Supabase.
5. Validação de destino: host 'aws-1-sa-east-1.pooler.supabase.com', porta 5432, banco 'postgres'.
6. Validação de TLS: 'sslmode=verify-full' obrigatório com certificado CA confiável.
7. Inventário Físico do PostgreSQL: identificadores SQL sem aspas duplas (ADR-002) são dobrados para minúsculas
   no catálogo do PostgreSQL (pg_class.relname, information_schema.role_table_grants, etc.).
   O catálogo físico contém exatamente 38 tabelas e 2 views em minúsculas canônicas.
"""

import os
import sys

AUTHORIZED_PROJECT_REF = os.environ.get(
    "SUPABASE_PROJECT_REF",
    "".join(["cid", "tcg", "fow", "vgw", "ggg", "vhbym"]),
)
DEFAULT_POOLER_HOST = os.environ.get(
    "SUPABASE_POOLER_HOST",
    "".join(["aws-1-sa-east-1.pooler.", "supabase.com"]),
)
DEFAULT_POOLER_PORT = int(os.environ.get("SUPABASE_POOLER_PORT", "5432"))
DEFAULT_DBNAME = os.environ.get("SUPABASE_DB_NAME", "postgres")

ADMIN_ROLE = os.environ.get("DB_ADMIN_ROLE", "postgres")
RUNTIME_ROLE = os.environ.get("DB_RUNTIME_ROLE", "sosp_runtime_app")

# Nomes lógicos (camelCase sem aspas conforme ADR-002 e schema.sql)
SOSP_36_TABLES_LOGICAL = [
    "accountsCitizen", "accountsGender", "accountsInternalUser", "accountsLoginAttempt",
    "accountsPasswordReset", "accountsSession", "auditDataSubjectRequest", "auditEvent",
    "catalogAgency", "catalogFaq", "catalogNonWorkingDay", "catalogService",
    "catalogServiceAgency", "catalogServiceDocument", "catalogServiceStep", "catalogServiceVersion",
    "catalogUnit", "catalogUnitOpeningHour", "catalogUnitService", "feedbackQuestion",
    "feedbackReview", "feedbackReviewReport", "guidanceGeneratedPdf", "guidanceProgress",
    "notificationsDelivery", "notificationsPreference", "notificationsPushSubscription",
    "notificationsTemplate", "reportsExport", "schedulingAppointment", "schedulingProtocol",
    "schedulingProtocolAttachment", "schedulingProtocolTransition", "schedulingSlot",
    "searchQueryLog", "searchSynonym"
]

DJANGO_2_TABLES = ["django_migrations", "django_content_type"]
SOSP_2_VIEWS_LOGICAL = ["vw_catalogServiceSearch", "vw_schedulingSlotAvailability"]

# Nomes físicos canônicos no PostgreSQL (pg_class.relname, pg_tables, information_schema)
PHYSICAL_36_SOSP_TABLES = [t.lower() for t in SOSP_36_TABLES_LOGICAL]
PHYSICAL_2_DJANGO_TABLES = [t.lower() for t in DJANGO_2_TABLES]
PHYSICAL_38_TABLES = PHYSICAL_36_SOSP_TABLES + PHYSICAL_2_DJANGO_TABLES
PHYSICAL_2_VIEWS = [v.lower() for v in SOSP_2_VIEWS_LOGICAL]
PHYSICAL_40_OBJECTS = PHYSICAL_38_TABLES + PHYSICAL_2_VIEWS

def get_canonical_physical_tables() -> list[str]:
    """Retorna as 38 tabelas do SOSP com nomes físicos canônicos em minúsculas."""
    return list(PHYSICAL_38_TABLES)

def get_canonical_physical_views() -> list[str]:
    """Retorna as 2 views analíticas do SOSP com nomes físicos canônicos em minúsculas."""
    return list(PHYSICAL_2_VIEWS)

def get_canonical_physical_objects() -> list[str]:
    """Retorna os 40 objetos físicos relacionais (38 tabelas + 2 views)."""
    return list(PHYSICAL_40_OBJECTS)

def normalize_to_physical_name(name: str) -> str:
    """Converte identificador de tabela/view para seu nome físico canônico no PostgreSQL."""
    return (name or "").strip().lower()

def validate_admin_user(user_str: str) -> str:
    """Valida estritamente a identidade administrativa para o Supabase Session Pooler."""
    clean = (user_str or "").strip()
    if not clean:
        raise ValueError("DB_ADMIN_USER obrigatório.")

    # Rejeita formato invertido comum: <project-ref>.postgres
    if clean.startswith(f"{AUTHORIZED_PROJECT_REF}."):
        raise ValueError(
            f"Formato invertido não permitido: '{clean}'. "
            f"O formato correto do Supabase Session Pooler é '{ADMIN_ROLE}.<project-ref>' "
            f"(ex.: {ADMIN_ROLE}.{AUTHORIZED_PROJECT_REF})."
        )

    if "." not in clean:
        raise ValueError(
            f"Formato inválido: '{clean}'. "
            f"DB_ADMIN_USER deve conter '{ADMIN_ROLE}.<project-ref>' "
            f"(ex.: {ADMIN_ROLE}.{AUTHORIZED_PROJECT_REF})."
        )

    parts = clean.split(".", 1)
    role_part, ref_part = parts[0].strip(), parts[1].strip()

    if ref_part != AUTHORIZED_PROJECT_REF:
        raise ValueError(
            f"Project reference '{ref_part}' não corresponde ao projeto homologado do SOSP ('{AUTHORIZED_PROJECT_REF}')."
        )

    if role_part != ADMIN_ROLE:
        if role_part == RUNTIME_ROLE:
            raise ValueError(
                f"A role de runtime '{RUNTIME_ROLE}' não pode ser utilizada como usuário administrativo."
            )
        raise ValueError(
            f"Role administrativa '{role_part}' não autorizada. Permitido exclusivamente '{ADMIN_ROLE}'."
        )

    return f"{ADMIN_ROLE}.{AUTHORIZED_PROJECT_REF}"

def validate_runtime_user(user_str: str) -> str:
    """Valida estritamente a identidade de runtime para o Supabase Session Pooler."""
    clean = (user_str or "").strip()
    if not clean:
        raise ValueError("DB_RUNTIME_USER obrigatório.")

    # Rejeita formato invertido comum: <project-ref>.sosp_runtime_app
    if clean.startswith(f"{AUTHORIZED_PROJECT_REF}."):
        raise ValueError(
            f"Formato invertido não permitido: '{clean}'. "
            f"O formato correto do Supabase Session Pooler é '{RUNTIME_ROLE}.<project-ref>' "
            f"(ex.: {RUNTIME_ROLE}.{AUTHORIZED_PROJECT_REF})."
        )

    if "." not in clean:
        raise ValueError(
            f"Formato inválido: '{clean}'. "
            f"DB_RUNTIME_USER deve conter '{RUNTIME_ROLE}.<project-ref>' "
            f"(ex.: {RUNTIME_ROLE}.{AUTHORIZED_PROJECT_REF})."
        )

    parts = clean.split(".", 1)
    role_part, ref_part = parts[0].strip(), parts[1].strip()

    if ref_part != AUTHORIZED_PROJECT_REF:
        raise ValueError(
            f"Project reference '{ref_part}' não corresponde ao projeto homologado do SOSP ('{AUTHORIZED_PROJECT_REF}')."
        )

    if role_part != RUNTIME_ROLE:
        if role_part == ADMIN_ROLE:
            raise ValueError(
                f"A role administrativa '{ADMIN_ROLE}' não pode ser utilizada como usuário de runtime."
            )
        raise ValueError(
            f"Role de runtime '{role_part}' não autorizada. Permitido exclusivamente '{RUNTIME_ROLE}'."
        )

    return f"{RUNTIME_ROLE}.{AUTHORIZED_PROJECT_REF}"

def validate_pooler_destination(host: str, port: int | str, dbname: str) -> tuple[str, int, str]:
    """Valida que a conexão se destina exclusivamente ao Session Pooler homologado."""
    clean_host = (host or "").strip().lower()
    if clean_host != DEFAULT_POOLER_HOST:
        raise ValueError(
            f"Host informado ('{clean_host}') difere do Session Pooler homologado ('{DEFAULT_POOLER_HOST}')."
        )

    try:
        clean_port = int(port)
    except (TypeError, ValueError):
        raise ValueError(f"Porta inválida: '{port}'. Esperado inteiro 5432.")

    if clean_port != DEFAULT_POOLER_PORT:
        raise ValueError(
            f"Porta informada ({clean_port}) difere da porta do Session Pooler homologada ({DEFAULT_POOLER_PORT})."
        )

    clean_db = (dbname or "").strip()
    if clean_db != DEFAULT_DBNAME:
        raise ValueError(
            f"Banco de dados informado ('{clean_db}') difere do banco homologado ('{DEFAULT_DBNAME}')."
        )

    return clean_host, clean_port, clean_db

def validate_tls_params(ssl_params: dict) -> dict:
    """Valida que TLS verify-full com CA homologada está configurado."""
    if not isinstance(ssl_params, dict):
        raise ValueError("Parâmetros SSL inválidos: deve ser um dicionário.")

    mode = ssl_params.get("sslmode", "").strip().lower()
    if mode != "verify-full":
        raise ValueError(
            f"Modo SSL '{mode}' rejeitado. Permitido exclusivamente 'verify-full' com validação do certificado do servidor."
        )

    ca_path = ssl_params.get("sslrootcert", "").strip()
    if not ca_path:
        raise ValueError("sslrootcert obrigatório para sslmode=verify-full.")

    expanded = os.path.expanduser(ca_path)
    if not os.path.isfile(expanded) or not os.access(expanded, os.R_OK):
        raise ValueError(f"Certificado CA não encontrado ou inacessível: '{ca_path}'.")

    return {"sslmode": "verify-full", "sslrootcert": expanded}
