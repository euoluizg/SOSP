#!/usr/bin/env python3
"""
SOSP — Gerador Local Seguro de SQL (Argon2id) para Admin e Servidor no Supabase.

Regras de governança:
- Nenhuma senha é armazenada ou gravada em arquivo versionado do repositório.
- Gera hashes Argon2id reais usando exatamente o Django `Argon2PasswordHasher` do backend.
- Emite SQL idempotente e não-destrutivo (zero DELETE/TRUNCATE/DROP) pronto para colar
  no Supabase SQL Editor e criar/atualizar:
    1) Admin SOSP Geral (CPF 99988877714 / Matrícula ADM-0001 / superadmin)
    2) João Servidor Central (CPF 33366699957 / Matrícula SSP-1001 / server / SSP + Central Já! Centro)

Uso:
  cd backend && .venv/bin/python ../scripts/staging_ddl/06_generate_internal_users_sql.py
  # Ou para gerar 2 senhas aleatórias fortes na hora (exibidas apenas no seu terminal):
  cd backend && .venv/bin/python ../scripts/staging_ddl/06_generate_internal_users_sql.py --auto
"""

import argparse
import getpass
import os
import re
import secrets
import string
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")
import django  # noqa: E402

django.setup()

from django.contrib.auth.hashers import make_password  # noqa: E402


def _validate_strength(password: str) -> bool:
    return (
        len(password) >= 8
        and bool(re.search(r"[A-Z]", password))
        and bool(re.search(r"[a-z]", password))
        and bool(re.search(r"\d", password))
        and bool(re.search(r"[^A-Za-z0-9]", password))
    )


def _build_random_secret() -> str:
    upper = secrets.choice(string.ascii_uppercase)
    lower = secrets.choice(string.ascii_lowercase)
    digit = secrets.choice(string.digits)
    symbol = secrets.choice("!@#$%&*")
    pool = string.ascii_letters + string.digits
    tail = "".join(secrets.choice(pool) for _ in range(12))
    chars = list(upper + lower + digit + symbol + tail)
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


def _sql_escape(value: str) -> str:
    return value.replace("'", "''")


def build_sql(admin_hash: str, server_hash: str) -> str:
    safe_admin_hash = _sql_escape(admin_hash)
    safe_server_hash = _sql_escape(server_hash)
    return f"""-- ==============================================================================
-- SOSP — Provisionamento / Atualização Idempotente de Admin e Servidor (Argon2id)
-- Execute no Supabase SQL Editor (após 05_seed_alagoas_catalog_and_demo_data.sql)
-- ==============================================================================

BEGIN;

DO $$
DECLARE
    v_ssp_id      uuid;
    v_unit_centro uuid;
    v_admin_id    uuid;
    v_server_id   uuid;
BEGIN
    SELECT id INTO v_ssp_id
      FROM public.catalogAgency
     WHERE acronym = 'SSP' AND deletedAt IS NULL
     LIMIT 1;

    SELECT id INTO v_unit_centro
      FROM public.catalogUnit
     WHERE name = 'Central Já! Centro' AND deletedAt IS NULL
     LIMIT 1;

    -- 1) Admin SOSP Geral (superadmin) — CPF: 99988877714 | Matrícula: ADM-0001
    SELECT id INTO v_admin_id
      FROM public.accountsInternalUser
     WHERE cpf = '99988877714' AND deletedAt IS NULL
     LIMIT 1;

    IF v_admin_id IS NULL THEN
        INSERT INTO public.accountsInternalUser (
            cpf, fullName, email, registrationNumber,
            agencyId, unitId, role, canManageCatalog,
            passwordHash, mustChangePassword, isActive
        ) VALUES (
            '99988877714', 'Admin SOSP Geral', 'admin@sosp.al.gov.br', 'ADM-0001',
            NULL, NULL, 'superadmin', true,
            '{safe_admin_hash}', false, true
        ) RETURNING id INTO v_admin_id;
    ELSE
        UPDATE public.accountsInternalUser
           SET fullName           = 'Admin SOSP Geral',
               email              = 'admin@sosp.al.gov.br',
               registrationNumber = 'ADM-0001',
               role               = 'superadmin',
               canManageCatalog   = true,
               passwordHash       = '{safe_admin_hash}',
               mustChangePassword = false,
               isActive           = true,
               deletedAt          = NULL,
               updatedAt          = now()
         WHERE id = v_admin_id;
    END IF;

    -- 2) João Servidor Central (server) — CPF: 33366699957 | Matrícula: SSP-1001
    SELECT id INTO v_server_id
      FROM public.accountsInternalUser
     WHERE cpf = '33366699957' AND deletedAt IS NULL
     LIMIT 1;

    IF v_server_id IS NULL THEN
        INSERT INTO public.accountsInternalUser (
            cpf, fullName, email, registrationNumber,
            agencyId, unitId, role, canManageCatalog,
            passwordHash, mustChangePassword, isActive
        ) VALUES (
            '33366699957', 'João Servidor Central', 'joao.servidor@ssp.al.gov.br', 'SSP-1001',
            v_ssp_id, v_unit_centro, 'server', false,
            '{safe_server_hash}', false, true
        ) RETURNING id INTO v_server_id;
    ELSE
        UPDATE public.accountsInternalUser
           SET fullName           = 'João Servidor Central',
               email              = 'joao.servidor@ssp.al.gov.br',
               registrationNumber = 'SSP-1001',
               agencyId           = COALESCE(v_ssp_id, agencyId),
               unitId             = COALESCE(v_unit_centro, unitId),
               role               = 'server',
               canManageCatalog   = false,
               passwordHash       = '{safe_server_hash}',
               mustChangePassword = false,
               isActive           = true,
               deletedAt          = NULL,
               updatedAt          = now()
         WHERE id = v_server_id;
    END IF;

    -- 3) Limpa eventuais bloqueios de tentativas anteriores (RN-29, sem DELETE físico)
    UPDATE public.accountsLoginAttempt
       SET wasSuccessful = true
     WHERE cpf IN ('99988877714', '33366699957')
       AND wasSuccessful = false;

    -- 4) Revoga sessões antigas para exigir novo token limpo
    UPDATE public.accountsSession
       SET revokedAt = now()
     WHERE subjectType = 'internal'
       AND subjectId IN (v_admin_id, v_server_id)
       AND revokedAt IS NULL;
END;
$$;

COMMIT;

-- Conferência (Somente Leitura — sem expor hash)
SELECT cpf, fullName, registrationNumber, email, role, canManageCatalog, mustChangePassword, isActive, agencyId, unitId
  FROM public.accountsInternalUser
 WHERE cpf IN ('99988877714', '33366699957')
   AND deletedAt IS NULL
 ORDER BY role DESC;
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera SQL seguro (Argon2id) para criar/atualizar Admin e Servidor no Supabase."
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Gera automaticamente duas senhas fortes aleatórias distintas (exibidas apenas localmente).",
    )
    args = parser.parse_args()

    if args.auto:
        admin_secret = _build_random_secret()
        server_secret = _build_random_secret()
        print("=================================================================")
        print("CREDENCIAIS GERADAS LOCALMENTE (ANOTE E NÃO COMMITE EM GIT)")
        print("=================================================================")
        print("Admin    -> CPF: 99988877714 | Matrícula: ADM-0001 | Senha:", admin_secret)
        print("Servidor -> CPF: 33366699957 | Matrícula: SSP-1001 | Senha:", server_secret)
        print("Portal   -> https://portal.sosp.workers.dev/login/institucional")
        print("=================================================================\n")
    else:
        print("Informe senhas fortes distintas (mín. 8 chars, maiúscula, minúscula, número e símbolo):")
        admin_secret = getpass.getpass("Senha para Admin (99988877714 / ADM-0001): ").strip()
        server_secret = getpass.getpass("Senha para Servidor (33366699957 / SSP-1001): ").strip()

    if not _validate_strength(admin_secret):
        print("ERRO: A senha do Admin não atende aos requisitos mínimos de segurança.", file=sys.stderr)
        return 1
    if not _validate_strength(server_secret):
        print("ERRO: A senha do Servidor não atende aos requisitos mínimos de segurança.", file=sys.stderr)
        return 1
    if admin_secret == server_secret:
        print("ERRO: As senhas de Admin e Servidor devem ser distintas.", file=sys.stderr)
        return 1

    admin_hash = make_password(admin_secret)
    server_hash = make_password(server_secret)
    print(build_sql(admin_hash, server_hash))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
