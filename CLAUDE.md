# Project Summary for Claude

## What This Is

A **lead generation pipeline** for Russian construction companies. It discovers company names from various sources, looks them up on **russprofile.ru** (a Russian company registry site, like a Crunchbase for Russian businesses), scrapes their profile pages, extracts structured business data (INN, OGRN, contacts, revenue, etc.), and stores enriched leads in PostgreSQL. Non-technical users interact via a web dashboard with one-click buttons and Excel export.

## Architecture (Two-Stage Pipeline)

### Stage 1: Discovery
- Pluggable sources yield `CandidateHint` objects (company name + metadata)
- Currently only `FakeSource` exists (8 hardcoded test companies)
- Candidates saved to `candidates` table, enrichment tasks auto-created in `enrichment_tasks` queue

### Stage 2: Enrichment (resolve -> fetch -> parse -> save)
1. **Resolve** (`ProfileResolver`): Search russprofile.ru by company name/INN, fetch top 3 profile pages, score each match (name similarity + INN match + region), return best URL if score >= 60
2. **Fetch** (`Fetcher`): Download HTML with retry + backoff. Priority: Bright Data Web Access API -> Bright Data Web Unlocker proxy -> direct HTTP
3. **Parse** (`RussprofileParser`): Label-based HTML extraction (finds "ИНН:", "ОГРН:", etc. and extracts adjacent values). Optional LLM fallback for contacts when deterministic parsing fails
4. **Save**: Insert into `leads` table with UPSERT on task_id

### Execution Modes
- **CLI** (`scrapper` command): `init-db`, `discover`, `enrich`, `export`, `stats`
- **Web API** (FastAPI): REST endpoints + Jinja2 dashboard at `/ui/`
- **Background Worker** (`scrapper-worker`): Continuous poll loop, processes tasks from queue, graceful SIGTERM shutdown
- **Docker Compose**: postgres + api + worker + caddy (reverse proxy with TLS)

## Database Schema (4 tables)
- `candidates` — raw company names from discovery (unique per source+name)
- `enrichment_tasks` — Postgres-backed task queue (NEW -> FETCHING -> PARSED -> DONE/FAILED)
- `raw_pages` — HTML snapshot metadata (file saved to `data/raw/`)
- `leads` — final enriched records (company_name, inn, ogrn, phone, email, address, revenue, ceo, etc.)

## Key Tech
- Python 3.11+, PostgreSQL 14+, psycopg3 (sync), httpx, BeautifulSoup + lxml
- FastAPI + Jinja2 + openpyxl (Excel export)
- Bright Data (Web Unlocker proxy + Web Access API + Browser API stub)
- Pydantic Settings for env-based config
- HTTP Basic Auth on web endpoints

## Current State — What Works
- Full pipeline scaffold is built end-to-end
- CLI commands functional (init-db, discover with fake source, enrich, export, stats)
- Web UI dashboard with stats, discovery trigger, export buttons
- Fetcher with 3 fetch strategies and retry logic
- Parser with label-based extraction for all fields (INN, OGRN, KPP, address, CEO, revenue, phones, emails, website)
- LLM client interface defined with validation/normalization (but no real Claude API implementation)
- Background worker with graceful shutdown
- Docker Compose deployment with Caddy reverse proxy
- Excel (.xlsx) export with proper formatting

## Critical TODOs — What Needs Work Next

### 1. Real Discovery Sources (HIGH PRIORITY)
The only discovery source is `FakeSource` with 8 hardcoded companies. Need real sources:
- **Yandex Maps API** — search for construction companies by region
- **Government registries** — EGRUL/EGRIP data
- **Industry directories** — construction-specific databases

### 2. Parser Validation Against Real HTML (HIGH PRIORITY)
The `RussprofileParser` uses label-based extraction but has **never been tested against real russprofile.ru HTML**. CSS selectors for search results (`.company-item`, `.search-result`, `div[data-company-id]`) are guesses. Need to:
- Fetch a real russprofile.ru page and inspect actual HTML structure
- Validate/fix all CSS selectors in `ProfileResolver._extract_profile_urls()`
- Validate label-based extraction against real page layout

### 3. LLM Fallback Implementation (MEDIUM)
The `LlmClient` is an abstract interface with only a `NullLlmClient`. Need a real `AnthropicLlmClient` that calls the Claude API for contact extraction when deterministic parsing fails. The prompts (`llm_prompts.py`) and validation (`llm_validate.py`) are already built.

### 4. Bright Data Configuration (MEDIUM)
The `.env` has `BRIGHTDATA_PROXY_A=604f2a0a-...` but the config expects `BRIGHTDATA_PROXY_URL` (full proxy URL format). This mismatch means Bright Data proxy is **not actually connected**. Need to either:
- Set `BRIGHTDATA_PROXY_URL` with full proxy URL, or
- Set `BRIGHTDATA_API_KEY` for the Web Access API path

### 5. Misc
- `_save_lead()` is duplicated in both `cli.py` and `worker.py` — should be extracted
- No tests for the parser against real HTML
- No rate limiting on HTTP requests
- No concurrent/async task processing (currently synchronous)
- Worker creates a new `Fetcher` instance per task (should reuse)
