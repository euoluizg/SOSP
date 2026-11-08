#!/usr/bin/env python3
"""
SOSP — Módulo de Proteção e Guarda de Isolamento Local (Portão B).
Garante que NENHUM teste de integração ou homologação conecte ao Supabase remoto
ou a qualquer provedor de nuvem externo.
Permite exclusivamente conexões contra PostgreSQL local (127.0.0.1, localhost, unix socket).
"""

import os
import sys

FORBIDDEN_HOST_PATTERNS = [
    "supabase",
    "pooler",
    "aws",
    "rds",
    "sa-east-1",
    "cidtcgfowvgwgggvhbym",
    "azure",
    "gcp",
    "compute",
    "azurecontainer",
]

PERMITTED_LOCAL_HOSTS = ["127.0.0.1", "localhost", "::1"]


def assert_strictly_local_test_environment(target_host: str | None = None) -> None:
    """
    Verifica exaustivamente argumentos, variáveis de ambiente e configurações.
    Lança RuntimeError imediato se qualquer parâmetro sugerir execução remota.
    """
    hosts_to_inspect = []
    if target_host:
        hosts_to_inspect.append(("target_host", target_host))

    for env_key in ["DB_HOST", "PGHOST", "DATABASE_URL"]:
        val = os.environ.get(env_key)
        if val:
            hosts_to_inspect.append((env_key, val))

    # Verifica cada host candidato
    for origin, host_str in hosts_to_inspect:
        h = str(host_str).strip().lower()

        # 1. Bloqueio por padrão de provedor de nuvem / supabase
        for pattern in FORBIDDEN_HOST_PATTERNS:
            if pattern in h:
                raise RuntimeError(
                    f"❌ [BLOQUEIO CRÍTICO DE SEGURANÇA PORTÃO B]\n"
                    f"Origem '{origin}' contém '{pattern}' no host '{host_str}'.\n"
                    f"Execuções no Portão B são ESTRITAMENTE LOCAIS em cluster descartável.\n"
                    f"Operação abortada imediatamente para proteger o ambiente remoto."
                )

        # 2. Permissão exclusiva para local
        if h in PERMITTED_LOCAL_HOSTS or h.startswith("/"):
            continue

        raise RuntimeError(
            f"❌ [BLOQUEIO DE SEGURANÇA PORTÃO B]\n"
            f"Host '{host_str}' (de '{origin}') não é um endereço local autorizado.\n"
            f"Permitidos exclusivamente: 127.0.0.1, localhost ou socket Unix (iniciado por '/')."
        )


if __name__ == "__main__":
    test_val = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    try:
        assert_strictly_local_test_environment(test_val)
        print(f"✓ Host '{test_val}' aprovado como estritamente local.")
    except RuntimeError as e:
        print(e)
        sys.exit(1)
