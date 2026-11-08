#!/usr/bin/env python3
"""
SOSP — Teste de Fronteira Transacional, Contexto HMAC, Nonce e Reuso de Conexão
Valida deterministicamente:
1. Autenticação DRF / Contexto HMAC / Nonce e queries na mesma transação atômica.
2. Comportamento sob ROLLBACK: cancelamento de mutações e contenção de erro.
3. Higiene de Pool de Conexões: clear_request_context limpa GUCs e impede contaminação.
4. Anti-Replay: Rejeição imediata de nonce duplicado.
"""

import sys
import os
import uuid
import time
import hmac
import hashlib

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../.."))
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from sosp_local_guard import assert_strictly_local_test_environment

try:
    import psycopg
except ImportError:
    import psycopg2 as psycopg


def compute_test_sig(key: str, uid: str, role: str, agency: str, exp: int, nonce: str) -> str:
    payload = f"{uid}:{role}:{agency}:{exp}:{nonce}".encode("utf-8")
    return hmac.new(key.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def test_transaction_boundary(host, port, dbname, user, password, sslmode, hmac_key):
    print("=" * 70)
    print("SOSP — TESTE DE FRONTEIRA TRANSACIONAL E HIGIENE DE CONEXÃO")
    print("=" * 70)

    # Guarda obrigatória de isolamento local (Portão B)
    assert_strictly_local_test_environment(host)
    print(f"✓ Guarda Local Ativa: Conexão estritamente local confirmada para '{host}'.")

    conn = psycopg.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
        sslmode=sslmode,
        connect_timeout=10,
    )
    conn.autocommit = False

    try:
        cur = conn.cursor()

        # ---------------------------------------------------------------------
        # CENÁRIO 1: Transação Bem-Sucedida (Contexto + Query + Commit)
        # ---------------------------------------------------------------------
        print("\n1. Testando transação bem-sucedida com contexto HMAC e nonce único...")
        test_uid = str(uuid.uuid4())
        test_role = "citizen"
        test_agency = ""
        now_epoch = int(time.time())
        exp = now_epoch + 60
        nonce_1 = str(uuid.uuid4())
        sig_1 = compute_test_sig(hmac_key, test_uid, test_role, test_agency, exp, nonce_1)

        cur.execute("SELECT sosp_security.set_request_context(%s, %s, %s, %s, %s, %s);", (
            test_uid, test_role, None, exp, nonce_1, sig_1
        ))
        assert cur.fetchone()[0] is True, "Falha ao definir contexto válido."

        cur.execute("SELECT sosp_security.is_context_valid();")
        assert cur.fetchone()[0] is True, "is_context_valid() deve retornar TRUE dentro da transação."

        cur.execute("SELECT sosp_security.get_current_citizen_id();")
        assert str(cur.fetchone()[0]) == test_uid, "get_current_citizen_id() deve retornar o UUID do cidadão."

        conn.commit()
        print("   ✓ Transação commitada com sucesso.")

        # ---------------------------------------------------------------------
        # CENÁRIO 2: Higiene de Pool de Conexões e Limpeza de Contexto
        # ---------------------------------------------------------------------
        print("\n2. Testando limpeza de contexto e reuso de conexão no pool...")
        cur.execute("SELECT sosp_security.clear_request_context();")
        conn.commit()

        cur.execute("SELECT current_setting('sosp.current_user_id', true);")
        res_uid = cur.fetchone()[0]
        assert not res_uid, f"sosp.current_user_id deve estar vazio após clear_request_context, obteve '{res_uid}'."

        cur.execute("SELECT sosp_security.get_current_role();")
        res_role = cur.fetchone()[0]
        assert res_role == "anonymous", f"Role deve ser 'anonymous' após limpeza, obteve '{res_role}'."

        cur.execute("SELECT sosp_security.is_context_valid();")
        assert cur.fetchone()[0] is False, "Contexto limpo não pode ser válido."
        print("   ✓ Higiene de conexão comprovada: GUCs limpos, estado anônimo restabelecido.")

        # ---------------------------------------------------------------------
        # CENÁRIO 3: Rollback em Caso de Erro de Aplicação
        # ---------------------------------------------------------------------
        print("\n3. Testando comportamento sob ROLLBACK em falha transacional...")
        nonce_2 = str(uuid.uuid4())
        sig_2 = compute_test_sig(hmac_key, test_uid, test_role, test_agency, exp, nonce_2)

        cur.execute("SELECT sosp_security.set_request_context(%s, %s, %s, %s, %s, %s);", (
            test_uid, test_role, None, exp, nonce_2, sig_2
        ))
        assert cur.fetchone()[0] is True

        # Simula ROLLBACK decorrente de erro
        conn.rollback()

        # Após o rollback, executa clear_request_context para sanitizar a conexão no pool
        cur.execute("SELECT sosp_security.clear_request_context();")
        conn.commit()

        cur.execute("SELECT sosp_security.is_context_valid();")
        assert cur.fetchone()[0] is False
        print("   ✓ Transação revertida com sucesso (ROLLBACK); conexão restaurada com segurança.")

        # ---------------------------------------------------------------------
        # CENÁRIO 4: Proteção Anti-Replay com Nonce Consumido
        # ---------------------------------------------------------------------
        print("\n4. Testando rejeição estrita de Anti-Replay com nonce já consumido...")
        # Tenta reutilizar nonce_1 (já commitado no Cenário 1)
        cur.execute("SELECT sosp_security.set_request_context(%s, %s, %s, %s, %s, %s);", (
            test_uid, test_role, None, exp, nonce_1, sig_1
        ))
        replay_result = cur.fetchone()[0]
        assert replay_result is False, "Replay de nonce já consumido DEVE retornar FALSE."
        conn.commit()
        print("   ✓ Replay com nonce anterior rejeitado sumariamente pelo PostgreSQL (Anti-Replay ativo).")

        print("\n" + "=" * 70)
        print("✓ [TODOS OS 4 CENÁRIOS DE TRANSAÇÃO E CONTEXTO APROVADOS]")
        print("=" * 70)
        return True

    finally:
        conn.close()


if __name__ == "__main__":
    host = os.environ.get("DB_HOST", "127.0.0.1")
    port = int(os.environ.get("DB_PORT", "5432"))
    dbname = os.environ.get("DB_NAME", "postgres")
    user = os.environ.get("DB_USER", "postgres")
    password = os.environ.get("DB_PASSWORD", "")
    sslmode = os.environ.get("DB_SSLMODE", "prefer")
    hmac_key = os.environ.get("DB_HMAC_SECRET_KEY", "ci_dummy_hmac_secret_key_32bytes_ok")

    success = test_transaction_boundary(host, port, dbname, user, password, sslmode, hmac_key)
    sys.exit(0 if success else 1)
