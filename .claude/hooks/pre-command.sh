#!/usr/bin/env bash
set -euo pipefail

# Pre-command hook: runs before every Claude command execution
# Purpose: Environment validation and safety checks

WORKSPACE_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

echo "[pre-command] Workspace: ${WORKSPACE_ROOT}"

# Check for uncommitted changes in protected paths
PROTECTED_PATHS=(".env" ".env.local" ".env.production" "secrets/" "certs/")
for path in "${PROTECTED_PATHS[@]}"; do
    if [[ -e "${WORKSPACE_ROOT}/${path}" ]]; then
        if git diff --name-only 2>/dev/null | grep -q "^${path}"; then
            echo "[pre-command] WARNING: Uncommitted changes in protected path: ${path}"
            echo "[pre-command] These files will NOT be auto-committed."
        fi
    fi
done

# Verify we are not on a protected branch for write operations
CURRENT_BRANCH="$(git branch --show-current 2>/dev/null || echo 'unknown')"
PROTECTED_BRANCHES=("main" "production" "master")
for branch in "${PROTECTED_BRANCHES[@]}"; do
    if [[ "${CURRENT_BRANCH}" == "${branch}" ]]; then
        echo "[pre-command] WARNING: Currently on protected branch '${branch}'."
        echo "[pre-command] Consider creating a feature branch before making changes."
    fi
done

# Check disk space (warn if less than 1GB free)
AVAILABLE_KB=$(df -k "${WORKSPACE_ROOT}" | tail -1 | awk '{print $4}')
if [[ "${AVAILABLE_KB}" -lt 1048576 ]]; then
    echo "[pre-command] WARNING: Low disk space ($(( AVAILABLE_KB / 1024 ))MB free)."
fi

# Verify Node.js and Python are available
if command -v node &>/dev/null; then
    echo "[pre-command] Node.js: $(node --version)"
else
    echo "[pre-command] WARNING: Node.js not found in PATH."
fi

if command -v python3 &>/dev/null; then
    echo "[pre-command] Python: $(python3 --version 2>&1)"
else
    echo "[pre-command] WARNING: Python 3 not found in PATH."
fi

echo "[pre-command] Checks complete."
