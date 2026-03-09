#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# test-all.sh — Run all tests across the monorepo
# =============================================================================
# Runs TypeScript/JavaScript tests via Turbo, then Python tests via pytest.
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo "=== Running All Tests ==="
echo ""

EXIT_CODE=0

# --- 1. TypeScript / JavaScript tests (Turbo) ---
echo "[1/2] Running TypeScript/JavaScript tests..."
cd "${ROOT_DIR}"
if pnpm turbo run test --no-daemon 2>/dev/null; then
  echo "  TS/JS tests: PASSED"
else
  echo "  TS/JS tests: FAILED"
  EXIT_CODE=1
fi
echo ""

# --- 2. Python tests (pytest) ---
echo "[2/2] Running Python tests..."
if [ -d "${ROOT_DIR}/apps/api" ] && [ -f "${ROOT_DIR}/apps/api/pyproject.toml" ]; then
  cd "${ROOT_DIR}/apps/api"
  if [ -d ".venv" ]; then
    .venv/bin/python -m pytest tests/ -v --tb=short 2>/dev/null || {
      echo "  Python tests: FAILED"
      EXIT_CODE=1
    }
  else
    echo "  WARNING: No .venv found in apps/api — run bootstrap.sh first."
  fi
else
  echo "  No Python project found — skipping."
fi
echo ""

# --- Summary ---
if [ "${EXIT_CODE}" -eq 0 ]; then
  echo "=== All Tests Passed ==="
else
  echo "=== Some Tests Failed ==="
  exit "${EXIT_CODE}"
fi
