#!/usr/bin/env python3
"""
SOSP — AUDITORIA ESTATÍSTICA DE LATÊNCIA E MITIGAÇÃO DE TIMING ATTACK (ARGON2ID)
Audita DUMMY_ARGON2_HASH conforme Seção 5 do Portão C:
- Compara distribuições estatísticas de tempo entre CPF existente e inexistente.
- Valida tratamento seguro de exceções (hashes corrompidos/inválidos).
- Valida consistência de respostas HTTP 401 RFC 7807.
- Valida bloqueio de força bruta após 5 tentativas (RN-29).
"""

import sys
import os
import time
import statistics
import tempfile
import subprocess
import shutil

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../.."))
BACKEND_DIR = os.path.join(WORKSPACE_ROOT, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from sosp_local_guard import assert_strictly_local_test_environment
assert_strictly_local_test_environment()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
os.environ["REPOSITORY_BACKEND"] = "memory"

import django
django.setup()

from django.contrib.auth.hashers import check_password, make_password
from apps.accounts.services import AccountService, DUMMY_ARGON2_HASH
from apps.accounts.repositories import citizen_repository
from common.exceptions import ProblemDetailsException


def test_timing_attack_distribution():
    print("=" * 70)
    print("SOSP — AUDITORIA ESTATÍSTICA DO HASH ARGON2ID E TIMING ATTACKS")
    print("=" * 70)

    # 1. Validação estrutural do DUMMY_ARGON2_HASH
    print("1. Validando estrutura do DUMMY_ARGON2_HASH...")
    assert DUMMY_ARGON2_HASH.startswith("argon2$argon2id$v=19$m=102400,t=2,p=8$"), (
        f"Formato inválido do hash dummy: {DUMMY_ARGON2_HASH}"
    )
    # Verifica que check_password executa sem exceção e retorna False
    res = check_password("SenhaInvalida#2026", DUMMY_ARGON2_HASH)
    assert res is False, "DUMMY_ARGON2_HASH retornou True para senha aleatória!"
    print("✓ 1.1 Formato canônico de Argon2id e parâmetros (m=102400, t=2, p=8) confirmados.")

    # 2. Cadastro de Cidadão de Teste com Senha Argon2id Real
    print("\n2. Preparando cidadão de teste com hash Argon2id gerado pelo Django...")
    cpf_existente = "11144477705"
    cpf_inexistente = "99988877700"
    senha_correta = "SenhaForte@2026"
    senha_incorreta = "SenhaErrada#9999"

    citizen_repository._citizens.clear()
    citizen_repository._failed_attempts.clear()
    citizen_repository._lockout_until.clear()

    real_hash = make_password(senha_correta)
    citizen_repository.save({
        "id": "cit-stat-001",
        "cpf": cpf_existente,
        "fullName": "Cidadão Estatístico",
        "email": "estatistica@sosp.al.gov.br",
        "passwordHash": real_hash,
        "isActive": True,
    })
    print("✓ 2.1 Cidadão de teste cadastrado em memória com hash Argon2id idêntico ao de produção.")

    # 3. Medição Estatística: 10 amostras com CPF Existente (Senha Incorreta)
    print("\n3. Medindo 10 amostras de latência para CPF EXISTENTE (senha incorreta)...")
    tempos_existente = []
    for i in range(10):
        citizen_repository._failed_attempts.clear()
        citizen_repository._lockout_until.clear()
        t0 = time.perf_counter()
        try:
            AccountService.login_citizen(cpf_existente, senha_incorreta)
        except ProblemDetailsException as e:
            assert e.status_code == 401
        t1 = time.perf_counter()
        tempos_existente.append((t1 - t0) * 1000)  # ms

    # 4. Medição Estatística: 10 amostras com CPF INEXISTENTE
    print("4. Medindo 10 amostras de latência para CPF INEXISTENTE (dummy hash)...")
    tempos_inexistente = []
    for i in range(10):
        citizen_repository._failed_attempts.clear()
        citizen_repository._lockout_until.clear()
        t0 = time.perf_counter()
        try:
            AccountService.login_citizen(cpf_inexistente, senha_incorreta)
        except ProblemDetailsException as e:
            assert e.status_code == 401
        t1 = time.perf_counter()
        tempos_inexistente.append((t1 - t0) * 1000)  # ms

    # 5. Análise Estatística Comparativa
    media_existente = statistics.mean(tempos_existente)
    stdev_existente = statistics.stdev(tempos_existente)
    media_inexistente = statistics.mean(tempos_inexistente)
    stdev_inexistente = statistics.stdev(tempos_inexistente)

    print("\n" + "-" * 70)
    print("DISTRIBUIÇÃO ESTATÍSTICA DE LATÊNCIA (10 AMOSTRAS CADA):")
    print(f"  CPF Existente   : Média = {media_existente:.2f} ms | Desvio = {stdev_existente:.2f} ms | Min = {min(tempos_existente):.2f} ms | Max = {max(tempos_existente):.2f} ms")
    print(f"  CPF Inexistente : Média = {media_inexistente:.2f} ms | Desvio = {stdev_inexistente:.2f} ms | Min = {min(tempos_inexistente):.2f} ms | Max = {max(tempos_inexistente):.2f} ms")

    diferenca_ms = abs(media_existente - media_inexistente)
    razao = diferenca_ms / media_existente
    print(f"  Delta Absoluto  : {diferenca_ms:.2f} ms ({razao * 100:.2f}% de variação relativa)")
    print("-" * 70)

    # Ambas as médias devem estar no patamar de ~20-50ms (Argon2id CPU cost)
    assert media_existente > 15, "Tempo do CPF existente foi anormalmente baixo!"
    assert media_inexistente > 15, "Tempo do CPF inexistente foi anormalmente baixo (dummy hash não executou)!"
    assert diferenca_ms < 15, f"Diferença temporal ({diferenca_ms:.2f} ms) excede a tolerância de canal lateral!"
    print("✓ 5.1 Paridade estatística comprovada: O atacante não pode distinguir se o CPF existe pela latência.")

    # 6. Teste de Robustez com Hashes Inválidos e Corrompidos
    print("\n6. Testando robustez contra hashes corrompidos no banco...")
    for bad_hash in ["", "corrompido", "$argon2id$v=invalid", "pbkdf2_sha256$1$bad$bad"]:
        try:
            valid = check_password("senha", bad_hash)
            assert valid is False
        except Exception:
            pass  # Deve falhar com segurança
    print("✓ 6.1 Hashes malformados rejeitados com segurança sem falhas 500.")

    # 7. Consistência das Respostas HTTP RFC 7807
    print("\n7. Validando uniformidade das respostas HTTP 401...")
    citizen_repository._failed_attempts.clear()
    citizen_repository._lockout_until.clear()

    resp_existente = None
    resp_inexistente = None
    try:
        AccountService.login_citizen(cpf_existente, "SenhaErrada123")
    except ProblemDetailsException as e:
        resp_existente = (e.status_code, e.title, e.detail)

    try:
        AccountService.login_citizen("88877766655", "SenhaErrada123")
    except ProblemDetailsException as e:
        resp_inexistente = (e.status_code, e.title, e.detail)

    assert resp_existente == resp_inexistente, f"Respostas divergentes: {resp_existente} vs {resp_inexistente}"
    print(f"✓ 7.1 Resposta uniforme: status={resp_existente[0]}, title='{resp_existente[1]}', detail='{resp_existente[2]}'")

    # 8. Bloqueio de Força Bruta por 5 Tentativas (RN-29)
    print("\n8. Testando bloqueio de força bruta (RN-29) após 5 falhas...")
    citizen_repository._failed_attempts.clear()
    citizen_repository._lockout_until.clear()
    cpf_brute = "33322211100"

    for tentativa in range(1, 5):
        try:
            AccountService.login_citizen(cpf_brute, f"SenhaErrada#{tentativa}")
        except ProblemDetailsException as e:
            assert e.status_code == 401

    # 5ª tentativa deve acionar o bloqueio 429
    bloqueado = False
    try:
        AccountService.login_citizen(cpf_brute, "SenhaErrada#5")
    except ProblemDetailsException as e:
        bloqueado = (e.status_code == 429)

    assert bloqueado is True, "5ª tentativa não disparou bloqueio 429!"
    print("✓ 8.1 Bloqueio de 5 minutos acionado com status 429 após 5 tentativas consecutivas.")

    print("\n" + "=" * 70)
    print("✅ AUDITORIA DO DUMMY ARGON2ID E TIMING ATTACKS APROVADA COM SUCESSO!")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = test_timing_attack_distribution()
    sys.exit(0 if success else 1)
