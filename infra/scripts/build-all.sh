#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# build-all.sh — Build all packages and applications
# =============================================================================
# Runs the Turbo build pipeline, then builds Docker images for deployment.
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/infra/docker/docker-compose.yml"

echo "=== Building All Packages ==="
echo ""

# --- 1. TypeScript / JavaScript build (Turbo) ---
echo "[1/2] Building TypeScript/JavaScript packages..."
cd "${ROOT_DIR}"
pnpm turbo run build --no-daemon
echo "  TS/JS build: DONE"
echo ""

# --- 2. Docker images ---
echo "[2/2] Building Docker images..."
if [ -f "${COMPOSE_FILE}" ]; then
  docker compose -f "${COMPOSE_FILE}" build
  echo "  Docker build: DONE"
else
  echo "  No docker-compose.yml found — skipping Docker build."
fi
echo ""

echo "=== Build Complete ==="
