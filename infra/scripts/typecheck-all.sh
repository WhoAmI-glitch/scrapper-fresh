#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# typecheck-all.sh — Run type checking across the monorepo
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo "=== Running Type Checks ==="

cd "${ROOT_DIR}"
pnpm turbo run typecheck --no-daemon

echo "=== Type Check Complete ==="
