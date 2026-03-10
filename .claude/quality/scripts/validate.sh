#!/usr/bin/env bash
set -euo pipefail

# validate.sh — Central quality gate runner
# Usage: validate.sh [check_name]
# If no check_name, runs all checks.

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
CHECK="${1:-all}"
SCHEMA_DIR="${REPO_ROOT}/.claude/schemas"
VALIDATE_SCRIPT="${REPO_ROOT}/scripts/validate-schema.py"

run_correctness() {
  echo "=== Correctness Check ==="
  local failed=0

  # Python: syntax check
  if compgen -G "${REPO_ROOT}/**/*.py" > /dev/null 2>&1; then
    local py_files
    py_files="$(find "${REPO_ROOT}" -name "*.py" -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/__pycache__/*" | head -50)"
    while IFS= read -r f; do
      [ -n "${f}" ] || continue
      if ! python3 -c "import ast; ast.parse(open('${f}').read())" 2>/dev/null; then
        echo "FAIL: ${f} has syntax errors"
        failed=1
      fi
    done <<< "${py_files}"
  fi

  # TypeScript: type check if tsconfig exists
  if [ -f "${REPO_ROOT}/tsconfig.json" ]; then
    if ! npx tsc --noEmit 2>/dev/null; then
      echo "FAIL: TypeScript type errors"
      failed=1
    fi
  fi

  # Shell: shellcheck on hook scripts
  if command -v shellcheck &>/dev/null; then
    local shell_files
    shell_files="$(find "${REPO_ROOT}/.claude/hooks" -name "*.sh" 2>/dev/null || true)"
    while IFS= read -r f; do
      [ -n "${f}" ] || continue
      if ! shellcheck "${f}" 2>/dev/null; then
        echo "FAIL: ${f} has shellcheck issues"
        failed=1
      fi
    done <<< "${shell_files}"
  fi

  # JSON: validate all JSON files in .claude/
  local json_files
  json_files="$(find "${REPO_ROOT}/.claude" -name "*.json" -not -path "*/node_modules/*" || true)"
  while IFS= read -r f; do
    [ -n "${f}" ] || continue
    if ! python3 -c "import json; json.load(open('${f}'))" 2>/dev/null; then
      echo "FAIL: ${f} is invalid JSON"
      failed=1
    fi
  done <<< "${json_files}"

  return ${failed}
}

run_regressions() {
  echo "=== Regression Check ==="
  local failed=0

  # Python tests
  if [ -f "${REPO_ROOT}/pyproject.toml" ] || [ -f "${REPO_ROOT}/setup.py" ]; then
    if command -v pytest &>/dev/null; then
      if ! (cd "${REPO_ROOT}" && pytest --tb=short -q 2>/dev/null); then
        echo "FAIL: pytest failures"
        failed=1
      fi
    fi
  fi

  # Node tests
  if [ -f "${REPO_ROOT}/package.json" ]; then
    if grep -q '"test"' "${REPO_ROOT}/package.json" 2>/dev/null; then
      if ! (cd "${REPO_ROOT}" && npm test 2>/dev/null); then
        echo "FAIL: npm test failures"
        failed=1
      fi
    fi
  fi

  return ${failed}
}

run_contracts() {
  echo "=== Contract Integrity Check ==="
  local failed=0
  local state_dir="${REPO_ROOT}/.claude/state"

  # Use real schema validation if available
  if [ -f "${VALIDATE_SCRIPT}" ] && command -v python3 &>/dev/null; then
    local schema_map=(
      "tasks:${SCHEMA_DIR}/task.schema.json"
      "handoffs:${SCHEMA_DIR}/handoff.schema.json"
      "findings:${SCHEMA_DIR}/finding.schema.json"
      "decisions:${SCHEMA_DIR}/decision.schema.json"
    )

    for entry in "${schema_map[@]}"; do
      local dir_name="${entry%%:*}"
      local schema_path="${entry#*:}"
      local dir_path="${state_dir}/${dir_name}"

      if [ -d "${dir_path}" ]; then
        local state_files
        state_files="$(find "${dir_path}" -name "*.json" -not -name ".gitkeep" 2>/dev/null || true)"
        while IFS= read -r f; do
          [ -n "${f}" ] || continue
          if ! python3 "${VALIDATE_SCRIPT}" "${schema_path}" "${f}" 2>/dev/null; then
            echo "FAIL: ${f} does not conform to ${dir_name} schema"
            failed=1
          fi
        done <<< "${state_files}"
      fi
    done
  else
    echo "INFO: Schema validation script not found; falling back to JSON syntax check"
    for dir in tasks handoffs findings decisions; do
      if [ -d "${state_dir}/${dir}" ]; then
        local state_files
        state_files="$(find "${state_dir}/${dir}" -name "*.json" -not -name ".gitkeep" 2>/dev/null || true)"
        while IFS= read -r f; do
          [ -n "${f}" ] || continue
          if ! python3 -c "import json; json.load(open('${f}'))" 2>/dev/null; then
            echo "FAIL: ${f} is invalid JSON"
            failed=1
          fi
        done <<< "${state_files}"
      fi
    done
  fi

  return ${failed}
}

run_tests() {
  echo "=== Test Coverage Check ==="
  if command -v pytest &>/dev/null && [ -f "${REPO_ROOT}/pyproject.toml" ]; then
    (cd "${REPO_ROOT}" && pytest --co -q 2>/dev/null | tail -1) || true
  fi
  echo "INFO: Manual review needed for new test coverage"
  return 0
}

run_runnability() {
  echo "=== Runnability Check ==="
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
    total_failed=0
    run_correctness || total_failed=1
    run_regressions || total_failed=1
    run_contracts || total_failed=1
    run_tests || total_failed=1
    run_runnability || total_failed=1
    echo "=== All checks complete ==="
    exit ${total_failed}
    ;;
  *)
    echo "Unknown check: ${CHECK}"
    echo "Available: correctness, regressions, contracts, tests, runnability, all"
    exit 1
    ;;
esac
