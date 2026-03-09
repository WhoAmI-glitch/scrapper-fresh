#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# format-all.sh — Format all code across the monorepo
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo "=== Formatting All Code ==="

cd "${ROOT_DIR}"
pnpm format

echo "=== Format Complete ==="
