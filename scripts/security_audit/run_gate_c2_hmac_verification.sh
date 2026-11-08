#!/usr/bin/env bash
# ==============================================================================
# SOSP — PORTÃO C.2: VALIDAÇÃO CRIPTOGRÁFICA DO CONTEXTO HMAC (MUTÁVEL)
# Launcher interativo para o Terminal do operador (@euoluizg)
# Valida a posse da chave HMAC contra o Supabase remoto e consome 1 nonce.
# Requer autorização explícita do operador humano.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
VENV_PYTHON="${WORKSPACE_ROOT}/backend/.venv/bin/python"

if [[ ! -f "${VENV_PYTHON}" ]]; then
    echo "❌ Erro: Ambiente virtual Python não encontrado em ${VENV_PYTHON}"
    exit 1
fi

export PYTHONUNBUFFERED=1

# Parâmetros padrão canônicos do Portão C.2
export DB_HOST="${DB_HOST:-aws-1-sa-east-1.pooler.supabase.com}"
export DB_PORT="${DB_PORT:-5432}"
export DB_NAME="${DB_NAME:-postgres}"
export DB_USER="sosp_runtime_app.cidtcgfowvgwgggvhbym"
export DB_SSLMODE="verify-full"

# Detecção automática de CA (prioriza o certificado já validado pelo operador)
if [[ -z "${PGSSLROOTCERT:-}" ]]; then
    if [[ -f "${HOME}/.sosp-certificates/supabase-ca.crt" ]]; then
        export PGSSLROOTCERT="${HOME}/.sosp-certificates/supabase-ca.crt"
    elif [[ -f "${HOME}/.sosp-certs/prod-ca-2021.crt" ]]; then
        export PGSSLROOTCERT="${HOME}/.sosp-certs/prod-ca-2021.crt"
    fi
fi

exec "${VENV_PYTHON}" "${SCRIPT_DIR}/run_gate_c2_hmac_verification.py" "$@"
