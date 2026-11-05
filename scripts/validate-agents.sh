#!/usr/bin/env bash
# =============================================================================
# SOSP — Script de Validação Não-Destrutiva dos 23 Agentes, Rules e Skills
# Verifica: Antigravity (.agents/), OpenCode (.opencode/ + opencode.json),
# Hermes (skill multiagent-development-orchestrator), links e modelos.
# =============================================================================

set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() { echo "✅ [PASS] $1"; PASS_COUNT=$((PASS_COUNT + 1)); }
warn() { echo "⚠️  [WARN] $1"; WARN_COUNT=$((WARN_COUNT + 1)); }
fail() { echo "❌ [FAIL] $1"; FAIL_COUNT=$((FAIL_COUNT + 1)); }

echo "============================================================================="
echo " AUDITORIA AUTOMATIZADA DE AGENTES — SOSP ($REPO_ROOT)"
echo "============================================================================="

# 1. Lista oficial dos 23 agentes esperados
EXPECTED_AGENTS=(
  # Frontend (8)
  "react-cto"
  "software-architect"
  "react-specialist"
  "nextjs-specialist"
  "ui-ux-engineer"
  "backend-engineer"
  "qa-engineer"
  "security-performance-engineer"
  # Backend (8)
  "backend-lead"
  "django-api-engineer"
  "django-domain-engineer"
  "postgresql-data-architect"
  "django-orm-migrations-engineer"
  "backend-auth-security-engineer"
  "backend-performance-engineer"
  "backend-integration-engineer"
  # QA (7)
  "test-lead"
  "frontend-test-engineer"
  "backend-api-tester"
  "integration-e2e-engineer"
  "database-test-engineer"
  "security-tester"
  "performance-engineer"
)

echo ""
echo "--- 1. Verificando Existência e Unicidade dos 23 Agentes (.agents/agents/ e .opencode/agents/) ---"
for ag in "${EXPECTED_AGENTS[@]}"; do
  if [[ -f ".agents/agents/${ag}.md" ]]; then
    pass "Agente Antigravity instalado: .agents/agents/${ag}.md"
  else
    fail "Agente Antigravity ausente: .agents/agents/${ag}.md"
  fi

  if [[ -f ".opencode/agents/${ag}.md" ]]; then
    pass "Agente OpenCode instalado: .opencode/agents/${ag}.md"
  else
    fail "Agente OpenCode ausente: .opencode/agents/${ag}.md"
  fi
done

AG_TOTAL=$(find .agents/agents -maxdepth 1 -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
OC_TOTAL=$(find .opencode/agents -maxdepth 1 -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
if [[ "$AG_TOTAL" == "23" && "$OC_TOTAL" == "23" ]]; then
  pass "Contagem exata de 23 agentes sem duplicatas (.agents=$AG_TOTAL, .opencode=$OC_TOTAL)"
else
  fail "Contagem inesperada de agentes (.agents=$AG_TOTAL, .opencode=$OC_TOTAL; esperado=23)"
fi

echo ""
echo "--- 2. Verificando Metadados, Modelos, Rules (.agents/rules/) e Skills (.agents/skills/) ---"
python3 - <<'PYEOF'
import os, re, json, sys

root = os.getcwd()
errors = 0

# Check .agents/agents/*.md frontmatter
for fn in sorted(os.listdir(os.path.join(root, ".agents/agents"))):
    if not fn.endswith(".md"):
        continue
    p = os.path.join(root, ".agents/agents", fn)
    txt = open(p, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", txt, flags=re.DOTALL)
    if not m:
        print(f"❌ [FAIL] Frontmatter inválido em .agents/agents/{fn}")
        errors += 1
        continue
    fm = m.group(1)
    for req in ["name:", "description:", "subagent:", "model:"]:
        if req not in fm:
            print(f"❌ [FAIL] Campo '{req}' ausente em .agents/agents/{fn}")
            errors += 1

# Check .opencode/agents/*.md frontmatter (description, mode, model, permissions)
for fn in sorted(os.listdir(os.path.join(root, ".opencode/agents"))):
    if not fn.endswith(".md"):
        continue
    p = os.path.join(root, ".opencode/agents", fn)
    txt = open(p, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", txt, flags=re.DOTALL)
    if not m:
        print(f"❌ [FAIL] Frontmatter inválido em .opencode/agents/{fn}")
        errors += 1
        continue
    fm = m.group(1)
    for req in ["description:", "mode:", "model:", "permissions:"]:
        if req not in fm:
            print(f"❌ [FAIL] Campo '{req}' ausente em .opencode/agents/{fn}")
            errors += 1

# Check .agents/rules/*.md
rules_dir = os.path.join(root, ".agents/rules")
rule_files = [f for f in sorted(os.listdir(rules_dir)) if f.endswith(".md")]
if len(rule_files) < 9:
    print(f"❌ [FAIL] Esperadas ao menos 9 rules em .agents/rules/, encontradas: {len(rule_files)}")
    errors += 1
for fn in rule_files:
    p = os.path.join(rules_dir, fn)
    if os.path.getsize(p) >= 24000:
        print(f"❌ [FAIL] Rule excede limite de 24KB: {fn}")
        errors += 1

# Check .agents/skills/*/SKILL.md
skills_dir = os.path.join(root, ".agents/skills")
skill_dirs = [d for d in sorted(os.listdir(skills_dir)) if os.path.isdir(os.path.join(skills_dir, d))]
if "multiagent-development-orchestrator" not in skill_dirs:
    print("❌ [FAIL] Skill multiagent-development-orchestrator ausente em .agents/skills/")
    errors += 1

for d in skill_dirs:
    sp = os.path.join(skills_dir, d, "SKILL.md")
    if not os.path.isfile(sp):
        print(f"❌ [FAIL] SKILL.md ausente em .agents/skills/{d}")
        errors += 1
        continue
    txt = open(sp, encoding="utf-8").read()
    if not re.match(r"^---\n.*?name:.*?description:.*?\n---", txt, flags=re.DOTALL):
        print(f"❌ [FAIL] Frontmatter inválido em .agents/skills/{d}/SKILL.md")
        errors += 1

# Check opencode.json
oc_json = os.path.join(root, "opencode.json")
if not os.path.isfile(oc_json):
    print("❌ [FAIL] opencode.json ausente na raiz")
    errors += 1
else:
    data = json.load(open(oc_json, encoding="utf-8"))
    perm = data.get("permission", {})
    if perm.get("edit") != "ask" or perm.get("bash") != "ask":
        print("❌ [FAIL] opencode.json não está com permissões supervisionadas (edit/bash = ask)")
        errors += 1

# Check relative links in docs/agent-*.md and AGENTS.md
check_docs = [
    "AGENTS.md",
    "docs/agent-architecture.md",
    "docs/agent-workflow.md",
    "docs/agent-model-matrix.md",
    "docs/agent-installation-report.md",
]
for rel in check_docs:
    fp = os.path.join(root, rel)
    if not os.path.isfile(fp):
        print(f"❌ [FAIL] Documento obrigatório ausente: {rel}")
        errors += 1
        continue
    txt = open(fp, encoding="utf-8").read()
    for m in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", txt):
        target = m.group(1).split("#")[0].strip()
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        resolved = os.path.normpath(os.path.join(os.path.dirname(fp), target))
        if not os.path.exists(resolved):
            print(f"❌ [FAIL] Link quebrado em {rel} -> {target}")
            errors += 1

if errors == 0:
    print(f"✅ [PASS] Metadados de 23 agentes (.agents e .opencode), {len(rule_files)} rules, {len(skill_dirs)} skills, opencode.json e links validados sem erros.")
else:
    sys.exit(1)
PYEOF

if [[ $? -eq 0 ]]; then
  pass "Validação estrutural Python concluída com 0 erros"
else
  fail "Validação estrutural Python encontrou erros"
fi

echo ""
echo "--- 3. Verificando Disponibilidade dos CLIs e Reconhecimento Real ---"
if [[ -x "/Users/euoluizg/.local/bin/hermes" ]]; then
  H_VER=$(/Users/euoluizg/.local/bin/hermes --version 2>/dev/null | head -n 1)
  pass "Hermes CLI encontrado: $H_VER"
else
  warn "Hermes CLI não encontrado em ~/.local/bin/hermes"
fi

if [[ -f "/Users/euoluizg/.hermes/skills/software-development/multiagent-development-orchestrator/SKILL.md" ]]; then
  pass "Skill multiagent-development-orchestrator instalada em ~/.hermes/skills/"
else
  warn "Skill multiagent-development-orchestrator não encontrada em ~/.hermes/skills/"
fi

if command -v opencode >/dev/null 2>&1; then
  OC_VER=$(opencode --version 2>/dev/null | head -n 1)
  pass "OpenCode CLI encontrado: $OC_VER"
else
  warn "OpenCode CLI não encontrado no PATH"
fi

if [[ -d "/Applications/Antigravity IDE.app" ]]; then
  pass "Google Antigravity IDE.app instalado em /Applications"
else
  warn "Google Antigravity IDE.app não encontrado em /Applications"
fi

echo ""
echo "============================================================================="
echo " RESUMO DA VALIDAÇÃO: PASS=$PASS_COUNT | WARN=$WARN_COUNT | FAIL=$FAIL_COUNT"
echo "============================================================================="
exit $FAIL_COUNT

