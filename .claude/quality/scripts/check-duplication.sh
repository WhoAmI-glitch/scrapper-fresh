#!/usr/bin/env bash
set -uo pipefail

# check-duplication.sh — Detect duplicate content and logic
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
CLAUDE_DIR="${REPO_ROOT}/.claude"
ISSUES=0

echo "=== Duplication Check ==="

# 1. Check for duplicate agent responsibilities
echo "Checking agent boundary overlaps..."
if [ -d "${CLAUDE_DIR}/agents" ]; then
  if ! python3 -c "
import json, sys
from collections import Counter
registry = json.load(open('${CLAUDE_DIR}/agents/REGISTRY.json'))
all_owns = []
for name, agent in registry.get('agents', {}).items():
    for item in agent.get('owns', []):
        all_owns.append((item.lower().strip(), name))
seen = Counter(item for item, _ in all_owns)
dupes = {k: v for k, v in seen.items() if v > 1}
if dupes:
    print('WARNING: Overlapping ownership detected:')
    for item, count in dupes.items():
        owners = [name for i, name in all_owns if i == item]
        print(f'  \"{item}\" owned by: {owners}')
    sys.exit(1)
else:
    print('OK: No overlapping agent ownership')
" 2>/dev/null; then
    ISSUES=1
  fi
fi

# 2. Check for duplicate files (same content, different paths)
echo "Checking for duplicate file content..."
DUPES=$(find "${CLAUDE_DIR}" \( -name "*.md" -o -name "*.json" \) -not -name ".gitkeep" -exec shasum {} \; 2>/dev/null \
  | awk '{print $1}' | sort | uniq -d)
if [ -n "${DUPES}" ]; then
  echo "WARNING: Duplicate file content detected"
  ISSUES=1
else
  echo "OK: No duplicate file content"
fi

# 3. Check for schema definitions outside schemas/ directory
echo "Checking for inline schema definitions..."
INLINE=$(grep -rl '"$schema"' "${CLAUDE_DIR}" --include="*.json" 2>/dev/null | grep -v '/schemas/' | grep -v '/node_modules/' || true)
if [ -n "${INLINE}" ]; then
  while IFS= read -r f; do
    case "${f}" in
      *REGISTRY.json|*gates.json|*criteria.json|*/state/*) ;;
      *) echo "WARNING: Possible inline schema in ${f}"; ISSUES=1 ;;
    esac
  done <<< "${INLINE}"
fi
echo "OK: No stray schema definitions"

# 4. Check for rules duplicated between CLAUDE.md and agent files
echo "Checking for rule duplication..."
RULE_DUPES=$(grep -l "Never commit secrets\|Never force-push\|Atomic commits\|Conventional commits" "${CLAUDE_DIR}/agents/"*.md 2>/dev/null || true)
if [ -n "${RULE_DUPES}" ]; then
  echo "WARNING: Agent files duplicate CLAUDE.md rules:"
  echo "${RULE_DUPES}"
  ISSUES=1
else
  echo "OK: No rule duplication in agent files"
fi

if [ "${ISSUES}" -eq 0 ]; then
  echo "=== Duplication check passed ==="
else
  echo "=== Duplication issues found ==="
fi
exit "${ISSUES}"
