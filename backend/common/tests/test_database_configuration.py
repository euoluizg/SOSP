"""
SOSP — Testes Automatizados de Configuração de Banco de Dados Multi-Ambiente.

Valida as regras de governança para DB_ENGINE, DB_REMOTE_REQUIRED, validação de credenciais
remotas, modos de pooling, aliases de driver e seleção de REPOSITORY_BACKEND.
"""

import os
import subprocess
import sys
import pytest
from django.core.exceptions import ImproperlyConfigured


def run_django_settings_eval(env_overrides: dict) -> subprocess.CompletedProcess:
    """Executa um subprocesso avaliando as configurações do Django com variáveis de ambiente modificadas."""
    env = os.environ.copy()
    env.update(env_overrides)
    cmd = [
        sys.executable,
        "-c",
        (
            "import os, django; "
            "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base'); "
            "django.setup(); "
            "from django.conf import settings; "
            "print('OK', settings.DATABASES['default']['ENGINE'], settings.REPOSITORY_BACKEND)"
        ),
    ]
    return subprocess.run(
        cmd,
        env=env,
        cwd=os.path.join(os.path.dirname(__file__), "../../../backend"),
        capture_output=True,
        text=True,
    )


def test_unknown_db_engine_raises_improperly_configured():
    """Valores desconhecidos de DB_ENGINE devem gerar ImproperlyConfigured, nunca fallback silencioso."""
    res = run_django_settings_eval({"DB_ENGINE": "mysql_custom"})
    assert res.returncode != 0
    assert "ImproperlyConfigured" in res.stderr
    assert "Mecanismo de banco de dados desconhecido: 'mysql_custom'" in res.stderr


def test_remote_required_with_sqlite_forbidden():
    """Se DB_REMOTE_REQUIRED=true, a aplicação não pode selecionar SQLite sob nenhuma circunstância."""
    res = run_django_settings_eval({
        "DB_REMOTE_REQUIRED": "true",
        "DB_ENGINE": "sqlite3",
    })
    assert res.returncode != 0
    assert "ImproperlyConfigured" in res.stderr
    assert "DB_REMOTE_REQUIRED está ativo, mas DB_ENGINE está configurado como SQLite" in res.stderr


def test_remote_required_with_missing_credentials_fails():
    """Se DB_REMOTE_REQUIRED=true e DB_ENGINE=postgresql, mas faltam credenciais, deve falhar explicitamente."""
    res = run_django_settings_eval({
        "DB_REMOTE_REQUIRED": "true",
        "DB_ENGINE": "postgresql",
        "DB_HOST": "aws-1-sa-east-1.pooler.supabase.com",
        "DB_PORT": "5432",
        "DB_USER": "",
        "DB_PASSWORD": "",
        "DB_NAME": "postgres",
    })
    assert res.returncode != 0
    assert "ImproperlyConfigured" in res.stderr
    assert "Configuração de PostgreSQL remoto incompleta no SOSP" in res.stderr


def test_remote_host_without_credentials_fails():
    """Mesmo sem DB_REMOTE_REQUIRED=true, especificar host remoto sem senha/user deve falhar."""
    res = run_django_settings_eval({
        "DB_ENGINE": "postgresql",
        "DB_HOST": "aws-1-sa-east-1.pooler.supabase.com",
        "DB_PORT": "5432",
        "DB_USER": "postgres.test",
        "DB_PASSWORD": "",  # Senha vazia para host remoto
        "DB_NAME": "postgres",
    })
    assert res.returncode != 0
    assert "ImproperlyConfigured" in res.stderr
    assert "Configuração de PostgreSQL remoto incompleta" in res.stderr


def test_db_engine_postgresql_aliases():
    """Testa que aliases 'postgresql', 'postgres' e 'django.db.backends.postgresql' são suportados."""
    for alias in ("postgresql", "postgres", "django.db.backends.postgresql"):
        res = run_django_settings_eval({
            "DB_ENGINE": alias,
            "DB_HOST": "localhost",
            "DB_USER": "postgres",
            "DB_NAME": "sosp_test",
            "DB_REMOTE_REQUIRED": "false",
        })
        assert res.returncode == 0, f"Falha com alias: {alias}, stderr: {res.stderr}"
        assert "django.db.backends.postgresql" in res.stdout


def test_db_engine_sqlite_aliases():
    """Testa que aliases 'sqlite3', 'sqlite' e 'django.db.backends.sqlite3' são suportados."""
    for alias in ("sqlite3", "sqlite", "django.db.backends.sqlite3"):
        res = run_django_settings_eval({
            "DB_ENGINE": alias,
            "DB_REMOTE_REQUIRED": "false",
        })
        assert res.returncode == 0, f"Falha com alias: {alias}, stderr: {res.stderr}"
        assert "django.db.backends.sqlite3" in res.stdout


def test_invalid_repository_backend_raises_improperly_configured():
    """REPOSITORY_BACKEND inválido deve gerar ImproperlyConfigured."""
    res = run_django_settings_eval({
        "REPOSITORY_BACKEND": "couchdb_unsupported",
    })
    assert res.returncode != 0
    assert "ImproperlyConfigured" in res.stderr
    assert "REPOSITORY_BACKEND inválido: 'couchdb_unsupported'" in res.stderr


def test_transaction_pooler_port_6543_disables_server_side_cursors():
    """Porta 6543 (Transaction Pooler) deve configurar DISABLE_SERVER_SIDE_CURSORS = True."""
    env = os.environ.copy()
    env.update({
        "DB_ENGINE": "postgresql",
        "DB_HOST": "localhost",
        "DB_PORT": "6543",
        "DB_USER": "postgres",
        "DB_NAME": "postgres",
        "DB_REMOTE_REQUIRED": "false",
    })
    cmd = [
        sys.executable,
        "-c",
        (
            "import os, django; "
            "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base'); "
            "django.setup(); "
            "from django.conf import settings; "
            "print('CURSORS:', settings.DATABASES['default'].get('DISABLE_SERVER_SIDE_CURSORS'))"
        ),
    ]
    res = subprocess.run(
        cmd,
        env=env,
        cwd=os.path.join(os.path.dirname(__file__), "../../../backend"),
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "CURSORS: True" in res.stdout
