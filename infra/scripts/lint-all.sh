#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# lint-all.sh — Run all linters across the monorepo
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo "=== Running All Linters ==="

cd "${ROOT_DIR}"
pnpm turbo run lint --no-daemon

echo "=== Lint Complete ==="
