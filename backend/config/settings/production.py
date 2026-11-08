import os
from .base import *

DEBUG = False

# Hosts permitidos em produção
raw_allowed_hosts = os.environ.get("ALLOWED_HOSTS", "")
if raw_allowed_hosts:
    ALLOWED_HOSTS = [h.strip() for h in raw_allowed_hosts.split(",") if h.strip()]
else:
    ALLOWED_HOSTS = ["sosp.al.gov.br", "api.sosp.al.gov.br", "localhost", "127.0.0.1"]

render_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if render_hostname and render_hostname not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_hostname)

# Arquivos estáticos em produção (necessário para collectstatic no deploy)
STATIC_ROOT = BASE_DIR / "staticfiles"

# Segurança de Transporte e Cookies (ADR-003, RS-01 a RS-05)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "true").lower() in ("true", "1")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 ano
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# CORS e CSRF Restritos a Produção / Staging
raw_cors = os.environ.get("CORS_ALLOWED_ORIGINS", "")
if raw_cors:
    CORS_ALLOWED_ORIGINS = [c.strip() for c in raw_cors.split(",") if c.strip()]
else:
    CORS_ALLOWED_ORIGINS = [
        "https://sosp.al.gov.br",
        "https://portal.sosp.al.gov.br",
        "https://sosp-portal.workers.dev",
        "https://sosp-portal-staging.workers.dev",
    ]

raw_csrf = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
if raw_csrf:
    CSRF_TRUSTED_ORIGINS = [c.strip() for c in raw_csrf.split(",") if c.strip()]
else:
    CSRF_TRUSTED_ORIGINS = [
        "https://sosp.al.gov.br",
        "https://portal.sosp.al.gov.br",
        "https://sosp-portal.workers.dev",
        "https://sosp-portal-staging.workers.dev",
    ]

# Logging Estruturado para Produção
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": "%(asctime)s [%(levelname)s] %(name)s (%(process)d): %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.environ.get("LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "common.security": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
