#!/usr/bin/env python3
"""
SOSP — Script de Pré-Voo: Conectividade de Banco de Dados (Etapa 4A / Hardened)

Objetivo:
Valida a conectividade TCP/Socket, resolução DNS, handshake SSL e autenticação básica
com o PostgreSQL (local ou Supabase remoto) de forma estritamente segura e não destrutiva.

Regras de Segurança:
- Não executa comandos DDL ou DML (somente 'SELECT version()').
- Não imprime senhas, tokens ou connection strings sensíveis no terminal/logs.
- Sanitiza mensagens de erro de conexão.
- Lê senha preferencialmente de variáveis de ambiente (DB_PASSWORD / PGPASSWORD) ou getpass.
- Retorna código de saída 0 (sucesso) ou 1 (falha).
"""

import os
import sys
import socket
import argparse
import getpass
from typing import Dict, Any


def mask_string(val: str, show_chars: int = 4) -> str:
    """Mascara strings sensíveis preservando prefixo identificador."""
    if not val:
        return "[NÃO DEFINIDO]"
    if len(val) <= show_chars * 2:
        return "***"
    return f"{val[:show_chars]}...{val[-show_chars:]}"


def test_tcp_port(host: str, port: int, timeout_sec: int = 5) -> bool:
    """Testa a abertura de socket TCP ou Unix Domain Socket com timeout curto."""
    if host.startswith("/"):
        socket_path = f"{host.rstrip('/')}/.s.PGSQL.{port}"
        print(f"[1/3] Testando conexão via Unix Domain Socket em {socket_path}...")
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(timeout_sec)
            s.connect(socket_path)
            s.close()
            print("  ✓ Conexão via Unix Domain Socket estabelecida com sucesso.")
            return True
        except Exception as e:
            print(f"  ✗ Falha ao conectar no socket Unix: {e}")
            return False

    print(f"[1/3] Testando resolução de rede e conexão TCP em {mask_string(host)}:{port} (timeout {timeout_sec}s)...")
    try:
        with socket.create_connection((host, port), timeout=timeout_sec):
            print("  ✓ Conexão de rede TCP estabelecida com sucesso.")
            return True
    except socket.gaierror as e:
        print(f"  ✗ Falha na resolução de nome DNS: {e.strerror}")
        return False
    except (socket.timeout, TimeoutError):
        print(f"  ✗ Timeout ({timeout_sec}s) esgotado ao tentar alcançar o host {mask_string(host)}.")
        print("    Dica: Se estiver usando o Supabase, utilize o host do Session Pooler (ex.: aws-1-sa-east-1.pooler.supabase.com) compatível com IPv4.")
        return False
    except ConnectionRefusedError:
        print(f"  ✗ Conexão recusada na porta {port}. Verifique se o serviço está ativo.")
        return False
    except OSError as e:
        print(f"  ✗ Erro de rede: {e}")
        return False


def test_postgresql_handshake(
    host: str,
    port: int,
    dbname: str,
    user: str,
    password: str,
    sslmode: str,
    timeout_sec: int = 8,
) -> bool:
    """Testa handshake SSL e autenticação com o PostgreSQL via psycopg 3."""
    print(f"[2/3] Testando handshake SSL (sslmode='{sslmode}') e autenticação...")
    try:
        import psycopg
    except ImportError:
        print("  ✗ Erro: Biblioteca 'psycopg' não encontrada. Instale via requirements.txt.")
        return False

    conn_info: Dict[str, Any] = {
        "host": host,
        "port": port,
        "dbname": dbname,
        "user": user,
        "password": password,
        "sslmode": sslmode,
        "connect_timeout": timeout_sec,
    }

    try:
        with psycopg.connect(**conn_info) as conn:
            with conn.cursor() as cur:
                print("  ✓ Autenticação e handshake SSL bem-sucedidos!")
                print("[3/3] Coletando metadados seguros da instância...")
                cur.execute("SELECT version();")
                pg_version = cur.fetchone()[0]
                cur.execute("SELECT current_database(), current_user;")
                db_name, cur_user = cur.fetchone()
                cur.execute("SELECT pg_is_in_recovery();")
                in_recovery = cur.fetchone()[0]

                print(f"  - Banco Conectado: {db_name}")
                print(f"  - Usuário Ativo:   {cur_user}")
                print(f"  - Modo Réplica:    {'Sim (Somente Leitura)' if in_recovery else 'Não (Primário / Escrita)'}")
                print(f"  - Versão Motor:    {pg_version.split(',')[0]}")
                return True
    except psycopg.OperationalError as e:
        # Sanitiza a mensagem para não expor senha se vier incluída
        err_msg = str(e)
        if password and password in err_msg:
            err_msg = err_msg.replace(password, "[SENHA MASCARADA]")
        print(f"  ✗ Falha operacional ao conectar ao PostgreSQL: {err_msg}")
        return False
    except Exception as e:
        print(f"  ✗ Erro inesperado durante handshake: {type(e).__name__}")
        return False


def resolve_password(cli_password: str = "", host: str = "localhost") -> str:
    """Resolve a senha de forma segura: CLI -> DB_PASSWORD -> PGPASSWORD -> getpass."""
    if cli_password:
        return cli_password
    env_pwd = os.environ.get("DB_PASSWORD") or os.environ.get("PGPASSWORD")
    if env_pwd:
        return env_pwd
    is_remote = host not in ("localhost", "127.0.0.1", "") and not host.startswith("/")
    if not is_remote:
        # Para hosts locais (localhost, socket Unix), não solicita senha por padrão (autenticação trust/peer)
        return ""
    if sys.stdin.isatty():
        try:
            return getpass.getpass("Digite a senha do banco PostgreSQL (ou Enter para vazio): ")
        except (EOFError, KeyboardInterrupt):
            print("\nOperação cancelada pelo usuário.")
            sys.exit(1)
    print("  ⚠️  Aviso: Nenhuma senha fornecida para conexão remota (defina DB_PASSWORD ou PGPASSWORD).")
    return ""


def main():
    parser = argparse.ArgumentParser(
        description="SOSP Preflight Connectivity Check (Não destrutivo / Somente leitura)"
    )
    parser.add_argument("--host", default=os.environ.get("DB_HOST", "localhost"), help="Host do banco")
    parser.add_argument("--port", type=int, default=int(os.environ.get("DB_PORT", "5432")), help="Porta do banco")
    parser.add_argument("--dbname", default=os.environ.get("DB_NAME", "postgres"), help="Nome da base")
    parser.add_argument("--user", default=os.environ.get("DB_USER", "postgres"), help="Usuário")
    parser.add_argument("--password", default="", help="(Opcional) Senha. Se omitido, lê de DB_PASSWORD/PGPASSWORD ou solicita via getpass.")
    parser.add_argument("--sslmode", default=os.environ.get("DB_SSLMODE", "prefer"), help="Modo SSL")
    parser.add_argument("--timeout", type=int, default=8, help="Timeout em segundos")

    args = parser.parse_args()

    password = resolve_password(args.password, args.host)

    print("=" * 70)
    print("SOSP — Pré-Voo de Conectividade com Banco de Dados")
    print("=" * 70)
    print(f"Host:     {mask_string(args.host)}")
    print(f"Porta:    {args.port}")
    print(f"Base:     {args.dbname}")
    print(f"Usuário:  {mask_string(args.user)}")
    print(f"SSL Mode: {args.sslmode}")
    print("-" * 70)

    # 1. Teste de Socket / Rede
    if not test_tcp_port(args.host, args.port, timeout_sec=min(args.timeout, 5)):
        print("\n❌ PRÉ-VOO REPROVADO NA ETAPA DE REDE.")
        sys.exit(1)

    # 2. Teste de Autenticação / Postgres
    if not test_postgresql_handshake(
        args.host,
        args.port,
        args.dbname,
        args.user,
        password,
        args.sslmode,
        timeout_sec=args.timeout,
    ):
        print("\n❌ PRÉ-VOO REPROVADO NO HANDSHAKE POSTGRESQL.")
        sys.exit(1)

    print("\n✅ PRÉ-VOO DE CONECTIVIDADE CONCLUÍDO COM SUCESSO.")
    sys.exit(0)


if __name__ == "__main__":
    main()
