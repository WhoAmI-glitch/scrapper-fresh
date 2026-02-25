#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# VPS Deployment Script — Scrapper Lead Generator
# Pulls latest code, builds images, runs migrations, and restarts services.
#
# Usage: ./scripts/vps_deploy.sh
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "=== Scrapper Deployment ==="
echo "Directory: $PROJECT_DIR"
echo "Date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo ""

# Step 1: Pull latest code
echo "[1/5] Pulling latest code..."
git pull --ff-only origin main
echo ""

# Step 2: Build Docker images
echo "[2/5] Building Docker images..."
docker compose build --no-cache
echo ""

# Step 3: Run database migrations
echo "[3/5] Running database migrations..."
docker compose up -d db
echo "  Waiting for database to be ready..."
sleep 5
docker compose run --rm api scrapper init-db
echo ""

# Step 4: Restart services with zero-downtime (recreate only changed)
echo "[4/5] Restarting services..."
docker compose up -d --build --remove-orphans
echo ""

# Step 5: Run smoke test
echo "[5/5] Running smoke test..."
sleep 5
if bash scripts/smoke_test.sh; then
    echo ""
    echo "=== Deployment Complete ==="
else
    echo ""
    echo "=== SMOKE TEST FAILED ==="
    echo "Check logs: docker compose logs --tail=50"
    exit 1
fi

# Print status summary
echo ""
echo "=== Service Status ==="
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "=== Recent Logs ==="
docker compose logs --tail=5 api worker 2>&1 || true
