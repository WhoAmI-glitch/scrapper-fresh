#!/usr/bin/env bash
set -euo pipefail

# check-duplication.sh — Detect duplicate content and logic
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
CLAUDE_DIR="${REPO_ROOT}/.claude"
failed=0

echo "=== Duplication Check ==="

# 1. Check for duplicate agent responsibilities
echo "Checking agent boundary overlaps..."
if [ -d "${CLAUDE_DIR}/agents" ]; then
  # Extract "owns" fields and check for overlaps
  python3 -c "
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
" 2>/dev/null || failed=1
fi

# 2. Check for duplicate files (same content, different paths)
echo "Checking for duplicate file content..."
find "${CLAUDE_DIR}" -name "*.md" -o -name "*.json" | while read -r f; do
  md5sum "${f}" 2>/dev/null || shasum "${f}" 2>/dev/null
done | sort | uniq -d -w 32 | while read -r line; do
  echo "WARNING: Duplicate content found: ${line}"
  failed=1
done

# 3. Check for schema definitions outside schemas/ directory
echo "Checking for inline schema definitions..."
grep -rl '"type".*"object"' "${CLAUDE_DIR}" --include="*.json" 2>/dev/null | while read -r f; do
  case "${f}" in
    */schemas/*) ;; # OK - schemas belong here
    */REGISTRY.json) ;; # OK - has object structure but not a schema
    */gates.json) ;; # OK - config with object structure
    */criteria.json) ;; # OK - config
    *)
      echo "WARNING: Possible inline schema in ${f} — should be in schemas/"
      ;;
  esac
done

# 4. Check for rules duplicated between CLAUDE.md and agent files
echo "Checking for rule duplication..."
if [ -f "${REPO_ROOT}/CLAUDE.md" ]; then
  # Look for agent files that redefine rules from CLAUDE.md
  grep -l "Never commit secrets\|Never force-push\|Atomic commits\|Conventional commits" "${CLAUDE_DIR}/agents/"*.md 2>/dev/null | while read -r f; do
    echo "WARNING: ${f} may duplicate rules from CLAUDE.md"
    failed=1
  done
fi

if [ ${failed} -eq 0 ]; then
  echo "=== Duplication check passed ==="
else
  echo "=== Duplication issues found ==="
fi
exit ${failed}
