#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# bootstrap.sh — First-time workspace setup
# =============================================================================
# Installs all dependencies, sets up databases, and validates the environment.
# Run once after cloning the repo or entering the devcontainer.
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

echo "=== Claude Autonomous Workspace — Bootstrap ==="
echo "Root: ${ROOT_DIR}"
echo ""

# --- 1. Check prerequisites ---
echo "[1/6] Checking prerequisites..."

command -v node >/dev/null 2>&1 || { echo "ERROR: node is required but not installed."; exit 1; }
command -v pnpm >/dev/null 2>&1 || { echo "ERROR: pnpm is required but not installed."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "WARNING: python3 not found — backend setup will be skipped."; }

echo "  node:   $(node --version)"
echo "  pnpm:   $(pnpm --version)"
if command -v python3 >/dev/null 2>&1; then
  echo "  python: $(python3 --version)"
fi
echo ""

# --- 2. Install Node dependencies ---
echo "[2/6] Installing Node dependencies..."
cd "${ROOT_DIR}"
pnpm install --frozen-lockfile 2>/dev/null || pnpm install
echo ""

# --- 3. Set up Python virtual environment (if backend exists) ---
echo "[3/6] Setting up Python environment..."
if [ -f "${ROOT_DIR}/apps/api/pyproject.toml" ]; then
  cd "${ROOT_DIR}/apps/api"
  if command -v uv >/dev/null 2>&1; then
    uv venv .venv
    uv pip install -e ".[dev]"
  else
    python3 -m venv .venv
    .venv/bin/pip install -e ".[dev]"
  fi
  echo "  Python venv created at apps/api/.venv"
else
  echo "  No apps/api/pyproject.toml found — skipping Python setup."
fi
echo ""

# --- 4. Copy environment file ---
echo "[4/6] Checking environment file..."
cd "${ROOT_DIR}"
if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    cp .env.example .env
    echo "  Copied .env.example -> .env (fill in your values)"
  else
    echo "  WARNING: No .env.example found."
  fi
else
  echo "  .env already exists — skipping."
fi
echo ""

# --- 5. Create data directories ---
echo "[5/6] Ensuring data directories exist..."
mkdir -p "${ROOT_DIR}/data/seeds"
mkdir -p "${ROOT_DIR}/data/snapshots"
mkdir -p "${ROOT_DIR}/data/exports"
echo "  data/seeds, data/snapshots, data/exports — OK"
echo ""

# --- 6. Validate ---
echo "[6/6] Validating workspace..."
if [ -f "${ROOT_DIR}/package.json" ]; then
  echo "  package.json       — OK"
fi
if [ -f "${ROOT_DIR}/pnpm-workspace.yaml" ]; then
  echo "  pnpm-workspace.yaml — OK"
fi
if [ -f "${ROOT_DIR}/turbo.json" ]; then
  echo "  turbo.json          — OK"
fi
echo ""

echo "=== Bootstrap complete ==="
echo "Next steps:"
echo "  1. Fill in .env with your API keys and secrets"
echo "  2. Run 'pnpm dev:up' to start infrastructure (Postgres, Redis)"
echo "  3. Run 'pnpm dev' to start development servers"
