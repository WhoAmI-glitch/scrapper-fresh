# Scrapper Architecture: Complete System Overview

**Last Updated:** 2024-02-13
**Version:** 1.0.0

This document provides a comprehensive view of how all components interact, what triggers what, and how data flows through the system.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [Data Flow Diagrams](#data-flow-diagrams)
4. [File Dependencies](#file-dependencies)
5. [Configuration Propagation](#configuration-propagation)
6. [Event Flow](#event-flow)
7. [Deployment Flow](#deployment-flow)

---

## System Overview

### The Big Picture

```
┌──────────────────────────────────────────────────────────────────┐
│                         INTERNET / CLIENT                         │
└────────────────────────────┬─────────────────────────────────────┘
                             │ HTTPS (443)
                             ↓
┌──────────────────────────────────────────────────────────────────┐
│  CADDY REVERSE PROXY (Container 1)                               │
│  - Automatic HTTPS via Let's Encrypt                             │
│  - Terminates SSL                                                │
│  - Forwards to API:8000                                          │
└────────────────────────────┬─────────────────────────────────────┘
                             │ HTTP (internal)
                             ↓
┌──────────────────────────────────────────────────────────────────┐
│  FASTAPI WEB API (Container 2)                                   │
│  - HTTP Basic Auth                                               │
│  - REST endpoints: /discover, /enrich, /stats, /export          │
│  - Database queries via connection pool                          │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ↓
┌──────────────────────────────────────────────────────────────────┐
│  POSTGRESQL DATABASE (Container 3)                               │
│  - Tables: candidates, enrichment_tasks, leads, raw_pages        │
│  - Row-level locking for task queue                             │
│  - Persistent storage via Docker volume                          │
└────────────────────────────┬─────────────────────────────────────┘
                             ↑
                             │ Polls queue every 5s
                             │
┌──────────────────────────────────────────────────────────────────┐
│  BACKGROUND WORKER (Container 4)                                 │
│  - Claims tasks from queue (SELECT FOR UPDATE SKIP LOCKED)       │
│  - Resolves → Fetches → Parses → Saves leads                   │
│  - Saves raw HTML snapshots to filesystem                        │
└──────────────────────────────────────────────────────────────────┘
```

### Shared Resources

```
Docker Volumes:
- postgres_data: Database persistence
- caddy_data: SSL certificates
- caddy_config: Caddy configuration

Shared Filesystem (bind mounts):
- ./data/raw: Raw HTML snapshots (all containers)
- ./data/exports: CSV exports (API only)
```

---

## Component Architecture

### 1. **Configuration Layer**

**File:** `src/scrapper/config.py`
**What it does:** Single source of truth for all configuration
**Triggers:**
- Read at startup by ALL containers
- Environment variables from `.env` file
- Validates configuration via Pydantic

**Propagation Flow:**
```
.env file (host)
    ↓ (docker-compose.yml loads)
Container Environment Variables
    ↓ (config.py reads)
Config Object (singleton)
    ↓ (imported by all modules)
All Application Components
```

**Key Dependencies:**
- `.env` → Environment variables
- `pyproject.toml` → Package metadata
- `pydantic-settings` → Type-safe config loading

---

### 2. **Database Layer**

**Files:**
- `src/scrapper/db/schema.sql` → Database schema definition
- `src/scrapper/db/connection.py` → Connection pool management
- `src/scrapper/db/models.py` → Data models (Pydantic)
- `src/scrapper/db/queue.py` → Task queue operations

**What happens:**

```
Container Start
    ↓
docker-compose.yml mounts schema.sql to /docker-entrypoint-initdb.d/
    ↓
PostgreSQL executes schema.sql (ONLY on first run)
    ↓
Tables created: candidates, enrichment_tasks, leads, raw_pages
    ↓
API/Worker containers connect via psycopg3 connection pool
    ↓
Connection pool initialized: min=2, max=10 connections
```

**Database Operations:**

| Operation | File | Function | When |
|-----------|------|----------|------|
| Create candidate | `discovery/sources/*.py` | `FakeSource.run()` | User triggers `/runs/discover` |
| Create task | `db/queue.py` | `TaskQueue.create_task()` | After candidate created |
| Claim task | `db/queue.py` | `TaskQueue.claim_next_task()` | Worker polls queue |
| Save lead | `pipeline/worker.py` | `_save_lead()` | After parsing completes |
| Export leads | `export/exporter.py` | `LeadExporter.export_to_csv()` | User requests `/export` |

---

### 3. **Web API Layer**

**File:** `src/scrapper/web/app.py`
**Container:** `scrapper-api`
**Command:** `uvicorn scrapper.web.app:app --host 0.0.0.0 --port 8000`

**Startup Sequence:**
```
1. docker-compose up -d
2. Dockerfile builds image (Python 3.11 + dependencies)
3. Container starts with uvicorn command
4. app.py startup event triggered
   ↓
5. setup_logging() - configures logging
6. get_pool() - initializes DB connection pool
7. FastAPI routes registered
8. Health check starts (every 30s)
   ↓
9. API ready to serve requests
```

**Endpoint Flow Examples:**

#### **POST /runs/discover**
```
User → curl -X POST /runs/discover -d '{"source":"fake","create_tasks":true}'
    ↓
1. Caddy receives HTTPS request on :443
2. Caddy forwards to api:8000
3. FastAPI receives request
4. verify_credentials() checks HTTP Basic Auth
    ↓ (if auth fails → 401 Unauthorized)
5. FakeSource().run(create_tasks=True)
    ↓
6. Insert 8 candidates into candidates table
7. For each candidate: TaskQueue.create_task()
    ↓
8. Insert 8 tasks into enrichment_tasks table (state=NEW)
9. Return: {candidates_discovered: 8, tasks_created: 8}
```

#### **GET /export**
```
User → curl /export
    ↓
1. verify_credentials() checks auth
2. LeadExporter.get_export_stats() → count leads
    ↓ (if 0 leads → 404 Not Found)
3. LeadExporter.export_to_csv()
    ↓
4. Query: SELECT * FROM leads
5. Write to temp CSV file in data/exports/
6. Return FileResponse with CSV
```

---

### 4. **Background Worker Layer**

**File:** `src/scrapper/pipeline/worker.py`
**Container:** `scrapper-worker`
**Command:** `scrapper-worker` (defined in `cli.py`)

**Worker Loop:**
```
Worker starts
    ↓
1. Register SIGTERM/SIGINT handlers (graceful shutdown)
2. Load config: poll_interval=5s, batch_size=10
3. Enter infinite loop:
    ↓
while not shutdown_requested:
    ┌─────────────────────────────────────┐
    │ 4. TaskQueue.claim_batch(10)        │
    │    ↓                                 │
    │    SELECT id FROM enrichment_tasks  │
    │    WHERE state = 'NEW'              │
    │    ORDER BY priority DESC           │
    │    LIMIT 10                         │
    │    FOR UPDATE SKIP LOCKED           │
    │    ↓                                 │
    │    UPDATE state = 'FETCHING'        │
    └─────────────────────────────────────┘
    ↓
5. If no tasks: sleep(5 seconds), continue
    ↓
6. For each claimed task:
    ├─ Get candidate: SELECT * FROM candidates WHERE id = ?
    ├─ process_single_task(task_id, candidate_id, company_name)
    │   ↓
    │   ┌──────────────────────────────────────┐
    │   │ STEP 1: Resolve Profile URL         │
    │   │ - ProfileResolver.resolve()          │
    │   │ - Searches for russprofile.ru URL   │
    │   │ - UPDATE russprofile_url             │
    │   └──────────────────────────────────────┘
    │   ↓
    │   ┌──────────────────────────────────────┐
    │   │ STEP 2: Fetch HTML                  │
    │   │ - Fetcher.fetch(url)                 │
    │   │ - httpx GET request                  │
    │   │ - RawPageStorage.save_snapshot()     │
    │   │   → INSERT INTO raw_pages            │
    │   │   → Save HTML to data/raw/*.html     │
    │   │ - UPDATE fetched_at, fetch_duration  │
    │   └──────────────────────────────────────┘
    │   ↓
    │   ┌──────────────────────────────────────┐
    │   │ STEP 3: Parse HTML                  │
    │   │ - RussprofileParser.parse(html)      │
    │   │ - BeautifulSoup4 extraction          │
    │   │ - Returns CompanyData object         │
    │   │ - UPDATE state = 'PARSED'            │
    │   └──────────────────────────────────────┘
    │   ↓
    │   ┌──────────────────────────────────────┐
    │   │ STEP 4: Save Lead                   │
    │   │ - _save_lead()                       │
    │   │ - INSERT INTO leads ... ON CONFLICT  │
    │   │ - UPDATE state = 'DONE'              │
    │   └──────────────────────────────────────┘
    │   ↓
    │   Task complete or failed
    └─ Continue to next task
    ↓
7. Log: "Batch completed: X succeeded, Y failed"
8. sleep(1 second)
9. Loop repeats
```

**Error Handling:**
```
If task fails:
    ↓
1. TaskQueue.mark_failed(task_id, error)
2. UPDATE state = 'FAILED', last_error = error
3. Task remains in DB for retry (if attempts < max_attempts)
4. Worker continues to next task (NO CRASH)
```

---

### 5. **Discovery Layer**

**Files:**
- `src/scrapper/discovery/base.py` → Base class for all sources
- `src/scrapper/discovery/sources/fake_source.py` → Test data source

**Discovery Flow:**
```
User triggers: POST /runs/discover
    ↓
API endpoint calls: FakeSource().run(create_tasks=True)
    ↓
┌────────────────────────────────────────────────┐
│ FakeSource.discover()                          │
│ - Returns 8 hardcoded candidates               │
│   [{"company_name": "Test LLC", ...}, ...]     │
└────────────────────────────────────────────────┘
    ↓
For each candidate:
    ├─ INSERT INTO candidates (company_name, source, metadata)
    │  ↓
    │  Returns candidate_id
    ↓
If create_tasks=True:
    └─ TaskQueue.create_task(candidate_id, priority=100)
       ↓
       INSERT INTO enrichment_tasks (candidate_id, state='NEW')
```

**To add new source (e.g., Yandex Maps):**
```
1. Create: src/scrapper/discovery/sources/yandex_maps.py
2. Inherit from: DiscoverySource
3. Implement: discover() method
4. Return: List[dict] with candidate data
5. Update: web/app.py to handle new source name
```

---

### 6. **Enrichment Layer**

**Files:**
- `enrichment/resolver.py` → Find russprofile.ru URLs
- `enrichment/fetcher.py` → HTTP client (httpx)
- `enrichment/parser.py` → Extract data from HTML
- `enrichment/llm_client.py` → Claude API fallback (optional)

**Enrichment Process Details:**

#### **Step 1: Profile Resolver**
```
Input: company_name="ООО Строй-Инвест", inn="7701234567"
    ↓
ProfileResolver.resolve(company_name, inn, fetcher)
    ↓
1. Build search URL:
   https://www.rusprofile.ru/search?query=ООО+Строй-Инвест
    ↓
2. Fetch search results page
3. Parse HTML for first .company-item link
4. Return: https://www.rusprofile.ru/id/7701234567
```

#### **Step 2: Fetcher**
```
Fetcher.fetch(url)
    ↓
1. httpx.get(url, timeout=(connect=10, total=30))
2. Follow redirects
3. Capture:
   - final_url
   - status_code
   - headers
   - html (raw bytes)
   - duration_ms
4. Return: FetchResult object
```

#### **Step 3: Parser**
```
RussprofileParser.parse(html, source_url)
    ↓
1. BeautifulSoup(html, 'html.parser')
2. Extract via CSS selectors:
   - company_name: .company-name
   - inn: .requisites-inn
   - phone: .contact-phone
   - email: .contact-email
   - address: .address
   - ceo_name: .director
   - revenue: .finance-revenue
   - ... etc
3. Return: CompanyData object
```

#### **Step 4: LLM Fallback (Optional)**
```
If deterministic parser fails:
    ↓
1. Check: config.claude_api_key is set?
    ↓ (if not → skip)
2. LLMClient.extract_contacts(html, company_name)
    ↓
3. Call: Anthropic API with claude-3-5-sonnet
4. Prompt: "Extract phone/email from this HTML"
5. Parse JSON response
6. Return: extracted data
    ↓
7. TaskQueue.mark_parsed(task_id, method='llm_fallback')
```

---

### 7. **Storage Layer**

**Files:**
- `storage/raw_pages.py` → Save HTML snapshots

**Storage Flow:**
```
Worker fetches HTML
    ↓
RawPageStorage.save_snapshot(task_id, url, html, status_code, headers)
    ↓
1. Generate filename: f"{task_id}_{timestamp}.html"
2. Save to filesystem: data/raw/{task_id}_{timestamp}.html
3. Insert metadata to DB:
   INSERT INTO raw_pages (task_id, url, file_path, ...)
    ↓
Files stored FOREVER (manual cleanup if needed)
```

**Filesystem Structure:**
```
data/
├── raw/
│   ├── 123_20240213_153000.html  (task_id=123)
│   ├── 124_20240213_153010.html  (task_id=124)
│   └── ...
└── exports/
    └── leads_20240213_153000.csv  (temporary)
```

---

### 8. **Export Layer**

**File:** `export/exporter.py`

**Export Flow:**
```
User requests: GET /export
    ↓
LeadExporter.export_to_csv(output_file, limit)
    ↓
1. Query database:
   SELECT company_name, inn, phone, email, ...
   FROM leads
   ORDER BY enriched_at DESC
   LIMIT {limit}
    ↓
2. Open CSV file with UTF-8-BOM (Excel compatibility)
3. Write header row
4. Write data rows
5. Close file
    ↓
6. Return file path
    ↓
API returns FileResponse with:
   - media_type: text/csv
   - filename: leads_{timestamp}.csv
```

---

## Data Flow Diagrams

### Complete Request-to-Lead Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ USER INITIATES DISCOVERY                                        │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: API Request                                             │
│ curl -X POST https://scrapper.com/runs/discover                 │
│      -d '{"source":"fake","create_tasks":true}'                 │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Discovery (API Container)                               │
│ - FakeSource.discover() returns 8 candidates                    │
│ - INSERT INTO candidates (company_name, source, metadata)       │
│ - Returns: [candidate_id=1, candidate_id=2, ...]               │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Task Creation (API Container)                           │
│ - For each candidate:                                           │
│   TaskQueue.create_task(candidate_id, priority=100)             │
│ - INSERT INTO enrichment_tasks (state='NEW')                    │
│ - Returns: [task_id=101, task_id=102, ...]                     │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ DATABASE STATE                                                   │
│ candidates:       8 rows  (source='fake')                       │
│ enrichment_tasks: 8 rows  (state='NEW')                         │
│ leads:            0 rows                                        │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Worker Polling (Worker Container)                       │
│ - Every 5 seconds: TaskQueue.claim_batch(10)                    │
│ - Claims all 8 tasks                                            │
│ - UPDATE state = 'FETCHING', attempts = 1                       │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Task Processing (Worker Container)                      │
│ For task_id=101, candidate_id=1, company="Test LLC":           │
│                                                                  │
│ 5a. ProfileResolver.resolve("Test LLC", inn=None)               │
│     → Returns: "https://russprofile.ru/id/1234567890"          │
│     → UPDATE russprofile_url                                    │
│                                                                  │
│ 5b. Fetcher.fetch(url)                                          │
│     → httpx.get() with timeout=(10, 30)                         │
│     → Returns: FetchResult(html, status=200, duration=1234ms)   │
│     → RawPageStorage.save_snapshot()                            │
│       ├─ INSERT INTO raw_pages                                  │
│       └─ Write: data/raw/101_20240213_153000.html               │
│     → UPDATE fetched_at, fetch_duration_ms                      │
│                                                                  │
│ 5c. RussprofileParser.parse(html)                               │
│     → BeautifulSoup extracts data                               │
│     → Returns: CompanyData(inn, phone, email, ...)              │
│     → UPDATE state = 'PARSED', parse_method = 'deterministic'   │
│                                                                  │
│ 5d. _save_lead(task_id, candidate_id, url, company_data)        │
│     → INSERT INTO leads ... ON CONFLICT UPDATE                  │
│     → UPDATE state = 'DONE'                                     │
│                                                                  │
│ Task 101 complete!                                              │
│ Repeat for tasks 102-108...                                     │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ FINAL DATABASE STATE (after ~2-5 minutes)                       │
│ candidates:       8 rows  (source='fake')                       │
│ enrichment_tasks: 8 rows  (state='DONE')                        │
│ leads:            8 rows  (company data populated)              │
│ raw_pages:        8 rows  + 8 HTML files on disk               │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ USER EXPORTS LEADS                                              │
│ curl https://scrapper.com/export -o leads.csv                   │
│ → Downloads CSV with 8 enriched companies                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Dependencies

### Dependency Graph

```
Configuration:
    .env
    ├→ docker-compose.yml (reads env vars)
    ├→ src/scrapper/config.py (via pydantic-settings)
    └→ All containers (via environment variables)

Docker Infrastructure:
    docker-compose.yml
    ├→ postgres (reads schema.sql)
    │   └→ src/scrapper/db/schema.sql
    ├→ api (built from Dockerfile)
    │   ├→ Dockerfile
    │   │   └→ pyproject.toml
    │   └→ src/scrapper/web/app.py (entrypoint)
    ├→ worker (built from Dockerfile)
    │   └→ src/scrapper/pipeline/worker.py (entrypoint)
    └→ caddy (reads Caddyfile)
        └→ Caddyfile

Python Application:
    src/scrapper/config.py (config singleton)
    ├→ src/scrapper/db/connection.py (DB pool)
    │   ├→ src/scrapper/db/queue.py (task operations)
    │   │   ├→ src/scrapper/web/app.py (API endpoints)
    │   │   └→ src/scrapper/pipeline/worker.py (task processor)
    │   ├→ src/scrapper/db/models.py (data models)
    │   └→ src/scrapper/export/exporter.py (CSV export)
    ├→ src/scrapper/discovery/sources/*.py
    │   └→ src/scrapper/web/app.py
    ├→ src/scrapper/enrichment/*.py
    │   └→ src/scrapper/pipeline/worker.py
    └→ src/scrapper/storage/raw_pages.py
        └→ src/scrapper/pipeline/worker.py

Documentation:
    docs/GO_LIVE_CHECKLIST.md
    ├→ references: scripts/vps_bootstrap_ubuntu.sh
    ├→ references: scripts/vps_deploy.sh
    └→ references: .env.production.example

    docs/CUSTOMER_QUICKSTART.md
    └→ references: web API endpoints

    docs/RU_MARKET_DEFAULTS.md
    └→ referenced by: .env.production.example

Deployment Scripts:
    scripts/vps_bootstrap_ubuntu.sh
    ├→ Installs: Docker, Docker Compose, UFW
    └→ Creates: scrapper user

    scripts/vps_deploy.sh
    ├→ Reads: .env
    ├→ Executes: docker compose build
    └→ Executes: docker compose up -d

    scripts/setup_cron_backups.sh
    ├→ Creates: backups/
    └→ Configures: cron job for daily backups

Tests:
    tests/unit/*.py
    └→ Imports: src/scrapper/*

    tests/integration/*.py
    ├→ Requires: PostgreSQL running
    └→ Imports: src/scrapper/*
```

---

## Configuration Propagation

### How Config Flows Through the System

```
1. LOCAL DEVELOPMENT
   ─────────────────
   .env (on host)
       ↓
   docker-compose.yml reads via ${VAR} syntax
       ↓
   Container environment variables set
       ↓
   src/scrapper/config.py reads via os.environ
       ↓
   Config singleton created
       ↓
   All modules import: from scrapper.config import config
       ↓
   Use: config.database_url, config.worker_poll_interval, etc.

2. PRODUCTION DEPLOYMENT
   ──────────────────────
   .env.production.example (template)
       ↓
   Admin copies to .env and fills values
       ↓
   scripts/vps_deploy.sh validates:
       - APP_PASSWORD != "testpassword123"
       - DOMAIN != "localhost"
       ↓
   Same flow as local development
```

### Configuration Hierarchy

```
Priority (highest to lowest):
1. Environment variables (docker-compose env:)
2. .env file values
3. Config class defaults (in config.py)
4. Pydantic Field defaults

Example:
    WORKER_POLL_INTERVAL in docker-compose.yml env:
        ↓ (overrides)
    WORKER_POLL_INTERVAL in .env:
        ↓ (overrides)
    Field(default=5) in config.py
```

---

## Event Flow

### What Triggers What

#### **Container Startup Events**

```
docker compose up -d
    ↓
┌────────────────────────────────────────┐
│ 1. postgres container starts          │
│    - Executes schema.sql (first time) │
│    - Health check begins               │
└────────────────┬───────────────────────┘
                 │
                 ↓ (depends_on: postgres healthy)
┌────────────────────────────────────────┐
│ 2. api container starts                │
│    - Waits for postgres health         │
│    - uvicorn starts FastAPI            │
│    - app.startup_event():              │
│      • setup_logging()                 │
│      • get_pool()  (connects to DB)    │
│    - Health check begins               │
└────────────────┬───────────────────────┘
                 │
                 ↓ (depends_on: postgres healthy)
┌────────────────────────────────────────┐
│ 3. worker container starts             │
│    - Waits for postgres health         │
│    - scrapper-worker CLI command       │
│    - worker.main():                    │
│      • setup_logging()                 │
│      • run_worker_loop()               │
│      • Starts polling queue            │
└────────────────┬───────────────────────┘
                 │
                 ↓ (depends_on: api)
┌────────────────────────────────────────┐
│ 4. caddy container starts              │
│    - Loads Caddyfile                   │
│    - Provisions SSL (if DOMAIN set)    │
│    - Proxies to api:8000               │
└────────────────────────────────────────┘
```

#### **User Request Events**

```
POST /runs/discover → Discovery → Tasks Created → Worker Processes
GET /stats          → Read-only query → Returns counts
GET /export         → Query leads → Generate CSV → Download
```

#### **Background Events (No User Trigger)**

```
Every 5 seconds:
    Worker polls queue
        ↓
    If tasks exist → Claims → Processes
    If no tasks → Sleep 5s

Every 30 seconds:
    API health check
        ↓
    SELECT 1 from database
        ↓
    Update container health status

Every 2 AM (if cron configured):
    Backup script runs
        ↓
    pg_dump scrapper > backup.sql
        ↓
    Delete backups older than 7 days
```

---

## Deployment Flow

### From Code to Production

```
┌────────────────────────────────────────────────────────────┐
│ DEVELOPMENT (Your Machine)                                 │
└──────────────────────────┬─────────────────────────────────┘
                           │
                           ↓
┌────────────────────────────────────────────────────────────┐
│ STEP 1: Git Repository                                     │
│ - git init                                                 │
│ - git add .                                                │
│ - git commit -m "production deployment package"           │
│ - git tag v1.0.0                                           │
└──────────────────────────┬─────────────────────────────────┘
                           │
                           ↓
┌────────────────────────────────────────────────────────────┐
│ STEP 2: GitHub                                             │
│ - gh repo create scrapper --private                        │
│ - git push -u origin main --tags                           │
└──────────────────────────┬─────────────────────────────────┘
                           │
                           ↓
┌────────────────────────────────────────────────────────────┐
│ STEP 3: VPS Provisioning                                   │
│ - Buy VPS (Hetzner Helsinki recommended)                   │
│ - SSH as root                                              │
│ - Run: scripts/vps_bootstrap_ubuntu.sh                     │
│   ├─ Installs Docker + Docker Compose                      │
│   ├─ Configures UFW firewall                               │
│   ├─ Creates scrapper user                                 │
│   └─ Hardens SSH                                           │
└──────────────────────────┬─────────────────────────────────┘
                           │
                           ↓
┌────────────────────────────────────────────────────────────┐
│ STEP 4: DNS Configuration                                  │
│ - Point A record: scrapper.yourdomain.com → VPS_IP        │
│ - Wait 5-30 minutes for propagation                        │
└──────────────────────────┬─────────────────────────────────┘
                           │
                           ↓
┌────────────────────────────────────────────────────────────┐
│ STEP 5: Application Deployment                             │
│ - SSH as scrapper user                                     │
│ - git clone https://github.com/you/scrapper.git            │
│ - cd scrapper                                              │
│ - cp .env.production.example .env                          │
│ - nano .env (set DOMAIN, passwords)                        │
│ - Run: scripts/vps_deploy.sh                               │
│   ├─ Validates .env                                        │
│   ├─ docker compose build                                  │
│   ├─ docker compose up -d                                  │
│   └─ Runs smoke tests                                      │
└──────────────────────────┬─────────────────────────────────┘
                           │
                           ↓
┌────────────────────────────────────────────────────────────┐
│ STEP 6: Verify Deployment                                  │
│ - curl https://scrapper.yourdomain.com/health              │
│ - Check Caddy provisioned SSL certificate                  │
│ - docker compose ps (all 4 containers running)             │
└──────────────────────────┬─────────────────────────────────┘
                           │
                           ↓
┌────────────────────────────────────────────────────────────┐
│ STEP 7: Setup Backups & Monitoring                         │
│ - Run: scripts/setup_cron_backups.sh                       │
│ - Setup: UptimeRobot (monitor /health endpoint)            │
└──────────────────────────┬─────────────────────────────────┘
                           │
                           ↓
┌────────────────────────────────────────────────────────────┐
│ PRODUCTION RUNNING ✅                                      │
│ - API: https://scrapper.yourdomain.com                     │
│ - Worker: Processing tasks every 5s                        │
│ - Database: Persistent via Docker volume                   │
│ - Backups: Daily at 2 AM                                   │
└────────────────────────────────────────────────────────────┘
```

---

## Critical Interactions

### Database Connection Pool

```
Application starts
    ↓
config.py loads DATABASE_URL from env
    ↓
connection.py creates global pool:
    pool = ConnectionPool(
        conninfo=config.database_url,
        min_size=config.db_pool_min_size,  # default: 2
        max_size=config.db_pool_max_size,  # default: 10
    )
    ↓
All DB operations use pool:
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT ...")
```

**Why it matters:**
- API and Worker share the same pool configuration
- Pool prevents connection exhaustion
- Automatic reconnection on connection failure

### Task Queue Locking

```
Worker 1 claims task:
    SELECT id FROM enrichment_tasks
    WHERE state = 'NEW'
    ORDER BY priority DESC
    LIMIT 1
    FOR UPDATE SKIP LOCKED  ← KEY: This prevents Worker 2 from claiming same task
    ↓
    UPDATE state = 'FETCHING', attempts = attempts + 1

Worker 2 simultaneously claims:
    ← SKIP LOCKED means Worker 2 gets the NEXT task, not the same one
```

**Why it matters:**
- Enables horizontal scaling (multiple workers)
- No task duplication
- No complex distributed locking needed

### Volume Mounting

```
docker-compose.yml:
    api:
      volumes:
        - ./data/raw:/app/data/raw       ← Host path : Container path
        - ./data/exports:/app/data/exports

This means:
    Host: /home/scrapper/scrapper/data/raw/123.html
    Container: /app/data/raw/123.html
```

**Why it matters:**
- Raw pages persist if container restarts
- Can inspect/delete files from host
- Shared between API and Worker containers

---

## Summary: The Chain of Causality

```
User Action
    ↓
API Endpoint Triggered
    ↓
Business Logic Executes (discovery, export, etc.)
    ↓
Database State Changes (INSERT, UPDATE)
    ↓
Worker Detects Changes (via polling)
    ↓
Worker Processes Tasks
    ↓
External HTTP Requests (fetch company pages)
    ↓
HTML Parsing
    ↓
Data Persisted (leads table + raw files)
    ↓
User Exports Results (CSV download)
```

**Every action has a clear trigger:**
- Discovery: User POST request
- Task creation: Discovery completion
- Task processing: Worker polling loop
- Lead creation: Successful parsing
- Export: User GET request
- Backups: Cron schedule (if configured)

**Nothing happens "magically" — everything is traceable:**
- Logs: Structured logging with context
- Database: Audit trail via timestamps
- Files: Raw HTML snapshots for debugging
- Metrics: /stats endpoint shows pipeline state

---

## Next Steps

For detailed information on specific components:
- **Configuration:** See `src/scrapper/config.py`
- **API Endpoints:** See `docs/CUSTOMER_QUICKSTART.md`
- **Database Schema:** See `src/scrapper/db/schema.sql`
- **Worker Logic:** See `src/scrapper/pipeline/worker.py`
- **Deployment:** See `docs/GO_LIVE_CHECKLIST.md`

---

**End of Architecture Document**
