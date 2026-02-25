#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Smoke Test — Verify deployment health
#
# Usage: ./scripts/smoke_test.sh
# =============================================================================

BASE_URL="${BASE_URL:-http://localhost:8000}"
PASS=0
FAIL=0

check() {
    local name="$1"
    local result="$2"
    if [ "$result" = "ok" ]; then
        echo "  [PASS] $name"
        PASS=$((PASS + 1))
    else
        echo "  [FAIL] $name — $result"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== Smoke Test ==="
echo "Target: $BASE_URL"
echo ""

# Test 1: Health endpoint (basic HTTP connectivity)
echo "Testing HTTP connectivity..."
HTTP_CODE=$(curl -sf -o /dev/null -w '%{http_code}' "$BASE_URL/" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    check "HTTP connectivity" "ok"
else
    check "HTTP connectivity" "got HTTP $HTTP_CODE"
fi

# Test 2: Database connectivity via CLI
echo "Testing database connectivity..."
DB_CHECK=$(docker compose exec -T api scrapper healthcheck 2>&1 || echo "FAILED")
if echo "$DB_CHECK" | grep -q "OK"; then
    check "Database connectivity" "ok"
else
    check "Database connectivity" "$DB_CHECK"
fi

# Test 3: Pipeline stats via CLI
echo "Testing pipeline stats..."
STATS=$(docker compose exec -T api scrapper stats 2>&1 || echo "FAILED")
if echo "$STATS" | grep -q "Candidates"; then
    check "Pipeline stats" "ok"
else
    check "Pipeline stats" "$STATS"
fi

# Test 4: Worker container is running
echo "Testing worker status..."
WORKER_STATUS=$(docker compose ps worker --format '{{.Status}}' 2>/dev/null || echo "not found")
if echo "$WORKER_STATUS" | grep -qi "up"; then
    check "Worker running" "ok"
else
    check "Worker running" "$WORKER_STATUS"
fi

# Summary
echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
