#!/usr/bin/env bash
set -euo pipefail

# pre-commit.sh — Pre-commit validation hook
# Consolidates secret scanning and basic checks into ONE hook.
# This is the SINGLE source of truth for pre-commit validation.

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

echo "Running pre-commit checks..."

# ============================================================
# 1. SECRET DETECTION (single source — no duplicate scanners)
# ============================================================
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || true)

if [ -n "${STAGED_FILES}" ]; then
  SECRET_PATTERNS=(
    'AKIA[0-9A-Z]{16}'                          # AWS Access Key
    'sk-[a-zA-Z0-9]{20,}'                       # OpenAI / Anthropic API Key
    'ghp_[a-zA-Z0-9]{36}'                       # GitHub PAT
    'gho_[a-zA-Z0-9]{36}'                       # GitHub OAuth
    'xoxb-[0-9]{10,}-[a-zA-Z0-9]{20,}'         # Slack Bot Token
    'sk_live_[a-zA-Z0-9]{20,}'                  # Stripe Live Key
    'rk_live_[a-zA-Z0-9]{20,}'                  # Stripe Restricted Key
    'SG\.[a-zA-Z0-9_-]{22}\.[a-zA-Z0-9_-]{43}' # SendGrid API Key
    'AC[a-f0-9]{32}'                             # Twilio Account SID
    '-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----' # Private Keys
    'postgres(ql)?://[^:]+:[^@]+@'              # DB connection string with password
    'mongodb(\+srv)?://[^:]+:[^@]+@'            # MongoDB connection string
    'redis://:[^@]+@'                            # Redis with password
  )

  # Files that contain pattern definitions (not actual secrets)
  PATTERN_FILES=(".claude/hooks/pre-commit.sh" "rules/common/security.md")

  FOUND_SECRETS=0
  for pattern in "${SECRET_PATTERNS[@]}"; do
    while IFS= read -r file; do
      if [ -f "${file}" ]; then
        # Skip files that define the patterns themselves
        skip=0
        for pf in "${PATTERN_FILES[@]}"; do
          if [[ "${file}" == *"${pf}" ]]; then skip=1; break; fi
        done
        [[ ${skip} -eq 1 ]] && continue
        if grep -qP "${pattern}" "${file}" 2>/dev/null || grep -qE "${pattern}" "${file}" 2>/dev/null; then
          echo "BLOCKED: Potential secret in ${file} matching pattern: ${pattern:0:20}..."
          FOUND_SECRETS=1
        fi
      fi
    done <<< "${STAGED_FILES}"
  done

  if [ "${FOUND_SECRETS}" -eq 1 ]; then
    echo ""
    echo "COMMIT BLOCKED: Secrets detected in staged files."
    echo "Remove secrets and try again."
    exit 1
  fi
fi

# ============================================================
# 2. PROTECTED PATH CHECK
# ============================================================
PROTECTED_PATHS=(".env" ".env.local" ".env.production" "secrets/" "certs/")
for path in "${PROTECTED_PATHS[@]}"; do
  if echo "${STAGED_FILES}" | grep -q "^${path}"; then
    echo "BLOCKED: Protected path staged for commit: ${path}"
    echo "Remove from staging: git reset HEAD ${path}"
    exit 1
  fi
done

# ============================================================
# 3. JSON VALIDATION (for .claude/ state files)
# ============================================================
json_fail=0
while IFS= read -r f; do
  [ -n "${f}" ] || continue
  if [ -f "${f}" ] && [ -s "${f}" ]; then
    if ! python3 -c "import json; json.load(open('${f}'))" 2>/dev/null; then
      echo "BLOCKED: Invalid JSON: ${f}"
      json_fail=1
    fi
  fi
done <<< "$(echo "${STAGED_FILES}" | grep -E '\.claude/.*\.json$' || true)"

if [ "${json_fail}" -eq 1 ]; then
  exit 1
fi

echo "Pre-commit checks passed."
