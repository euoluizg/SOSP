#!/usr/bin/env bash
# ==============================================================================
# SOSP — ETAPA 4D.2: APLICAÇÃO SUPERVISIONADA DE CONTEXTO HMAC, GRANTS E RLS
# HISTÓRICO OPERACIONAL: A Etapa 4D.2 já foi aplicada e homologada no Supabase.
# O COMMIT 4D.2 e a auditoria pós-commit foram confirmados.
# Preservado exclusivamente para histórico operacional. NÃO reaplicar remotamente.
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

exec "${VENV_PYTHON}" "${SCRIPT_DIR}/run_4d2_apply_security_remote.py" "$@"
