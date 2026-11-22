#!/usr/bin/env bash
# ==============================================================================
# SOSP — ETAPA 4D.2: ROLLBACK REMOTO SUPERVISIONADO (PORTÃO E)
# Launcher interativo para o Terminal do proprietário (@euoluizg)
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

exec "${VENV_PYTHON}" "${SCRIPT_DIR}/run_4d2_rollback_remote.py" "$@"
