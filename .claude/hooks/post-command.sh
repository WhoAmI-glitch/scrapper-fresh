#!/usr/bin/env bash
set -euo pipefail

# Post-command hook: runs after every Claude command execution
# Purpose: Validation, cleanup, and status reporting

WORKSPACE_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

echo "[post-command] Running post-command checks..."

# Check for any unstaged changes that might have been missed
UNSTAGED=$(git diff --name-only 2>/dev/null || true)
if [[ -n "${UNSTAGED}" ]]; then
    echo "[post-command] Unstaged changes detected:"
    echo "${UNSTAGED}" | head -20
    UNSTAGED_COUNT=$(echo "${UNSTAGED}" | wc -l | tr -d ' ')
    if [[ "${UNSTAGED_COUNT}" -gt 20 ]]; then
        echo "[post-command] ... and $((UNSTAGED_COUNT - 20)) more files."
    fi
fi

# Check for untracked files
UNTRACKED=$(git ls-files --others --exclude-standard 2>/dev/null || true)
if [[ -n "${UNTRACKED}" ]]; then
    UNTRACKED_COUNT=$(echo "${UNTRACKED}" | wc -l | tr -d ' ')
    echo "[post-command] ${UNTRACKED_COUNT} untracked file(s) detected."
fi

# Log command completion
LOG_DIR="${WORKSPACE_ROOT}/.claude/task-logs"
if [[ -d "${LOG_DIR}" ]]; then
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "${TIMESTAMP} | post-command | completed" >> "${LOG_DIR}/activity.log" 2>/dev/null || true
fi

# Check if node_modules or venv is bloated
if [[ -d "${WORKSPACE_ROOT}/node_modules" ]]; then
    NODE_SIZE=$(du -sm "${WORKSPACE_ROOT}/node_modules" 2>/dev/null | cut -f1 || echo "0")
    if [[ "${NODE_SIZE}" -gt 1000 ]]; then
        echo "[post-command] WARNING: node_modules is ${NODE_SIZE}MB. Consider pruning unused dependencies."
    fi
fi

# Verify .gitignore covers common patterns
if [[ -f "${WORKSPACE_ROOT}/.gitignore" ]]; then
    REQUIRED_PATTERNS=("node_modules" ".env" ".env.local" "__pycache__" ".next" "dist")
    for pattern in "${REQUIRED_PATTERNS[@]}"; do
        if ! grep -q "^${pattern}" "${WORKSPACE_ROOT}/.gitignore" 2>/dev/null; then
            echo "[post-command] NOTE: '${pattern}' not found in .gitignore"
        fi
    done
fi

echo "[post-command] Checks complete."
