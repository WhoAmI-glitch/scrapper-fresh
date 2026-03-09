#!/usr/bin/env bash
set -euo pipefail

# score-change.sh — Evaluate a finding against quality gates
# Usage: score-change.sh <finding-id>
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
CLAUDE_DIR="${REPO_ROOT}/.claude"
FINDING_ID="${1:-}"

if [ -z "${FINDING_ID}" ]; then
  echo "Usage: score-change.sh <finding-id>"
  exit 1
fi

FINDING_FILE="${CLAUDE_DIR}/state/findings/${FINDING_ID}.json"
if [ ! -f "${FINDING_FILE}" ]; then
  echo "Finding not found: ${FINDING_FILE}"
  exit 1
fi

echo "=== Scoring change for ${FINDING_ID} ==="

# Run automated checks and collect results
SCORE=0
TOTAL_WEIGHT=0

run_check() {
  local name=$1
  local weight=$2
  local command=$3

  TOTAL_WEIGHT=$(echo "${TOTAL_WEIGHT} + ${weight}" | bc)

  if eval "${command}" > /dev/null 2>&1; then
    SCORE=$(echo "${SCORE} + ${weight}" | bc)
    echo "  PASS: ${name} (+${weight})"
  else
    echo "  FAIL: ${name} (0/${weight})"
  fi
}

run_check "correctness" 25 "${CLAUDE_DIR}/quality/scripts/validate.sh correctness"
run_check "regressions" 20 "${CLAUDE_DIR}/quality/scripts/validate.sh regressions"
run_check "duplication" 10 "${CLAUDE_DIR}/quality/scripts/check-duplication.sh"
run_check "contracts" 10 "${CLAUDE_DIR}/quality/scripts/validate.sh contracts"
run_check "tests" 10 "${CLAUDE_DIR}/quality/scripts/validate.sh tests"
run_check "runnability" 3 "${CLAUDE_DIR}/quality/scripts/validate.sh runnability"

# Manual checks get assumed pass for automated scoring
SCORE=$((SCORE + 22))  # completeness(20) + documentation(2)

echo ""
echo "Score: ${SCORE}/100"

# Read thresholds from gates.json
ACCEPT=$(python3 -c "import json; print(json.load(open('${CLAUDE_DIR}/quality/gates.json'))['thresholds']['accept'])")
NOTES=$(python3 -c "import json; print(json.load(open('${CLAUDE_DIR}/quality/gates.json'))['thresholds']['accept_with_notes'])")

if [ "${SCORE}" -ge "${ACCEPT}" ]; then
  echo "Verdict: ACCEPT"
elif [ "${SCORE}" -ge "${NOTES}" ]; then
  echo "Verdict: ACCEPT_WITH_NOTES"
else
  echo "Verdict: REJECT"
fi
