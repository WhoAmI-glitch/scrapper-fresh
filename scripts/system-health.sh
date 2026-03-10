#!/usr/bin/env bash
set -euo pipefail

# system-health.sh — Multi-agent system health monitor
# Reports on system integrity, artifact counts, and potential issues.

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STATE_DIR="$PROJECT_ROOT/.claude/state"
AGENTS_DIR="$PROJECT_ROOT/.claude/agents"
SKILLS_DIR="$PROJECT_ROOT/.claude/skills"
COMMANDS_DIR="$PROJECT_ROOT/.claude/commands"
SCHEMAS_DIR="$PROJECT_ROOT/.claude/schemas"
REGISTRY="$AGENTS_DIR/REGISTRY.json"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

pass() { echo -e "  ${GREEN}PASS${NC}  $1"; }
warn() { echo -e "  ${YELLOW}WARN${NC}  $1"; }
fail() { echo -e "  ${RED}FAIL${NC}  $1"; }

echo "=== Multi-Agent System Health Check ==="
echo ""

total_checks=0
total_pass=0
total_warn=0
total_fail=0

check() {
  total_checks=$((total_checks + 1))
}

# --- 1. Directory Structure ---
echo "--- Directory Structure ---"

required_dirs=(
  ".claude/agents"
  ".claude/skills/s-tier"
  ".claude/skills/a-tier"
  ".claude/commands"
  ".claude/schemas"
  ".claude/state/tasks"
  ".claude/state/handoffs"
  ".claude/state/findings"
  ".claude/state/decisions"
  ".claude/state/workflows"
  ".claude/quality/scripts"
  ".claude/policy/proposals"
  ".claude/policy/archive"
  "rules/common"
  "scripts"
)

for dir in "${required_dirs[@]}"; do
  check
  if [[ -d "$PROJECT_ROOT/$dir" ]]; then
    pass "$dir/"
    total_pass=$((total_pass + 1))
  else
    fail "$dir/ missing"
    total_fail=$((total_fail + 1))
  fi
done

echo ""

# --- 2. Registry Integrity ---
echo "--- Registry Integrity ---"

check
if [[ -f "$REGISTRY" ]]; then
  if jq empty "$REGISTRY" 2>/dev/null; then
    pass "REGISTRY.json is valid JSON"
    total_pass=$((total_pass + 1))
  else
    fail "REGISTRY.json is invalid JSON"
    total_fail=$((total_fail + 1))
  fi
else
  fail "REGISTRY.json not found"
  total_fail=$((total_fail + 1))
fi

check
registry_count=$(jq '.agents | length' "$REGISTRY" 2>/dev/null || echo 0)
agent_files=$(find "$AGENTS_DIR" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
if [[ "$registry_count" -eq "$agent_files" ]]; then
  pass "Registry ($registry_count) matches agent files ($agent_files)"
  total_pass=$((total_pass + 1))
else
  fail "Registry ($registry_count) != agent files ($agent_files)"
  total_fail=$((total_fail + 1))
fi

echo ""

# --- 3. Schema Coverage ---
echo "--- Schema Coverage ---"

expected_schemas=("task" "handoff" "finding" "decision" "quality-report" "proposal")
for schema_name in "${expected_schemas[@]}"; do
  check
  if [[ -f "$SCHEMAS_DIR/${schema_name}.schema.json" ]]; then
    if jq empty "$SCHEMAS_DIR/${schema_name}.schema.json" 2>/dev/null; then
      pass "${schema_name}.schema.json"
      total_pass=$((total_pass + 1))
    else
      fail "${schema_name}.schema.json is invalid"
      total_fail=$((total_fail + 1))
    fi
  else
    fail "${schema_name}.schema.json missing"
    total_fail=$((total_fail + 1))
  fi
done

echo ""

# --- 4. Script Health ---
echo "--- Script Health ---"

expected_scripts=("orchestrate.sh" "handoff.sh" "decide.sh" "propose-policy.sh" "finding.sh" "quality-report.sh" "validate-schema.py" "system-health.sh")
for script in "${expected_scripts[@]}"; do
  check
  if [[ -f "$PROJECT_ROOT/scripts/$script" ]]; then
    pass "scripts/$script"
    total_pass=$((total_pass + 1))
  else
    warn "scripts/$script missing"
    total_warn=$((total_warn + 1))
  fi
done

echo ""

# --- 5. Quality Gate ---
echo "--- Quality Gate ---"

quality_scripts=("validate.sh" "check-agents.sh" "check-skills.sh" "check-commands.sh" "check-refs.sh")
for qs in "${quality_scripts[@]}"; do
  check
  if [[ -f "$PROJECT_ROOT/.claude/quality/scripts/$qs" ]]; then
    pass ".claude/quality/scripts/$qs"
    total_pass=$((total_pass + 1))
  else
    warn ".claude/quality/scripts/$qs missing"
    total_warn=$((total_warn + 1))
  fi
done

echo ""

# --- 6. State Artifact Counts ---
echo "--- State Artifacts ---"

for dir in tasks handoffs findings decisions workflows; do
  count=$(find "$STATE_DIR/$dir" -name "*.json" -not -name ".gitkeep" 2>/dev/null | wc -l | tr -d ' ')
  echo "  $dir: $count"
done

proposal_count=$(find "$STATE_DIR/proposals" -name "*.json" -not -name ".gitkeep" 2>/dev/null | wc -l | tr -d ' ')
echo "  proposals: $proposal_count"

echo ""

# --- 7. Git Hook ---
echo "--- Git Integration ---"

check
if [[ -f "$PROJECT_ROOT/.git/hooks/pre-commit" ]]; then
  pass "pre-commit hook installed"
  total_pass=$((total_pass + 1))
else
  warn "pre-commit hook not installed (run: ln -s ../../.claude/hooks/pre-commit.sh .git/hooks/pre-commit)"
  total_warn=$((total_warn + 1))
fi

echo ""

# --- 8. Skills & Commands ---
echo "--- Component Counts ---"

s_tier=$(find "$SKILLS_DIR/s-tier" -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')
a_tier=$(find "$SKILLS_DIR/a-tier" -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')
commands=$(find "$COMMANDS_DIR" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
rules=$(find "$PROJECT_ROOT/rules" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')

echo "  Agents:    $agent_files"
echo "  Skills:    $((s_tier + a_tier)) (s-tier: $s_tier, a-tier: $a_tier)"
echo "  Commands:  $commands"
echo "  Schemas:   ${#expected_schemas[@]}"
echo "  Rules:     $rules"

echo ""

# --- Summary ---
echo "=== Health Summary ==="
echo -e "  ${GREEN}Pass:${NC} $total_pass"
echo -e "  ${YELLOW}Warn:${NC} $total_warn"
echo -e "  ${RED}Fail:${NC} $total_fail"
echo "  Total checks: $total_checks"
echo ""

if [[ $total_fail -gt 0 ]]; then
  echo -e "${RED}System has failures — fix before proceeding.${NC}"
  exit 1
elif [[ $total_warn -gt 0 ]]; then
  echo -e "${YELLOW}System operational with warnings.${NC}"
  exit 0
else
  echo -e "${GREEN}System fully healthy.${NC}"
  exit 0
fi
