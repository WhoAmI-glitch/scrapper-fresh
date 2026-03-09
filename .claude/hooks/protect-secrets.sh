#!/usr/bin/env bash
set -euo pipefail

# Protect-secrets hook: scans staged files for potential secrets
# Purpose: Prevent accidental commit of API keys, tokens, and credentials
# Usage: Run as a pre-commit hook or manually before committing

echo "[protect-secrets] Scanning staged files for secrets..."

# Get list of staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || true)

if [[ -z "${STAGED_FILES}" ]]; then
    echo "[protect-secrets] No staged files to check."
    exit 0
fi

FOUND_SECRETS=0

# Patterns to detect common secret formats
declare -a SECRET_PATTERNS=(
    # AWS
    'AKIA[A-Z0-9]{16}'
    'aws_secret_access_key\s*=\s*[A-Za-z0-9/+=]{40}'
    # OpenAI / Anthropic
    'sk-[a-zA-Z0-9]{48,}'
    'sk-ant-[a-zA-Z0-9-]{80,}'
    # GitHub
    'ghp_[a-zA-Z0-9]{36}'
    'gho_[a-zA-Z0-9]{36}'
    'github_pat_[a-zA-Z0-9_]{82}'
    # Generic
    '-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----'
    '-----BEGIN OPENSSH PRIVATE KEY-----'
    # Database URLs with credentials
    'postgres(ql)?://[^:]+:[^@]+@'
    'mysql://[^:]+:[^@]+@'
    'mongodb(\+srv)?://[^:]+:[^@]+@'
    # Generic API key patterns
    'api[_-]?key\s*[:=]\s*["\x27][a-zA-Z0-9_\-]{20,}["\x27]'
    'api[_-]?secret\s*[:=]\s*["\x27][a-zA-Z0-9_\-]{20,}["\x27]'
    'access[_-]?token\s*[:=]\s*["\x27][a-zA-Z0-9_\-]{20,}["\x27]'
    # Telegram
    '[0-9]{8,10}:[a-zA-Z0-9_-]{35}'
    # Stripe
    'sk_live_[a-zA-Z0-9]{24,}'
    'pk_live_[a-zA-Z0-9]{24,}'
    # Twilio
    'SK[a-f0-9]{32}'
    # SendGrid
    'SG\.[a-zA-Z0-9_-]{22}\.[a-zA-Z0-9_-]{43}'
)

# Files to always skip (binary, lockfiles, etc.)
SKIP_PATTERNS="\.lock$|\.png$|\.jpg$|\.jpeg$|\.gif$|\.ico$|\.woff|\.ttf|\.eot|\.svg$|pnpm-lock\.yaml$|package-lock\.json$|yarn\.lock$"

while IFS= read -r file; do
    # Skip binary and lock files
    if echo "${file}" | grep -qE "${SKIP_PATTERNS}"; then
        continue
    fi

    # Skip if file doesn't exist (deleted)
    if [[ ! -f "${file}" ]]; then
        continue
    fi

    for pattern in "${SECRET_PATTERNS[@]}"; do
        MATCHES=$(git diff --cached -- "${file}" | grep -cE "${pattern}" 2>/dev/null || true)
        if [[ "${MATCHES}" -gt 0 ]]; then
            echo "[protect-secrets] ALERT: Potential secret found in '${file}'"
            echo "[protect-secrets]   Pattern: ${pattern}"
            echo "[protect-secrets]   Matches: ${MATCHES}"
            FOUND_SECRETS=$((FOUND_SECRETS + 1))
        fi
    done
done <<< "${STAGED_FILES}"

# Check for protected file paths being staged
PROTECTED_PATHS=(".env" ".env.local" ".env.production" "secrets/" "certs/" ".key" ".pem")
while IFS= read -r file; do
    for protected in "${PROTECTED_PATHS[@]}"; do
        if [[ "${file}" == *"${protected}"* ]] && [[ "${file}" != ".env.example" ]]; then
            echo "[protect-secrets] ALERT: Protected file staged for commit: '${file}'"
            FOUND_SECRETS=$((FOUND_SECRETS + 1))
        fi
    done
done <<< "${STAGED_FILES}"

if [[ "${FOUND_SECRETS}" -gt 0 ]]; then
    echo ""
    echo "[protect-secrets] BLOCKED: ${FOUND_SECRETS} potential secret(s) detected."
    echo "[protect-secrets] Please remove secrets before committing."
    echo "[protect-secrets] If these are false positives, review and use 'git commit --no-verify' (NOT recommended)."
    exit 1
fi

echo "[protect-secrets] No secrets detected. Safe to commit."
exit 0
