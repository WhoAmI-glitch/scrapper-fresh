#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# dev-up.sh — Start development infrastructure
# =============================================================================
# Brings up PostgreSQL and Redis via Docker Compose for local development.
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/infra/docker/docker-compose.yml"

echo "=== Starting Development Infrastructure ==="

# Check Docker is running
if ! docker info >/dev/null 2>&1; then
  echo "ERROR: Docker is not running. Please start Docker Desktop or the Docker daemon."
  exit 1
fi

# Start only infrastructure services (postgres + redis)
echo "[1/3] Starting PostgreSQL and Redis..."
docker compose -f "${COMPOSE_FILE}" up -d postgres redis

# Wait for PostgreSQL to be ready
echo "[2/3] Waiting for PostgreSQL to be ready..."
RETRIES=30
until docker compose -f "${COMPOSE_FILE}" exec -T postgres pg_isready -U postgres >/dev/null 2>&1 || [ "${RETRIES}" -eq 0 ]; do
  RETRIES=$((RETRIES - 1))
  echo "  Waiting for PostgreSQL... (${RETRIES} retries left)"
  sleep 1
done

if [ "${RETRIES}" -eq 0 ]; then
  echo "ERROR: PostgreSQL did not become ready in time."
  exit 1
fi

echo "  PostgreSQL is ready."

# Wait for Redis to be ready
echo "[3/3] Waiting for Redis to be ready..."
RETRIES=15
until docker compose -f "${COMPOSE_FILE}" exec -T redis redis-cli ping 2>/dev/null | grep -q PONG || [ "${RETRIES}" -eq 0 ]; do
  RETRIES=$((RETRIES - 1))
  echo "  Waiting for Redis... (${RETRIES} retries left)"
  sleep 1
done

if [ "${RETRIES}" -eq 0 ]; then
  echo "ERROR: Redis did not become ready in time."
  exit 1
fi

echo "  Redis is ready."
echo ""
echo "=== Infrastructure Running ==="
echo "  PostgreSQL: localhost:5432 (user: postgres, db: claude_workspace)"
echo "  Redis:      localhost:6379"
echo ""
echo "To stop: docker compose -f ${COMPOSE_FILE} down"
