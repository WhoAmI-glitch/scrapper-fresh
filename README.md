# Russian Construction Company Lead Generator

Two-stage pipeline for discovering and enriching Russian construction company data from russprofile.ru.

## Architecture

### Stage 1: Discovery
Find construction company candidates from pluggable sources:
- **Fake Source** (demo): Returns hardcoded test companies
- **Future sources**: Yandex Maps, government registries, industry directories, etc.

Candidates are stored in the `candidates` table with source attribution.

### Stage 2: Enrichment
For each candidate, the pipeline:
1. **Resolve**: Find the company's russprofile.ru profile URL
2. **Fetch**: Download HTML via Bright Data Web Unlocker proxy
3. **Parse**: Extract company data (INN, OGRN, contacts, revenue, etc.)
4. **Save**: Store enriched lead in `leads` table

All HTML is saved to disk (`data/raw/`) for debugging and replay.

## Database Schema

- `candidates`: Raw company names from discovery sources
- `enrichment_tasks`: Postgres-backed task queue (states: NEW → FETCHING → PARSED → DONE/FAILED)
- `raw_pages`: HTML snapshot metadata
- `leads`: Final enriched company records with full contact/business data

## Tech Stack

- **Python 3.11+**
- **PostgreSQL** (single durable store + task queue)
- **psycopg3** (async-ready Postgres driver)
- **httpx** (HTTP client for fetching)
- **BeautifulSoup + lxml** (HTML parsing)
- **Bright Data Web Unlocker** (proxy for russprofile.ru)
- **Click** (CLI framework)
- **Pydantic** (config management)
- **FastAPI** (web API + UI)
- **Jinja2** (HTML templates)
- **openpyxl** (Excel export)

## Web UI

**Simple web interface for non-technical users**:

- 📊 Dashboard with real-time stats
- 🚀 One-click discovery and enrichment
- 📥 Excel (.xlsx) export with proper formatting

**Quick Start**:
```bash
docker compose up -d --build
# Open http://localhost/ui/
# Login: admin / testpassword123
```

See [docs/WEB_UI.md](docs/WEB_UI.md) for complete documentation.

## Setup

### 1. Prerequisites

- Python 3.11 or higher
- PostgreSQL 14+ running locally or remotely

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package in development mode
pip install -e .
```

### 3. Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env and set your database URL
# Optionally add Bright Data proxy credentials
```

Minimum required configuration:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/scrapper
```

### 4. Initialize Database

```bash
scrapper init-db
```

This creates all tables and indexes defined in `src/scrapper/db/schema.sql`.

## Usage

### CLI Commands

The `scrapper` CLI provides four main commands:

#### 1. Initialize Database
```bash
scrapper init-db
```
Creates database schema. Safe to run multiple times (idempotent).

#### 2. Run Discovery
```bash
# Discover candidates using the fake source (demo data)
scrapper discover --source fake

# Discovery without creating enrichment tasks
scrapper discover --source fake --no-tasks
```

This finds candidate companies and creates enrichment tasks for them.

#### 3. Process Enrichment
```bash
# Process up to 10 tasks (default batch size)
scrapper enrich

# Process specific number of tasks
scrapper enrich --batch-size 50

# Dry run (no HTTP requests)
scrapper enrich --dry-run
```

For each task:
- Resolves company name to russprofile URL
- Fetches HTML (via Bright Data if configured)
- Saves raw HTML snapshot to `data/raw/`
- Parses company data using deterministic CSS selectors
- Saves enriched lead to database

#### 4. Export Leads
```bash
# Export to CSV (default)
scrapper export

# Export to JSON
scrapper export --format json

# Limit number of records
scrapper export --limit 100

# Custom output filename
scrapper export --output my_leads.csv

# Include raw_data field (JSON only)
scrapper export --format json --include-raw
```

Exports are saved to `data/exports/` by default.

#### 5. View Statistics
```bash
scrapper stats
```

Shows:
- Queue status (tasks by state)
- Candidates by source
- Total leads
- Raw pages stored

### Example Workflow

```bash
# 1. Initialize database
scrapper init-db

# 2. Discover companies
scrapper discover --source fake
# Output: Discovered 8 candidates

# 3. Process enrichment tasks
scrapper enrich --batch-size 5
# Output: Success: 5, Failed: 0

# 4. Check progress
scrapper stats

# 5. Export results
scrapper export --format csv
# Output: Exported to data/exports/leads_20260213_143022.csv
```

## Project Structure

```
scrapper/
├── pyproject.toml              # Dependencies and package config
├── README.md                   # This file
├── .env.example                # Example environment variables
├── data/
│   ├── raw/                    # Raw HTML snapshots (YYYY-MM-DD/)
│   └── exports/                # CSV/JSON exports
└── src/scrapper/
    ├── __init__.py
    ├── config.py               # Environment-based configuration
    ├── logging_.py             # Structured logging setup
    ├── cli.py                  # CLI entrypoint
    ├── db/
    │   ├── __init__.py
    │   ├── schema.sql          # Database schema
    │   ├── connection.py       # Connection pooling
    │   ├── models.py           # Data classes
    │   └── queue.py            # Task queue abstraction
    ├── discovery/
    │   ├── __init__.py
    │   ├── base.py             # DiscoverySource base class
    │   └── sources/
    │       ├── __init__.py
    │       └── fake_source.py  # Demo source plugin
    ├── enrichment/
    │   ├── __init__.py
    │   ├── resolver.py         # Resolve company → profile URL
    │   ├── fetcher.py          # HTTP client (Bright Data)
    │   └── parser.py           # HTML parsing (deterministic)
    ├── storage/
    │   ├── __init__.py
    │   └── raw_pages.py        # Raw HTML snapshot storage
    └── export/
        ├── __init__.py
        └── exporter.py         # CSV/JSON export
```

## Configuration

All configuration is via environment variables (`.env` file or shell exports).

Key settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://...` | PostgreSQL connection string |
| `BRIGHTDATA_PROXY_URL` | None | Bright Data proxy (optional for dev) |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `TASK_BATCH_SIZE` | `10` | Tasks to process per `enrich` run |
| `MAX_TASK_ATTEMPTS` | `3` | Max retries before marking FAILED |

See [.env.example](.env.example) for all options.

## Development

### Adding a New Discovery Source

1. Create a new file in `src/scrapper/discovery/sources/`
2. Subclass `DiscoverySource`
3. Implement `discover()` method to yield `CandidateHint` objects
4. Register in `src/scrapper/discovery/sources/__init__.py`
5. Add to CLI choices in `cli.py`

Example:
```python
from scrapper.discovery.base import DiscoverySource, CandidateHint

class YandexMapsSource(DiscoverySource):
    def __init__(self):
        super().__init__(source_name="yandex_maps")

    def discover(self):
        # Fetch from Yandex Maps API
        for company in self._fetch_companies():
            yield CandidateHint(
                company_name=company["name"],
                hint_text=company["category"],
                metadata={"lat": company["lat"], "lon": company["lon"]}
            )
```

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests (when added)
pytest
```

### Code Quality

```bash
# Format code
black src/

# Lint
ruff src/

# Type checking
mypy src/
```

## Limitations & TODOs

This is an MVP scaffold. The following are **stubbed** and need implementation:

### Critical TODOs
- [ ] **ProfileResolver**: Currently returns search URL, not actual profile URL
  - Need to fetch search results and extract best match
- [ ] **RussprofileParser**: Placeholder CSS selectors
  - Need to inspect actual russprofile.ru HTML structure
  - Implement robust selectors for all fields
- [ ] **Bright Data Integration**: Works but not tested with real proxy
  - Add proper error handling for proxy failures
- [ ] **LLM Fallback Parser**: Not implemented
  - Add Claude API integration for when deterministic parsing fails

### Nice-to-Haves
- [ ] Add retry logic with exponential backoff
- [ ] Add rate limiting for HTTP requests
- [ ] Implement concurrent task processing (async/multiprocessing)
- [ ] Add monitoring/metrics (Prometheus)
- [ ] Add duplicate detection (fuzzy company name matching)
- [ ] Add data validation (pydantic models for parsed data)
- [ ] Add incremental discovery (track processed sources)

## License

Proprietary - Internal use only.

## Support

For issues or questions, contact the development team.
