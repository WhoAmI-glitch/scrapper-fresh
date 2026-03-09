# Charcoal Shipment Intelligence Platform

A full-stack platform for tracking charcoal cargo shipments from origin to destination. Combines AIS vessel tracking, commercial deal management, risk-zone monitoring, and email intelligence into a single operational dashboard built on a 3D globe visualization. Designed for commodity traders and logistics teams who need real-time visibility over in-transit cargo.

## Architecture

```
Frontend (Next.js 14 + Mapbox GL / Globe)
  |
  |-- REST API + WebSocket (FastAPI)
  |     |-- Services (business logic, ETA calculation, risk scoring)
  |     |-- Integrations (AIS providers, Gmail API)
  |     |-- Background workers (position polling, email sync)
  |     |-- PostgreSQL + PostGIS (spatial queries, voyage tracks)
```

Three layers:
1. **Data layer** -- PostGIS database with spatial indexes for ports, risk zones, and vessel tracks.
2. **API layer** -- FastAPI backend exposing REST endpoints and WebSocket streams for live position updates.
3. **Presentation layer** -- Next.js frontend rendering a Mapbox-powered globe with shipment arcs, risk zones, and a deal management panel.

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Docker & Docker Compose | 20+ | Primary deployment method |
| Node.js | 20+ | Only for local frontend dev |
| Python | 3.11+ | Only for local backend dev |
| Mapbox token | -- | Free tier works for development |
| Gmail API credentials | -- | Optional, for email intelligence |
| MarineTraffic API key | -- | Optional, mock provider available |

## Quick Start

```bash
# 1. Clone and navigate
cd apps/shipment-tracker

# 2. Copy environment file
cp .env.example .env

# 3. Start all services
docker compose up -d

# 4. Open the dashboard
open http://localhost:3001
```

The database auto-initializes with schema and seed data on first run.

## Development Setup (Without Docker)

**Backend:**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e .
uvicorn tracker.main:app --reload --port 8000
```

Requires a local PostgreSQL 14+ instance with PostGIS. Set `DATABASE_URL` in `.env` to point to it.

**Frontend:**

```bash
cd frontend
corepack enable
pnpm install
pnpm dev
```

Runs on http://localhost:3000 by default.

## Makefile Commands

| Command | Description |
|---|---|
| `make up` | Start all services in background |
| `make down` | Stop all services |
| `make logs` | Tail logs from all containers |
| `make db-shell` | Open psql shell in the database |
| `make backend-shell` | Open bash shell in the backend container |
| `make seed` | Re-run seed data against the database |
| `make test` | Run backend tests with pytest |
| `make lint` | Lint backend (ruff) and frontend (eslint) |
| `make dev-backend` | Run backend locally without Docker |
| `make dev-frontend` | Run frontend locally without Docker |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/deals` | List all deals with filters |
| POST | `/api/deals` | Create a new deal |
| GET | `/api/deals/{id}` | Get deal details |
| PATCH | `/api/deals/{id}` | Update deal fields |
| GET | `/api/shipments` | List shipments, optionally by deal |
| POST | `/api/shipments` | Create a shipment under a deal |
| GET | `/api/shipments/{id}` | Get shipment with vessel position |
| GET | `/api/vessels` | List tracked vessels |
| GET | `/api/vessels/{id}/track` | Get voyage track (AIS history) |
| GET | `/api/ports` | List ports |
| GET | `/api/risk-zones` | List active risk zones |
| GET | `/api/alerts` | List alerts, filter by acknowledged |
| PATCH | `/api/alerts/{id}/ack` | Acknowledge an alert |
| GET | `/api/dashboard/metrics` | Aggregated dashboard stats |
| WS | `/ws/live` | Live vessel position stream |

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | (see .env.example) | PostgreSQL connection string |
| `AIS_PROVIDER` | `mock` | AIS data source: `mock` or `marinetraffic` |
| `MARINETRAFFIC_API_KEY` | -- | Required when AIS_PROVIDER=marinetraffic |
| `GMAIL_CREDENTIALS_PATH` | `./credentials.json` | Google OAuth credentials file |
| `GMAIL_TOKEN_PATH` | `./token.json` | Google OAuth token file |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend URL for frontend |
| `NEXT_PUBLIC_WS_URL` | `ws://localhost:8000/ws/live` | WebSocket URL for live updates |
| `NEXT_PUBLIC_MAPBOX_TOKEN` | -- | Mapbox GL JS access token |
| `CORS_ORIGINS` | `http://localhost:3001` | Allowed CORS origins (comma-separated) |

## Project Structure

```
apps/shipment-tracker/
├── docker-compose.yml
├── Makefile
├── .env.example
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── src/tracker/
│       ├── main.py              # FastAPI app entry point
│       ├── config.py            # Settings via pydantic-settings
│       ├── db.py                # Async database pool
│       ├── models/
│       │   ├── schema.sql       # DDL + views
│       │   └── seed.sql         # Sample data
│       ├── schemas/             # Pydantic request/response models
│       ├── routes/              # API route handlers
│       ├── services/            # Business logic
│       ├── integrations/        # AIS, Gmail adapters
│       └── workers/             # Background tasks
└── frontend/
    ├── Dockerfile
    ├── package.json
    └── src/
        ├── app/                 # Next.js app router pages
        ├── components/          # React components
        │   ├── globe/           # 3D globe and map layers
        │   └── panels/          # Side panels, deal forms
        ├── hooks/               # SWR data hooks
        └── lib/                 # API client, types, websocket
```

## Data Model

The database is centered around three core entities:

- **Deals** represent commercial contracts between a buyer and seller for a quantity of charcoal at a given price and Incoterm, routed between a load port and a discharge port.
- **Shipments** represent physical cargo movements under a deal, linked to a vessel, with lifecycle tracking from loading through arrival.
- **Vessels** are tracked via AIS, with current position, speed, heading, and a full history of voyage track points stored as PostGIS geography.

Supporting entities:
- **Ports** with UNLOCODE identifiers and geographic coordinates.
- **Risk Zones** as MultiPolygon geographies with severity levels (piracy, conflict, restricted, insurance).
- **Alerts** triggered by risk-zone entry, route deviation, delays, or inbound emails.
- **Emails** parsed from Gmail and linked to deals/shipments for document intelligence.
- **Attachments** stored as references to files associated with parsed emails.

Two database views provide pre-joined query surfaces: `active_shipments` for the map layer and `dashboard_metrics` for aggregate KPIs.
