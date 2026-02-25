# Quick Start Guide

## Verify Installation

### 1. Check Python Version
```bash
python --version  # Should be 3.11+
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows
```

### 3. Install Package
```bash
pip install -e .
```

### 4. Verify CLI
```bash
scrapper --help
```

You should see:
```
Usage: scrapper [OPTIONS] COMMAND [ARGS]...

  Russian construction company discovery and enrichment pipeline.

Commands:
  discover  Run discovery to find candidate companies.
  enrich    Process enrichment tasks: resolve → fetch → parse → save.
  export    Export enriched leads to CSV or JSON.
  init-db   Initialize database schema from schema.sql.
  stats     Show pipeline statistics.
```

## Database Setup

### Option 1: Local PostgreSQL

Install PostgreSQL locally and create a database:

```bash
# Install PostgreSQL (macOS)
brew install postgresql@14
brew services start postgresql@14

# Create database
createdb scrapper

# Update .env
cp .env.example .env
# Edit .env and set:
# DATABASE_URL=postgresql://yourusername@localhost:5432/scrapper
```

### Option 2: Docker PostgreSQL

```bash
docker run --name scrapper-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=scrapper \
  -p 5432:5432 \
  -d postgres:14

# Use default DATABASE_URL in .env.example
cp .env.example .env
```

## Test the Pipeline

### 1. Initialize Database
```bash
scrapper init-db
```

Expected output:
```
Initializing database schema...
✓ Database schema initialized successfully
```

### 2. Run Discovery (Fake Data)
```bash
scrapper discover --source fake
```

Expected output:
```
Running discovery from source: fake
✓ Discovered 8 candidates
Queue stats: {'NEW': 8}
```

### 3. Check Stats
```bash
scrapper stats
```

Expected output:
```
Queue Statistics:
  NEW: 8

Overall Statistics:
  Candidates by source:
    fake: 8
  Total leads: 0
  Raw pages stored: 0
```

### 4. Process Tasks (Dry Run)
```bash
scrapper enrich --batch-size 3 --dry-run
```

Expected output:
```
DRY RUN MODE - no HTTP requests will be made
Processing up to 3 enrichment tasks...
Claimed 3 tasks from queue

[Task 1] Processing: ООО "СтройИнжиниринг"
  → Resolving profile URL...
  → Profile URL: https://www.russprofile.ru/search?name=...
  → [DRY RUN] Skipping fetch and parse
  ✓ Task 1 completed successfully

[... more tasks ...]

============================================================
Enrichment completed:
  ✓ Success: 3
  ✗ Failed:  0
============================================================
```

### 5. Process Real Tasks (Without Bright Data)

**Note**: Without Bright Data proxy, this will make direct requests to russprofile.ru.
For testing, this works but may be rate-limited.

```bash
scrapper enrich --batch-size 2
```

This will:
- Resolve company names to URLs
- Fetch HTML (direct request, no proxy)
- Save raw HTML to `data/raw/YYYY-MM-DD/`
- Parse (placeholder selectors - won't extract real data yet)
- Save to leads table

### 6. Export Results
```bash
scrapper export --format csv
```

Output:
```
Exporting leads to CSV...
Found 2 leads in database
✓ Exported to: data/exports/leads_20260213_195500.csv
```

Check the file:
```bash
cat data/exports/leads_*.csv
```

## Next Steps

### For Production Use

1. **Add Bright Data Proxy**
   - Sign up at https://brightdata.com
   - Get Web Unlocker credentials
   - Add to `.env`:
     ```
     BRIGHTDATA_PROXY_URL=http://user:pass@proxy.brightdata.com:22225
     ```

2. **Implement Real Parsing**
   - Inspect russprofile.ru HTML structure
   - Update CSS selectors in `src/scrapper/enrichment/parser.py`
   - Test with real data

3. **Add Real Discovery Sources**
   - Implement Yandex Maps source
   - Implement government registry source
   - Add to `src/scrapper/discovery/sources/`

4. **Deploy**
   - Set up production PostgreSQL
   - Configure environment variables
   - Run as cron job or service
   - Add monitoring

## Troubleshooting

### "Module not found" errors
```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Reinstall
pip install -e .
```

### Database connection errors
```bash
# Check PostgreSQL is running
pg_isready

# Check DATABASE_URL in .env
cat .env | grep DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

### Import errors
```bash
# Check package is installed
pip list | grep scrapper

# Reinstall in editable mode
pip install -e .
```

## Project Status

**Working**:
- ✅ Full project structure
- ✅ Database schema and migrations
- ✅ CLI commands (init-db, discover, enrich, export, stats)
- ✅ Postgres-backed task queue
- ✅ Raw HTML snapshot storage
- ✅ Fake discovery source (demo data)
- ✅ CSV/JSON export

**Stubbed (TODOs)**:
- ⚠️ ProfileResolver: Returns search URL, not actual profile URL
- ⚠️ RussprofileParser: Placeholder CSS selectors (won't extract real data)
- ⚠️ Bright Data: Integration code exists but not tested
- ⚠️ LLM Fallback: Not implemented (planned for later)

**To Be Added**:
- 🔜 Real discovery sources (Yandex Maps, gov registries)
- 🔜 Actual russprofile.ru parsing
- 🔜 Claude API integration for fallback parsing
- 🔜 Concurrent processing (async/parallel)
- 🔜 Tests
