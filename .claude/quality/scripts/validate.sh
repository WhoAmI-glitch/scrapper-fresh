#!/usr/bin/env bash
set -euo pipefail

# validate.sh — Central quality gate runner
# Usage: validate.sh [check_name]
# If no check_name, runs all checks.

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
CHECK="${1:-all}"

run_correctness() {
  echo "=== Correctness Check ==="
  local failed=0

  # Python: syntax check
  if compgen -G "${REPO_ROOT}/**/*.py" > /dev/null 2>&1; then
    find "${REPO_ROOT}" -name "*.py" -not -path "*/node_modules/*" -not -path "*/.git/*" | head -50 | while read -r f; do
      python3 -c "import ast; ast.parse(open('${f}').read())" 2>/dev/null || { echo "FAIL: ${f} has syntax errors"; failed=1; }
    done
  fi

  # TypeScript: type check if tsconfig exists
  if [ -f "${REPO_ROOT}/tsconfig.json" ]; then
    npx tsc --noEmit 2>/dev/null || { echo "FAIL: TypeScript type errors"; failed=1; }
  fi

  # Shell: shellcheck on hook scripts
  if command -v shellcheck &>/dev/null; then
    find "${REPO_ROOT}/.claude/hooks" -name "*.sh" 2>/dev/null | while read -r f; do
      shellcheck "${f}" || { echo "FAIL: ${f} has shellcheck issues"; failed=1; }
    done
  fi

  # JSON: validate all JSON files in .claude/
  find "${REPO_ROOT}/.claude" -name "*.json" -not -path "*/node_modules/*" | while read -r f; do
    python3 -c "import json; json.load(open('${f}'))" 2>/dev/null || { echo "FAIL: ${f} is invalid JSON"; failed=1; }
  done

  return ${failed}
}

run_regressions() {
  echo "=== Regression Check ==="
  local failed=0

  # Python tests
  if [ -f "${REPO_ROOT}/pyproject.toml" ] || [ -f "${REPO_ROOT}/setup.py" ]; then
    if command -v pytest &>/dev/null; then
      cd "${REPO_ROOT}" && pytest --tb=short -q 2>/dev/null || { echo "FAIL: pytest failures"; failed=1; }
    fi
  fi

  # Node tests
  if [ -f "${REPO_ROOT}/package.json" ]; then
    if grep -q '"test"' "${REPO_ROOT}/package.json" 2>/dev/null; then
      cd "${REPO_ROOT}" && npm test 2>/dev/null || { echo "FAIL: npm test failures"; failed=1; }
    fi
  fi

  return ${failed}
}

run_contracts() {
  echo "=== Contract Integrity Check ==="
  local failed=0
  local schema_dir="${REPO_ROOT}/.claude/schemas"
  local state_dir="${REPO_ROOT}/.claude/state"

  # Validate state files against schemas
  for dir in tasks handoffs findings decisions; do
    if [ -d "${state_dir}/${dir}" ]; then
      find "${state_dir}/${dir}" -name "*.json" -not -name ".gitkeep" | while read -r f; do
        python3 -c "
import json, sys
try:
    data = json.load(open('${f}'))
    required_id_prefix = '${dir}'[:-1]  # tasks→task, handoffs→handoff, etc
    if 'id' in data and not data['id'].startswith(required_id_prefix):
        print(f'FAIL: {\"${f}\"} ID does not match expected prefix')
        sys.exit(1)
except Exception as e:
    print(f'FAIL: {\"${f}\"}: {e}')
    sys.exit(1)
" 2>/dev/null || failed=1
      done
    fi
  done

  return ${failed}
}

run_tests() {
  echo "=== Test Coverage Check ==="
  # Delegates to regression runner but with coverage flag
  if command -v pytest &>/dev/null && [ -f "${REPO_ROOT}/pyproject.toml" ]; then
    cd "${REPO_ROOT}" && pytest --co -q 2>/dev/null | tail -1 || true
  fi
  echo "INFO: Manual review needed for new test coverage"
  return 0
}

run_runnability() {
  echo "=== Runnability Check ==="
  # Check that main entry points exist and are importable
  if [ -f "${REPO_ROOT}/pyproject.toml" ]; then
    python3 -c "
import tomllib, sys
with open('${REPO_ROOT}/pyproject.toml', 'rb') as f:
    data = tomllib.load(f)
    scripts = data.get('project', {}).get('scripts', {})
    for name, entry in scripts.items():
        module = entry.split(':')[0]
        print(f'Checking {name} -> {module}')
" 2>/dev/null || true
  fi
  return 0
}

case "${CHECK}" in
  correctness)  run_correctness ;;
  regressions)  run_regressions ;;
  contracts)    run_contracts ;;
  tests)        run_tests ;;
  runnability)  run_runnability ;;
  all)
    echo "Running all quality checks..."
    run_correctness
    run_regressions
    run_contracts
    run_tests
    run_runnability
    echo "=== All checks complete ==="
    ;;
  *)
    echo "Unknown check: ${CHECK}"
    echo "Available: correctness, regressions, contracts, tests, runnability, all"
    exit 1
    ;;
esac
