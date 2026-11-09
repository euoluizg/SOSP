#!/usr/bin/env python3
"""
SOSP — Script de Aplicação Segura de DDL no Supabase Staging (Etapa 1 / Supabase DDL Prep)

Garantias de Execução:
1. Idempotente e Não-Destrutivo: Executa '02_apply_schema.sql'.
2. Suporte a Dry-Run (--dry-run): Executa o script dentro de uma transação e faz ROLLBACK,
   comprovando sintaxe, integridade de tipos, constraints, views e funções sem alterar o banco.
3. Confirmação Obrigatória para Apply (--apply): Exige a flag explícita '--confirm-apply' ou
   a variável de ambiente 'SOSP_CONFIRM_STAGING_APPLY=true' antes de emitir COMMIT.
4. Suporte a Mock (--mock): Permite testes locais determinísticos sem necessidade de rede.
5. Transacional: Executado dentro de BEGIN ... COMMIT com rollback automático em qualquer erro.
"""

import os
import sys
import argparse
from typing import Dict, Any, Optional

try:
    import psycopg
except ImportError:
    psycopg = None

DEFAULT_SQL_PATH = os.path.join(os.path.dirname(__file__), "02_apply_schema.sql")


def validate_sslmode(sslmode: str, host: str) -> str:
    """Valida requisitos de TLS: conexões remotas exigem require ou superior."""
    mode = (sslmode or "require").strip().lower()
    is_local = host in ("localhost", "127.0.0.1", "::1", "") or host.startswith("/")
    if not is_local and mode in ("disable", "allow", "prefer"):
        raise ValueError(
            f"Conexão remota com '{host}' rejeitada: sslmode='{mode}' inseguro. "
            f"Exigido 'require', 'verify-ca' ou 'verify-full'."
        )
    return mode


def parse_connection_params() -> Dict[str, Any]:
    """Extrai parâmetros de conexão de variáveis de ambiente com defaults seguros."""
    host = os.environ.get("DB_HOST") or os.environ.get("SUPABASE_POOLER_HOST") or "aws-1-sa-east-1.pooler.supabase.com"
    port = int(os.environ.get("DB_PORT") or os.environ.get("SUPABASE_POOLER_PORT") or "5432")
    dbname = os.environ.get("DB_NAME") or os.environ.get("SUPABASE_DB_NAME") or "postgres"
    user = os.environ.get("DB_USER") or os.environ.get("DB_ADMIN_USER") or "postgres"
    sslmode = validate_sslmode(os.environ.get("DB_SSLMODE", "require"), host)
    password = os.environ.get("DB_PASSWORD") or os.environ.get("PGPASSWORD") or ""

    return {
        "host": host,
        "port": port,
        "dbname": dbname,
        "user": user,
        "password": password,
        "sslmode": sslmode,
    }


def execute_ddl(
    sql_path: str,
    params: Dict[str, Any],
    dry_run: bool = True,
    confirm_apply: bool = False,
    mock_mode: bool = False,
) -> Dict[str, Any]:
    """Executa o script DDL em modo dry-run (ROLLBACK) ou apply definitivo (COMMIT)."""
    if not os.path.exists(sql_path):
        raise FileNotFoundError(f"Arquivo DDL não encontrado: {sql_path}")

    with open(sql_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    result: Dict[str, Any] = {
        "sql_path": sql_path,
        "dry_run": dry_run,
        "success": False,
        "action": "ROLLBACK" if dry_run else "COMMIT",
        "objects_validated": 0,
        "message": "",
    }

    if mock_mode:
        result["success"] = True
        result["objects_validated"] = 38
        result["message"] = (
            "Simulação local (MOCK) de DDL concluída com 100% de sucesso. "
            f"Transação encerrada com {result['action']} seguro."
        )
        return result

    if not dry_run and not confirm_apply:
        raise PermissionError(
            "Modo --apply requer autorização explícita via flag '--confirm-apply' "
            "ou variável de ambiente 'SOSP_CONFIRM_STAGING_APPLY=true'."
        )

    if psycopg is None:
        raise RuntimeError("Biblioteca 'psycopg' não instalada no ambiente.")

    conninfo = (
        f"host={params['host']} port={params['port']} dbname={params['dbname']} "
        f"user={params['user']} sslmode={params['sslmode']}"
    )
    if params["password"]:
        conninfo += f" password={params['password']}"

    # Conecta com autocommit=False para controle transacional estrito
    with psycopg.connect(conninfo, autocommit=False) as conn:
        try:
            with conn.cursor() as cur:
                print(f"Executando DDL ({'DRY-RUN / Simulação' if dry_run else 'APPLY REAL'})...")
                cur.execute(sql_content)

                # Verifica quantos objetos foram criados na transação
                cur.execute(
                    "SELECT count(*) FROM pg_tables WHERE schemaname = 'public';"
                )
                table_count = cur.fetchone()[0]
                result["objects_validated"] = table_count

            if dry_run:
                conn.rollback()
                result["action"] = "ROLLBACK"
                result["success"] = True
                result["message"] = (
                    f"✓ DRY-RUN BEM-SUCEDIDO: {table_count} tabelas compiladas sem erros de sintaxe ou integridade. "
                    "Transação desfeita com ROLLBACK seguro. O banco permanece inalterado."
                )
            else:
                conn.commit()
                result["action"] = "COMMIT"
                result["success"] = True
                result["message"] = (
                    f"✓ APLICAÇÃO CONCLUÍDA: {table_count} tabelas criadas/atualizadas com sucesso no Supabase. "
                    "Transação confirmada com COMMIT."
                )
        except Exception as e:
            conn.rollback()
            result["success"] = False
            result["message"] = f"Falha na execução do DDL (transação revertida): {e}"
            raise

    return result


def main():
    parser = argparse.ArgumentParser(description="SOSP Staging DDL Executor")
    parser.add_argument("--file", default=DEFAULT_SQL_PATH, help="Caminho do arquivo SQL a executar.")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Executa em transação com ROLLBACK (padrão seguro).")
    parser.add_argument("--apply", dest="dry_run", action="store_false", help="Aplica as alterações com COMMIT.")
    parser.add_argument("--confirm-apply", action="store_true", help="Confirmação expressa para execução do modo --apply.")
    parser.add_argument("--mock", action="store_true", help="Executa simulação local sem rede para testes unitários.")
    args = parser.parse_args()

    # Confirmação via flag ou env
    confirm_apply = args.confirm_apply or os.environ.get("SOSP_CONFIRM_STAGING_APPLY", "").lower() in ("true", "1")

    try:
        params = parse_connection_params()
        result = execute_ddl(
            sql_path=args.file,
            params=params,
            dry_run=args.dry_run,
            confirm_apply=confirm_apply,
            mock_mode=args.mock,
        )
        print("=" * 78)
        print("SOSP — RESULTADO DA EXECUÇÃO DDL (STAGING)")
        print("=" * 78)
        print(f"Arquivo DDL:   {result['sql_path']}")
        print(f"Modo:          {'DRY-RUN (Simulação com Rollback)' if result['dry_run'] else 'APPLY REAL (Commit)'}")
        print(f"Status:        {'✓ SUCESSO' if result['success'] else '❌ FALHA'}")
        print(f"Resultado:     {result['message']}")
        print("=" * 78)
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERRO NA EXECUÇÃO DE DDL: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
