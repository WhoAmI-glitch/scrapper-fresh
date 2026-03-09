#!/usr/bin/env bash
set -euo pipefail

# Post-edit hook: runs after Claude edits a file
# Purpose: Auto-format and validate edited files

FILE_PATH="${1:-}"

if [[ -z "${FILE_PATH}" ]]; then
    echo "[post-edit] No file path provided, skipping."
    exit 0
fi

echo "[post-edit] Processing: ${FILE_PATH}"

# Determine file type and apply appropriate formatting
case "${FILE_PATH}" in
    *.ts|*.tsx|*.js|*.jsx)
        # Format with Prettier if available
        if command -v npx &>/dev/null && [[ -f "node_modules/.bin/prettier" ]]; then
            echo "[post-edit] Formatting with Prettier..."
            npx prettier --write "${FILE_PATH}" 2>/dev/null || true
        fi
        # Lint with ESLint if available
        if command -v npx &>/dev/null && [[ -f "node_modules/.bin/eslint" ]]; then
            echo "[post-edit] Linting with ESLint..."
            npx eslint --fix "${FILE_PATH}" 2>/dev/null || true
        fi
        ;;
    *.py)
        # Format with ruff if available
        if command -v ruff &>/dev/null; then
            echo "[post-edit] Formatting with ruff..."
            ruff format "${FILE_PATH}" 2>/dev/null || true
            ruff check --fix "${FILE_PATH}" 2>/dev/null || true
        fi
        ;;
    *.json)
        # Validate JSON
        if command -v python3 &>/dev/null; then
            if ! python3 -m json.tool "${FILE_PATH}" >/dev/null 2>&1; then
                echo "[post-edit] WARNING: Invalid JSON in ${FILE_PATH}"
            fi
        fi
        ;;
    *.yaml|*.yml)
        # Validate YAML if yq is available
        if command -v yq &>/dev/null; then
            if ! yq eval '.' "${FILE_PATH}" >/dev/null 2>&1; then
                echo "[post-edit] WARNING: Invalid YAML in ${FILE_PATH}"
            fi
        fi
        ;;
    *.sh)
        # Check with shellcheck if available
        if command -v shellcheck &>/dev/null; then
            echo "[post-edit] Checking with shellcheck..."
            shellcheck "${FILE_PATH}" 2>/dev/null || true
        fi
        ;;
    *.md)
        # Lint markdown if markdownlint is available
        if command -v npx &>/dev/null && [[ -f "node_modules/.bin/markdownlint" ]]; then
            echo "[post-edit] Linting markdown..."
            npx markdownlint --fix "${FILE_PATH}" 2>/dev/null || true
        fi
        ;;
esac

# Check for accidentally committed secrets
if grep -qE '(AKIA[A-Z0-9]{16}|sk-[a-zA-Z0-9]{48}|ghp_[a-zA-Z0-9]{36}|-----BEGIN (RSA |EC )?PRIVATE KEY-----)' "${FILE_PATH}" 2>/dev/null; then
    echo "[post-edit] CRITICAL: Potential secret detected in ${FILE_PATH}!"
    echo "[post-edit] Please remove the secret before committing."
    exit 1
fi

echo "[post-edit] Done: ${FILE_PATH}"
