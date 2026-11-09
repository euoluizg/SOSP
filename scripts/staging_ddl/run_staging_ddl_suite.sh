#!/usr/bin/env bash
# ==============================================================================
# SOSP — Suite de Execução Supervisionada de DDL para Supabase Staging
#
# Protocolo de Segurança (Pilar 0 / AGENTS.md):
# 1. Pré-voo somente leitura (01_preflight_check.py)
# 2. Simulação Dry-Run com ROLLBACK automático (02_apply_staging_ddl.py --dry-run)
# 3. Solicitação de Autorização Humana Explícita para o Apply
# 4. Aplicação transacional com COMMIT (02_apply_staging_ddl.py --apply --confirm-apply)
# 5. Auditoria de integridade pós-voo (03_postflight_verify.py)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${SCRIPT_DIR}/../../backend/.venv/bin/python"
if [ ! -f "$PYTHON_BIN" ]; then
    PYTHON_BIN="python3"
fi

echo "=============================================================================="
echo "SOSP — PIPELINE DE DDL SUPABASE POSTGRESQL 17 (STAGING)"
echo "=============================================================================="

# Passo 1: Pré-Voo
echo ""
echo ">>> [PASSO 1/3] Executando Pré-Voo Somente Leitura..."
"$PYTHON_BIN" "${SCRIPT_DIR}/01_preflight_check.py" "$@"

# Passo 2: Dry-Run
echo ""
echo ">>> [PASSO 2/3] Executando Simulação Transacional Dry-Run (ROLLBACK)..."
"$PYTHON_BIN" "${SCRIPT_DIR}/02_apply_staging_ddl.py" --dry-run "$@"

echo ""
echo "=============================================================================="
echo "✓ PRÉ-VOO E SIMULAÇÃO DRY-RUN CONCLUÍDOS COM SUCESSO."
echo "  O banco de dados NÃO sofreu nenhuma alteração."
echo ""
echo "Para executar a APLICAÇÃO REAL em staging, é OBRIGATÓRIA a aprovação humana."
echo "Comando para execução após aprovação:"
echo "  SOSP_CONFIRM_STAGING_APPLY=true $PYTHON_BIN ${SCRIPT_DIR}/02_apply_staging_ddl.py --apply --confirm-apply"
echo "  $PYTHON_BIN ${SCRIPT_DIR}/03_postflight_verify.py"
echo "=============================================================================="
