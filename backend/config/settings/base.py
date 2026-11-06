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

# Configuração de Banco de Dados Multi-ambiente (ADR-001, ADR-002, Etapa 3)
# Suporta SQLite em memória (padrão para testes offline) e PostgreSQL (local/isolado/Supabase futuro)
DB_ENGINE = os.environ.get("DB_ENGINE", "sqlite3").lower()

if DB_ENGINE in ("postgresql", "postgres"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME", "sosp_local"),
            "USER": os.environ.get("DB_USER", "postgres"),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "5432"),
            "CONN_MAX_AGE": int(os.environ.get("DB_CONN_MAX_AGE", "0")),
            "OPTIONS": {},
        }
    }
    # Modo SSL (ex.: 'require' para conexões remotas seguras)
    db_sslmode = os.environ.get("DB_SSLMODE")
    if db_sslmode:
        DATABASES["default"]["OPTIONS"]["sslmode"] = db_sslmode

    # Compatibilidade com Pooler de Transação (PgBouncer/Supavisor do Supabase na porta 6543):
    # Desativa cursores do lado do servidor se a variável estiver ativa
    if os.environ.get("DB_DISABLE_SERVER_SIDE_CURSORS", "false").lower() in ("true", "1", "yes"):
        DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.environ.get("SQLITE_NAME", ":memory:"),
        }
    }

# Seleção da Estratégia de Repositório de Persistência (ADR-001 / Etapa 3):
# 'memory' (simulado em memória, retrocompatível) ou 'orm' (PostgreSQL real via Django ORM)
REPOSITORY_BACKEND = os.environ.get("REPOSITORY_BACKEND", "memory").lower()

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

