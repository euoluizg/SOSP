import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get(
    "SECRET_KEY", "django-insecure-sosp-backend-development-secret-key-2026"
)

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0", "testserver"]

# Aplicações instaladas (Monólito Modular — ADR-001)
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    # Módulos de Domínio SOSP
    "apps.accounts",
    "apps.catalog",
    "apps.search",
    "apps.guidance",
    "apps.scheduling",
    "apps.feedback",
    "apps.notifications",
    "apps.reports",
    "apps.audit",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Configuração de Banco de Dados Multi-ambiente (ADR-001, ADR-002, Etapa 3 e Etapa 4A)
# Suporta SQLite em memória (padrão para testes offline/CI) e PostgreSQL (local/isolado/Supabase)
from django.core.exceptions import ImproperlyConfigured

raw_db_engine = os.environ.get("DB_ENGINE", "sqlite3").strip().lower()
is_remote_required = os.environ.get("DB_REMOTE_REQUIRED", "false").lower() in ("true", "1", "yes")

POSTGRES_ALIASES = ("postgresql", "postgres", "django.db.backends.postgresql")
SQLITE_ALIASES = ("sqlite3", "sqlite", "django.db.backends.sqlite3")

if raw_db_engine in POSTGRES_ALIASES:
    DB_ENGINE = "postgresql"
elif raw_db_engine in SQLITE_ALIASES:
    DB_ENGINE = "sqlite3"
else:
    raise ImproperlyConfigured(
        f"Mecanismo de banco de dados desconhecido: '{raw_db_engine}'. "
        f"Valores suportados: {POSTGRES_ALIASES + SQLITE_ALIASES}. "
        "Fallback silencioso para SQLite é proibido por governança."
    )

if is_remote_required and DB_ENGINE == "sqlite3":
    raise ImproperlyConfigured(
        "DB_REMOTE_REQUIRED está ativo, mas DB_ENGINE está configurado como SQLite. "
        "A aplicação não pode selecionar SQLite sob nenhuma circunstância em modo remoto."
    )

if DB_ENGINE == "postgresql":
    db_name = os.environ.get("DB_NAME", "sosp_local")
    db_user = os.environ.get("DB_USER", "postgres")
    db_password = os.environ.get("DB_PASSWORD", "")
    db_host = os.environ.get("DB_HOST", "localhost")
    db_port = os.environ.get("DB_PORT", "5432")

    is_remote = db_host not in ("localhost", "127.0.0.1", "") and not db_host.startswith("/")

    # Falha explícita se PostgreSQL remoto for selecionado e a configuração estiver incompleta
    if (is_remote or is_remote_required) and (not db_password or not db_user or not db_name or not db_host):
        raise ImproperlyConfigured(
            "Configuração de PostgreSQL remoto incompleta no SOSP: "
            "DB_NAME, DB_USER, DB_PASSWORD e DB_HOST devem ser definidos explicitamente no ambiente. "
            "Fallback silencioso para SQLite é proibido por governança."
        )

    # Modo SSL: padrão 'require' para conexões remotas seguras (Supabase)
    db_sslmode = os.environ.get("DB_SSLMODE")
    if not db_sslmode:
        db_sslmode = "require" if is_remote else "prefer"

    db_connect_timeout = int(os.environ.get("DB_CONNECT_TIMEOUT", "10"))
    db_statement_timeout = int(os.environ.get("DB_STATEMENT_TIMEOUT", "30000"))

    db_options = {
        "sslmode": db_sslmode,
        "connect_timeout": db_connect_timeout,
        "options": f"-c statement_timeout={db_statement_timeout}",
    }

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": db_name,
            "USER": db_user,
            "PASSWORD": db_password,
            "HOST": db_host,
            "PORT": db_port,
            "CONN_MAX_AGE": int(os.environ.get("DB_CONN_MAX_AGE", "0")),
            "OPTIONS": db_options,
        }
    }

    # Compatibilidade com Pooler de Transação do Supabase:
    # Na porta 6543 (Transaction Pooler) ou com flag ativa, desativa cursores server-side
    disable_cursors_env = os.environ.get("DB_DISABLE_SERVER_SIDE_CURSORS")
    if disable_cursors_env is not None:
        if disable_cursors_env.lower() in ("true", "1", "yes"):
            DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
    elif db_port == "6543":
        DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.environ.get("SQLITE_NAME", ":memory:"),
        }
    }

# Seleção da Estratégia de Repositório de Persistência (ADR-001 / Etapa 3):
# 'memory' (padrão até implantação real do banco) ou 'orm' (PostgreSQL real via Django ORM)
REPOSITORY_BACKEND = os.environ.get("REPOSITORY_BACKEND", "memory").strip().lower()
if REPOSITORY_BACKEND not in ("memory", "orm"):
    raise ImproperlyConfigured(
        f"REPOSITORY_BACKEND inválido: '{REPOSITORY_BACKEND}'. "
        "Valores permitidos: 'memory' (padrão) ou 'orm'."
    )

# Autenticação e Hasher Argon2id (RF-01, RF-02, ADR-003)
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
]

# Sessão expira após 30 minutos de inatividade (RN-28)
SESSION_COOKIE_AGE = 1800
SESSION_SAVE_EVERY_REQUEST = True

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Maceio"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"

# Django REST Framework & RFC 7807 (Problem Details)
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ],
    "EXCEPTION_HANDLER": "common.exceptions.problem_details_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "common.pagination.StandardPagination",
    "PAGE_SIZE": 10,
    "UNAUTHENTICATED_USER": None,
}

# CORS (Comunicação com o portal Next.js 15 na porta 3000)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "idempotency-key",
]

APPEND_SLASH = False

