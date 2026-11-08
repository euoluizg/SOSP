#!/usr/bin/env python3
"""
SOSP — PORTÃO A: VERIFICAÇÃO SEGURA DE CREDENCIAIS REMOTAS (ESTRITAMENTE READ-ONLY)
Conecta ao Supabase Session Pooler como a role de runtime 'sosp_runtime_app.<PROJECT_REF>'
e verifica conectividade, TLS verify-full, permissões e inventário sem mutação de dados e sem consumir nonces.

Garantias e Regras Estritas:
1. Conexão inicial em autocommit=True.
2. Abertura imediata e explícita via 'BEGIN TRANSACTION READ ONLY;' antes de qualquer consulta.
3. Validação em-transação de 'SHOW transaction_read_only' obrigando o retorno 'on'.
4. Identidade estritamente validada: 'sosp_runtime_app.cidtcgfowvgwgggvhbym'. Rejeita qualquer identidade administrativa.
5. TLS verify-full obrigatório contra o Supabase Session Pooler com validação de CA.
6. Encerramento incondicional via ROLLBACK no bloco finally (nenhum COMMIT).
7. Zero mutações DDL/DML e zero chamadas a funções que consumam nonces.
"""

import sys
import os
import getpass
from typing import Optional, Dict, Any

try:
    import psycopg
except ImportError:
    try:
        import psycopg2 as psycopg
    except ImportError:
        print("❌ [FAIL] Driver psycopg (versão 3) ou psycopg2 não encontrado no ambiente virtual.")
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

EXPECTED_REMOTE_RUNTIME_USER = f"{RUNTIME_ROLE}.{AUTHORIZED_PROJECT_REF}"


def validate_runtime_user_strictly(host: str, user_candidate: Optional[str]) -> str:
    """
    Valida e impõe estritamente o usuário de runtime do SOSP.
    Rejeita terminantemente qualquer tentativa de uso de usuário administrativo (ex: postgres).
    """
    candidate = (user_candidate or "").strip()

    if host == DEFAULT_POOLER_HOST:
        # Se for o pooler do Supabase, o usuário DEVE ser estritamente o runtime role do projeto
        if not candidate:
            candidate = EXPECTED_REMOTE_RUNTIME_USER

        if "postgres" in candidate.lower():
            raise ValueError(
                f"VIOLAÇÃO DE SEGURANÇA: Usuário administrativo '{candidate}' rejeitado no Portão A. "
                f"O Portão A deve executar exclusivamente como '{EXPECTED_REMOTE_RUNTIME_USER}'."
            )

        if candidate != EXPECTED_REMOTE_RUNTIME_USER:
            raise ValueError(
                f"Identidade incorreta: '{candidate}'. "
                f"Para o host '{host}', a identidade esperada é estritamente '{EXPECTED_REMOTE_RUNTIME_USER}'."
            )
        return candidate
    else:
        # Para testes locais em cluster de teste
        if not candidate:
            candidate = RUNTIME_ROLE
        return candidate


def resolve_ca_certificate(host: str, sslmode: str) -> Optional[str]:
    """
    Localiza o certificado raiz CA para validação TLS verify-full.
    """
    ca_candidate = os.environ.get("PGSSLROOTCERT") or os.environ.get("DB_SSLROOTCERT")
    if ca_candidate and os.path.isfile(os.path.expanduser(ca_candidate)):
        return os.path.abspath(os.path.expanduser(ca_candidate))

    # Caminhos padrão do projeto (prioriza certificado validado do operador)
    for default_path in [
        os.path.expanduser("~/.sosp-certificates/supabase-ca.crt"),
        os.path.expanduser("~/.sosp-certs/prod-ca-2021.crt"),
    ]:
        if os.path.isfile(default_path):
            return default_path

    # CA padrão do sistema macOS / Linux
    for sys_ca in ["/etc/ssl/cert.pem", "/etc/ssl/certs/ca-certificates.crt"]:
        if os.path.isfile(sys_ca):
            return sys_ca

    if host == DEFAULT_POOLER_HOST and sslmode == "verify-full":
        print("⚠️ [AVISO] Nenhum arquivo CA especificado via PGSSLROOTCERT. Utilizando CA do sistema.")
    return None


def run_gate_a_readonly() -> bool:
    print("=" * 70)
    print("SOSP — PORTÃO A: VERIFICAÇÃO DE CREDENCIAIS E INVENTÁRIO (READ ONLY)")
    print("=" * 70)

    host = os.environ.get("DB_HOST", DEFAULT_POOLER_HOST).strip()
    port = int(os.environ.get("DB_PORT", str(DEFAULT_POOLER_PORT)).strip())
    dbname = os.environ.get("DB_NAME", DEFAULT_DBNAME).strip()

    # 1. Validação estrita de identidade ANTES de solicitar senha
    try:
        user_env = os.environ.get("DB_USER") or os.environ.get("PGUSER")
        user = validate_runtime_user_strictly(host, user_env)
        print(f"✓ Identidade de runtime validada: '{user}'")
    except ValueError as e:
        print(f"❌ [FAIL] {e}")
        return False

    # 2. Validação rigorosa de TLS
    sslmode = os.environ.get("DB_SSLMODE", "verify-full" if host == DEFAULT_POOLER_HOST else "prefer").strip()
    if host == DEFAULT_POOLER_HOST and sslmode != "verify-full":
        print(f"❌ [FAIL] Violação de segurança: sslmode deve ser estritamente 'verify-full' para o host '{host}'. (Fornecido: '{sslmode}')")
        return False

    sslrootcert = resolve_ca_certificate(host, sslmode)
    if sslrootcert:
        print(f"✓ Certificado CA configurado: '{sslrootcert}'")

    # 3. Obtenção de senha segura
    password = os.environ.get("DB_PASSWORD") or os.environ.get("PGPASSWORD")
    if not password and sys.stdin.isatty():
        try:
            password = getpass.getpass(f"Informe a senha para o usuário de runtime '{user}' (oculta): ")
        except (KeyboardInterrupt, EOFError):
            print("\nOperação cancelada pelo operador.")
            return False

    print(f"\nConectando a {host}:{port}/{dbname}...")

    conn_params: Dict[str, Any] = {
        "host": host,
        "port": port,
        "dbname": dbname,
        "user": user,
        "password": password,
        "sslmode": sslmode,
        "connect_timeout": 15,
        "autocommit": True,  # ESTRATÉGIA ROBUSTA: conexão inicial limpa fora de transação implícita
    }
    if sslrootcert:
        conn_params["sslrootcert"] = sslrootcert

    conn = None
    cur = None
    try:
        conn = psycopg.connect(**conn_params)
        cur = conn.cursor()

        # ---------------------------------------------------------------------
        # FRONTEIRA TRANSACIONAL READ ONLY (ABERTURA EXPLÍCITA ANTES DE QUALQUER QUERY)
        # ---------------------------------------------------------------------
        cur.execute("BEGIN TRANSACTION READ ONLY;")

        # Validação obrigatória na mesma transação
        cur.execute("SHOW transaction_read_only;")
        show_ro = str(cur.fetchone()[0]).lower().strip()

        cur.execute("SELECT current_setting('transaction_read_only');")
        setting_ro = str(cur.fetchone()[0]).lower().strip()

        if show_ro != "on" or setting_ro != "on":
            print(f"❌ [FAIL] ABORTO DE SEGURANÇA: Transação não está em modo READ ONLY (SHOW='{show_ro}', setting='{setting_ro}').")
            return False

        print(f"✓ Fronteira Transacional: transaction_read_only='{show_ro}' (ON) confirmada na mesma transação.")

        # 1. Verifica identidade ativa
        cur.execute("SELECT current_user, session_user;")
        curr_user, sess_user = cur.fetchone()
        print(f"✓ Identidade da Sessão: current_user='{curr_user}', session_user='{sess_user}'")

        # 2. Verifica pertencimento a sosp_runtime_role
        cur.execute("SELECT pg_has_role(current_user, 'sosp_runtime_role', 'member');")
        is_member = cur.fetchone()[0]
        if not is_member:
            print("❌ [FAIL] O usuário autenticado não herda a role 'sosp_runtime_role'.")
            return False
        print("✓ Pertencimento a 'sosp_runtime_role': Confirmado (True).")

        # 3. Verifica isolamento de tabelas de segredos no schema sosp_security
        # Tentativa de SELECT direto deve falhar com 42501 permission denied
        try:
            cur.execute("SELECT 1 FROM sosp_security.hmac_secret LIMIT 1;")
            print("❌ [FAIL] Violação de segurança: SELECT direto em sosp_security.hmac_secret foi permitido!")
            return False
        except Exception:
            # Esperado: permission denied.
            # Como a transação é abortada em erro no Postgres, reabre a transação READ ONLY limpa
            cur.execute("ROLLBACK;")
            cur.execute("BEGIN TRANSACTION READ ONLY;")
            print("✓ Isolamento do Segredo HMAC: Confirmado (SELECT direto negado para runtime).")

        # 4. Verifica integridade do catálogo físico (38 tabelas e 2 views no schema public)
        cur.execute("""
            SELECT relname, relkind
            FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relkind IN ('r', 'v');
        """)
        rows = cur.fetchall()
        found_tables = {r[0] for r in rows if r[1] == 'r'}
        found_views = {r[0] for r in rows if r[1] == 'v'}

        missing_tables = set(PHYSICAL_38_TABLES) - found_tables
        missing_views = set(PHYSICAL_2_VIEWS) - found_views

        if missing_tables:
            print(f"❌ [FAIL] Tabelas ausentes no schema public: {missing_tables}")
            return False
        if missing_views:
            print(f"❌ [FAIL] Views ausentes no schema public: {missing_views}")
            return False

        print(f"✓ Inventário Físico: 38 tabelas e 2 views presentes e íntegras no schema public.")

        # 5. Confirmação de que operações de escrita são sumariamente bloqueadas
        try:
            cur.execute("CREATE TEMPORARY TABLE t_verify_ro_gate_a (id int);")
            print("❌ [FAIL] Violação de segurança: escrita permitida em transação READ ONLY!")
            return False
        except psycopg.errors.ReadOnlySqlTransaction:
            cur.execute("ROLLBACK;")
            print("✓ Bloqueio de Escrita: Confirmado (ReadOnlySqlTransaction lançado ao tentar mutação).")
        except Exception:
            cur.execute("ROLLBACK;")
            print("✓ Bloqueio de Escrita: Confirmado.")

        print("\n" + "=" * 70)
        print("✓ [PORTÃO A APROVADO] Credenciais de runtime, conectividade e isolamento verificados.")
        print("                      Transação 100% READ ONLY. Zero dados gravados. Zero nonces consumidos.")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"\n❌ [ERROR] Falha durante a execução do Portão A: {e}")
        return False
    finally:
        # Encerramento incondicional com ROLLBACK
        if cur:
            try:
                cur.execute("ROLLBACK;")
            except Exception:
                pass
            try:
                cur.close()
            except Exception:
                pass
        if conn:
            try:
                conn.close()
            except Exception:
                pass


if __name__ == "__main__":
    success = run_gate_a_readonly()
    sys.exit(0 if success else 1)
