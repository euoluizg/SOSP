#!/usr/bin/env bash
# =============================================================================
# SOSP — Sistema de Orientação para Serviços Públicos
# Teste de Autenticação Real (LOGIN) vs. Impersonação (SET ROLE) — 3AF / 2026
#
# Demonstra que as contas sosp_leitor_3af e sosp_operador_3af são contas
# completas de LOGIN (principais de banco), capazes de estabelecer conexões
# TCP/Socket independentes com sessão própria (session_user = current_user).
#
# SEGURANÇA:
#   - As credenciais são geradas randomicamente em tempo de execução via openssl;
#   - Nenhuma senha estática é versionada;
#   - Ao final do teste, as credenciais de teste são redefinidas (revogadas).
# =============================================================================

set -euo pipefail

DB_NAME="${PGDATABASE:-sosp_isolated_test}"
DB_HOST="${PGHOST:-localhost}"
DB_PORT="${PGPORT:-54329}"
ADMIN_USER="${PGUSER:-$(whoami)}"

echo "======================================================================"
echo "SOSP: TESTE DE AUTENTICAÇÃO REAL DE CONTAS LOGIN (PostgreSQL)"
echo "Alvo: host=$DB_HOST, porta=$DB_PORT, banco=$DB_NAME"
echo "======================================================================"

# Salvaguarda: só executa em bancos de teste locais
if [[ "$DB_NAME" != *"test"* && "$DB_NAME" != *"local"* && "$DB_NAME" != *"isolated"* ]]; then
  echo "ERRO DE SEGURANÇA: O banco de dados '$DB_NAME' não parece ser descartável/local!"
  exit 1
fi

TEMP_PASS_LEITOR=$(openssl rand -hex 16)
TEMP_PASS_OPERADOR=$(openssl rand -hex 16)

cleanup() {
  echo ">> Limpando credenciais temporárias de teste..."
  psql -h "$DB_HOST" -p "$DB_PORT" -U "$ADMIN_USER" -d "$DB_NAME" -q \
    -c "ALTER ROLE sosp_leitor_3af WITH PASSWORD NULL; ALTER ROLE sosp_operador_3af WITH PASSWORD NULL;" || true
}
trap cleanup EXIT

echo ">> Configurando senhas temporárias dinâmicas via sessão administrativa..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$ADMIN_USER" -d "$DB_NAME" -q \
  -c "ALTER ROLE sosp_leitor_3af WITH PASSWORD '$TEMP_PASS_LEITOR';" \
  -c "ALTER ROLE sosp_operador_3af WITH PASSWORD '$TEMP_PASS_OPERADOR';"

echo ""
echo ">> 1. Testando autenticação real com a conta 'sosp_leitor_3af'..."
RES_LEITOR=$(PGPASSWORD="$TEMP_PASS_LEITOR" psql -h "$DB_HOST" -p "$DB_PORT" -U "sosp_leitor_3af" -d "$DB_NAME" -t -A \
  -c "SELECT current_user || ':' || session_user;")

if [[ "$RES_LEITOR" != "sosp_leitor_3af:sosp_leitor_3af" ]]; then
  echo "FALHA: Autenticação de sosp_leitor_3af retornou '$RES_LEITOR' (esperado: 'sosp_leitor_3af:sosp_leitor_3af')"
  exit 1
fi
echo "SUCESSO: sosp_leitor_3af autenticado com sessão real ($RES_LEITOR)."

echo ""
echo ">> 2. Testando autenticação real com a conta 'sosp_operador_3af'..."
RES_OPERADOR=$(PGPASSWORD="$TEMP_PASS_OPERADOR" psql -h "$DB_HOST" -p "$DB_PORT" -U "sosp_operador_3af" -d "$DB_NAME" -t -A \
  -c "SELECT current_user || ':' || session_user;")

if [[ "$RES_OPERADOR" != "sosp_operador_3af:sosp_operador_3af" ]]; then
  echo "FALHA: Autenticação de sosp_operador_3af retornou '$RES_OPERADOR' (esperado: 'sosp_operador_3af:sosp_operador_3af')"
  exit 1
fi
echo "SUCESSO: sosp_operador_3af autenticado com sessão real ($RES_OPERADOR)."

echo ""
echo "======================================================================"
echo "TESTE DE AUTENTICAÇÃO REAL CONCLUÍDO COM 100% DE SUCESSO!"
echo "======================================================================"
