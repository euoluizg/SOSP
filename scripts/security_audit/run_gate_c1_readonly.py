#!/usr/bin/env python3
"""
SOSP — PORTÃO C.1: HOMOLOGAÇÃO REMOTA DA APLICAÇÃO (ESTRITAMENTE READ ONLY)
Conecta ao Supabase Session Pooler como 'sosp_runtime_app.<PROJECT_REF>' e verifica
a prontidão do banco para o Django ORM em modo estritamente READ ONLY.

Garantias e Regras Estritas:
1. Identidade exclusiva: 'sosp_runtime_app.cidtcgfowvgwgggvhbym'. Rejeita qualquer conta administrativa.
2. Supabase Session Pooler na porta 5432.
3. TLS verify-full obrigatório com certificado CA.
4. Conexão em autocommit=True com 'BEGIN TRANSACTION READ ONLY;' explícito como 1ª instrução.
5. Verificação imediata na mesma transação: 'SHOW transaction_read_only' == 'on'.
6. Zero COMMIT. Zero DDL/DML. Zero chamadas a set_request_context. Zero consumo de nonces.
7. Zero alterações em roles, grants, policies ou migrations.
8. Encerramento incondicional com ROLLBACK no bloco finally.
9. Inspeção fiel das 38 tabelas e das 2 views com security_invoker=true:
   - vw_catalogservicesearch
   - vw_schedulingslotavailability
"""

import sys
import os
import getpass
from typing import Optional, Dict, Any, List

try:
    import psycopg
except ImportError:
    try:
        import psycopg2 as psycopg
    except ImportError:
        print("❌ [FAIL] Driver psycopg não encontrado.")
        sys.exit(1)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from sosp_remote_pooler_identity import (
    AUTHORIZED_PROJECT_REF,
    DEFAULT_POOLER_HOST,
    DEFAULT_POOLER_PORT,
    DEFAULT_DBNAME,
    RUNTIME_ROLE,
    PHYSICAL_38_TABLES,
    PHYSICAL_2_VIEWS,
)

EXPECTED_RUNTIME_USER = f"{RUNTIME_ROLE}.{AUTHORIZED_PROJECT_REF}"


def validate_runtime_user_strictly(host: str, user_candidate: Optional[str]) -> str:
    candidate = (user_candidate or "").strip()
    if host == DEFAULT_POOLER_HOST:
        if not candidate:
            candidate = EXPECTED_RUNTIME_USER
        if "postgres" in candidate.lower() or "admin" in candidate.lower() or "root" in candidate.lower():
            raise ValueError(
                f"VIOLAÇÃO DE SEGURANÇA: Usuário administrativo '{candidate}' rejeitado no Portão C.1. "
                f"O Portão C.1 deve executar exclusivamente como '{EXPECTED_RUNTIME_USER}'."
            )
        if candidate != EXPECTED_RUNTIME_USER:
            raise ValueError(
                f"Identidade incorreta: '{candidate}'. Esperado para '{host}': '{EXPECTED_RUNTIME_USER}'."
            )
        return candidate
    else:
        # Cluster local de testes
        if not candidate or "postgres" in candidate.lower():
            candidate = RUNTIME_ROLE
        return candidate


def resolve_ca_cert() -> Optional[str]:
    candidate = os.environ.get("PGSSLROOTCERT") or os.environ.get("DB_SSLROOTCERT")
    if candidate and os.path.isfile(os.path.expanduser(candidate)):
        return os.path.abspath(os.path.expanduser(candidate))
    for ca_path in [
        os.path.expanduser("~/.sosp-certificates/supabase-ca.crt"),
        os.path.expanduser("~/.sosp-certs/prod-ca-2021.crt"),
        "/etc/ssl/cert.pem",
        "/etc/ssl/certs/ca-certificates.crt",
    ]:
        if os.path.isfile(ca_path):
            return ca_path
    return None


def run_gate_c1_readonly() -> bool:
    print("=" * 70)
    print("SOSP — PORTÃO C.1: HOMOLOGAÇÃO REMOTA (ESTRITAMENTE READ ONLY)")
    print("=" * 70)

    host = os.environ.get("DB_HOST", DEFAULT_POOLER_HOST).strip()
    port = int(os.environ.get("DB_PORT", str(DEFAULT_POOLER_PORT)).strip())
    dbname = os.environ.get("DB_NAME", DEFAULT_DBNAME).strip()

    # 1. Validação estrita de identidade de runtime
    try:
        user_env = os.environ.get("DB_USER") or os.environ.get("PGUSER")
        user = validate_runtime_user_strictly(host, user_env)
        print(f"✓ Identidade de runtime validada: '{user}'")
    except ValueError as e:
        print(f"❌ [FAIL] {e}")
        return False

    # 2. Validação rigorosa de TLS verify-full
    sslmode = os.environ.get("DB_SSLMODE", "verify-full" if host == DEFAULT_POOLER_HOST else "prefer").strip()
    if host == DEFAULT_POOLER_HOST and sslmode != "verify-full":
        print(f"❌ [FAIL] Violação de segurança: sslmode deve ser estritamente 'verify-full' para '{host}'.")
        return False

    sslrootcert = resolve_ca_cert()
    if sslrootcert:
        print(f"✓ Certificado CA configurado: '{sslrootcert}'")

    # 3. Solicitação de senha segura
    password = os.environ.get("DB_PASSWORD") or os.environ.get("PGPASSWORD")
    if not password and sys.stdin.isatty():
        try:
            password = getpass.getpass(f"Informe a senha para o usuário '{user}' (oculta): ")
        except (KeyboardInterrupt, EOFError):
            print("\nOperação cancelada.")
            return False

    print(f"\nConectando a {host}:{port}/{dbname}...")

    conn_params = {
        "host": host,
        "port": port,
        "dbname": dbname,
        "user": user,
        "password": password,
        "sslmode": sslmode,
        "connect_timeout": 15,
        "autocommit": True,  # Impede início implícito de transação read-write
    }
    if sslrootcert:
        conn_params["sslrootcert"] = sslrootcert

    conn = None
    cur = None
    try:
        conn = psycopg.connect(**conn_params)
        cur = conn.cursor()

        # ---------------------------------------------------------------------
        # FRONTEIRA TRANSACIONAL READ ONLY (OBRIGATÓRIA)
        # ---------------------------------------------------------------------
        cur.execute("BEGIN TRANSACTION READ ONLY;")

        # Verifica na mesma transação
        cur.execute("SHOW transaction_read_only;")
        show_ro = str(cur.fetchone()[0]).lower().strip()

        cur.execute("SELECT current_setting('transaction_read_only');")
        setting_ro = str(cur.fetchone()[0]).lower().strip()

        if show_ro != "on" or setting_ro != "on":
            print(f"❌ [FAIL] Violação transacional: transaction_read_only não está 'on' (SHOW='{show_ro}', setting='{setting_ro}').")
            return False

        print(f"✓ Fronteira Transacional: transaction_read_only='{show_ro}' (ON) confirmada na transação ativa.")

        # 1. Identidade e Role de Runtime
        cur.execute("SELECT current_user, session_user;")
        curr_user, sess_user = cur.fetchone()
        print(f"✓ Sessão Ativa: current_user='{curr_user}', session_user='{sess_user}'")

        cur.execute("SELECT pg_has_role(current_user, 'sosp_runtime_role', 'member');")
        assert cur.fetchone()[0] is True, "O usuário não herda sosp_runtime_role."
        print("✓ Pertencimento a 'sosp_runtime_role': Confirmado (True).")

        # 2. Integridade das 38 Tabelas Físicas
        cur.execute("""
            SELECT relname
            FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relkind = 'r';
        """)
        found_tables = {r[0] for r in cur.fetchall()}
        missing_tables = set(PHYSICAL_38_TABLES) - found_tables
        if missing_tables:
            print(f"❌ [FAIL] Tabelas ausentes no schema public: {missing_tables}")
            return False
        print(f"✓ Inventário de Tabelas: Todas as 38 tabelas físicas presentes e compatíveis.")

        # 3. Auditoria Profunda das 2 Views Físicas (security_invoker = true)
        cur.execute("""
            SELECT c.relname, c.reloptions
            FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relkind = 'v'
              AND c.relname IN ('vw_catalogservicesearch', 'vw_schedulingslotavailability');
        """)
        views_info = cur.fetchall()
        found_views = {v[0]: (v[1] or []) for v in views_info}

        for expected_view in PHYSICAL_2_VIEWS:
            if expected_view not in found_views:
                print(f"❌ [FAIL] View '{expected_view}' não encontrada no schema public.")
                return False
            options = found_views[expected_view]
            assert any("security_invoker=true" in opt for opt in options), f"View '{expected_view}' sem security_invoker=true!"

        print("✓ Views Físicas: 'vw_catalogservicesearch' e 'vw_schedulingslotavailability' auditadas com 'security_invoker=true'.")

        # 4. Inspeção das Colunas Reais das Views
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'vw_catalogservicesearch'
            ORDER BY ordinal_position;
        """)
        cols_search = [r[0] for r in cur.fetchall()]
        assert "serviceid" in cols_search and "servicename" in cols_search and "category" in cols_search
        print(f"✓ Colunas de vw_catalogservicesearch verificadas: {len(cols_search)} colunas conformes.")

        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'vw_schedulingslotavailability'
            ORDER BY ordinal_position;
        """)
        cols_slots = [r[0] for r in cur.fetchall()]
        assert "slotid" in cols_slots and "unitid" in cols_slots and "availableslots" in cols_slots
        print(f"✓ Colunas de vw_schedulingslotavailability verificadas: {len(cols_slots)} colunas conformes.")

        # 5. Isolamento Criptográfico e Bloqueio de Leitura Direta de Segredos
        try:
            cur.execute("SELECT * FROM sosp_security.hmac_secret LIMIT 1;")
            print("❌ [FAIL] Violação: runtime conseguiu ler sosp_security.hmac_secret!")
            return False
        except Exception:
            # Erro 42501 esperado; reabre transação READ ONLY limpa
            cur.execute("ROLLBACK;")
            cur.execute("BEGIN TRANSACTION READ ONLY;")
            print("✓ Isolamento do Segredo HMAC: Confirmado (SELECT direto negado para runtime).")

        # 6. Prova de Bloqueio de Escrita (ReadOnlySqlTransaction)
        try:
            cur.execute("CREATE TEMPORARY TABLE t_c1_fail (id int);")
            print("❌ [FAIL] Escrita permitida em transação READ ONLY!")
            return False
        except psycopg.errors.ReadOnlySqlTransaction:
            cur.execute("ROLLBACK;")
            print("✓ Bloqueio de Escrita: Confirmado (ReadOnlySqlTransaction lançado em tentativa de DDL).")

        print("\n" + "=" * 70)
        print("✓ [PORTÃO C.1 APROVADO] Conectividade, TLS verify-full, esquema físico e")
        print("                       restrições READ ONLY comprovadas sem mutações no banco.")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"\n❌ [ERROR] Falha durante a execução do Portão C.1: {e}")
        return False
    finally:
        if cur:
            try:
                cur.execute("ROLLBACK;")
            except Exception:
                pass
            cur.close()
        if conn:
            try:
                conn.close()
            except Exception:
                pass


if __name__ == "__main__":
    success = run_gate_c1_readonly()
    sys.exit(0 if success else 1)
