.PHONY: up down logs db-shell backend-shell seed test lint

# Start all services
up:
	docker compose up -d

# Stop all services
down:
	docker compose down

# View logs
logs:
	docker compose logs -f

# Database shell
db-shell:
	docker compose exec db psql -U tracker -d shipment_tracker

# Backend shell
backend-shell:
	docker compose exec backend bash

# Reseed database
seed:
	docker compose exec db psql -U tracker -d shipment_tracker -f /docker-entrypoint-initdb.d/02-seed.sql

# Run backend tests
test:
	cd backend && python -m pytest tests/ -v

# Lint
lint:
	cd backend && ruff check src/
	cd frontend && pnpm lint

# Dev without Docker (requires local PostgreSQL + PostGIS)
dev-backend:
	cd backend && uvicorn tracker.main:app --reload --port 8000

dev-frontend:
	cd frontend && pnpm dev
