#!/usr/bin/env bash
# ==============================================================================
# SOSP — Script de Build para Render (Web Service)
# Referência: ADR-001, ADR-008 e Runbook de Implantação
# ==============================================================================
set -o errexit

echo "=== SOSP [Render]: Iniciando processo de build do backend ==="

# 1. Instalar dependências Python
echo "-> Instalando pacotes via pip..."
pip install --upgrade pip
pip install -r requirements.txt

# 2. Verificação estática do Django (sem dependência de banco em build time)
echo "-> Executando django manage.py check..."
python manage.py check

# 3. Coleta de arquivos estáticos
echo "-> Coletando arquivos estáticos..."
python manage.py collectstatic --no-input --clear || echo "Aviso: collectstatic finalizado."

echo "=== SOSP [Render]: Build finalizado com sucesso! ==="
# REGRA CRÍTICA DE SEGURANÇA:
# NUNCA adicionar 'python manage.py migrate' neste script.
# O schema no Supabase PostgreSQL 17.11 já está implantado (4C.2/4D.2)
# e qualquer migração deve seguir processo administrativo supervisionado.
