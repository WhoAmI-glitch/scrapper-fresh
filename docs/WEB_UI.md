# Web UI & Excel Export

Simple web interface for the Scrapper pipeline with Excel export functionality.

## Features

- 📊 **Dashboard**: Real-time stats showing leads, candidates, queue status
- 🚀 **One-Click Actions**: Trigger discovery and check enrichment status
- 📥 **Excel Export**: Download enriched leads as .xlsx with proper formatting
- 🔒 **Secure**: HTTP Basic Authentication required for all operations
- 🔄 **Auto-Refresh**: Dashboard updates every 30 seconds

## Quick Start

### Local Development

1. **Start the stack**:
   ```bash
   docker compose up -d --build
   ```

2. **Open the dashboard**:
   ```
   http://localhost/ui/
   ```

3. **Login with credentials** (from `.env`):
   - Username: `admin`
   - Password: `testpassword123` (change this in production!)

4. **Use the dashboard**:
   - Click **Run Discovery** to discover companies
   - Click **Check Enrichment Queue** to see processing status
   - Click **Download Excel** to export leads

### Production Deployment

1. **Set strong credentials in `.env`**:
   ```bash
   APP_USERNAME=admin
   APP_PASSWORD=<strong-password-here>
   ```

2. **Deploy to VPS** (see [README_PRODUCTION.md](../README_PRODUCTION.md)):
   ```bash
   docker compose up -d --build
   ```

3. **Access via domain or IP**:
   ```
   http://yourdomain.com/ui/
   # or
   http://your-vps-ip/ui/
   ```

## API Endpoints

### Web UI Routes

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/ui/` | GET | Yes | Dashboard page |
| `/ui/discover` | POST | Yes | Trigger discovery |
| `/ui/enrich` | POST | Yes | Check queue status |

### Export Routes

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/export` | GET | Yes | Download CSV |
| `/export.xlsx` | GET | Yes | Download Excel |

#### Query Parameters

- `limit` (optional): Limit number of records to export
  - Example: `/export.xlsx?limit=100`

## Excel Export Details

### Column Schema (18 columns)

1. **id** - Lead ID
2. **company_name** - Company name
3. **inn** - Tax ID (formatted as text to prevent scientific notation)
4. **ogrn** - Registration number (formatted as text)
5. **kpp** - Tax reason code
6. **phone** - Phone number (formatted as text)
7. **email** - Email address
8. **website** - Website URL
9. **address** - Company address
10. **ceo_name** - CEO/Director name
11. **revenue_rub** - Revenue in rubles
12. **employee_count** - Number of employees
13. **registration_date** - Company registration date
14. **okved_codes** - OKVED codes (comma-separated)
15. **russprofile_url** - Source profile URL
16. **enriched_at** - Enrichment timestamp
17. **discovery_source** - Discovery source name
18. **discovered_at** - Discovery timestamp

### Excel Formatting Features

- ✅ **Bold headers** for easy reading
- ✅ **Frozen first row** for scrolling large datasets
- ✅ **TEXT format** for INN/OGRN/KPP/phone to prevent scientific notation
- ✅ **Auto-adjusted column widths** for better visibility
- ✅ **Proper MIME type** for direct download

### Why TEXT Format for INN/OGRN?

Russian tax IDs (INN) and registration numbers (OGRN) are long numeric strings that Excel treats as numbers by default, displaying them in scientific notation (e.g., `1.23E+12`).

We explicitly format these columns as TEXT to preserve the full number display.

## Testing

### Unit Tests

Run XLSX export tests:
```bash
pytest tests/unit/test_xlsx_export.py -v
```

### Integration Tests

Run UI and API tests:
```bash
pytest tests/integration/test_ui_api.py -v --tb=short
```

### Smoke Test

Run end-to-end smoke test:
```bash
./scripts/smoke_ui_export.sh
```

This script:
1. Starts Docker stack
2. Triggers discovery
3. Waits for enrichment
4. Downloads Excel file
5. Validates file structure
6. Cleans up

### Skip Build (Use Existing Images)

```bash
SKIP_BUILD=1 ./scripts/smoke_ui_export.sh
```

### Skip Cleanup (Keep Stack Running)

```bash
SKIP_CLEANUP=1 ./scripts/smoke_ui_export.sh
```

## Troubleshooting

### Dashboard shows "No leads available"

- Run discovery first: Click **Run Discovery** button
- Wait for worker to process tasks (check queue stats)
- Refresh page after enrichment completes

### Excel export returns 404

This means no leads exist in the database yet. Run discovery and enrichment first.

### Authentication fails

Check your credentials in `.env`:
```bash
cat .env | grep APP_
```

Make sure `APP_USERNAME` and `APP_PASSWORD` are set.

### UI not loading

1. Check services are running:
   ```bash
   docker compose ps
   ```

2. Check API health:
   ```bash
   curl http://localhost/health
   ```

3. Check logs:
   ```bash
   docker compose logs api --tail=50
   ```

## Architecture

### UI Stack

```
Browser → Caddy (reverse proxy) → FastAPI (app.py)
                                      ├─ Jinja2 Templates
                                      ├─ Basic Auth
                                      └─ Static Assets
```

### Export Flow

```
User clicks "Download Excel"
    ↓
GET /export.xlsx (FastAPI endpoint)
    ↓
LeadExporter.export_to_xlsx()
    ↓
Query database for leads
    ↓
Generate XLSX with openpyxl
    ↓
Return FileResponse with proper MIME type
    ↓
Browser downloads file
```

## Security Notes

### Authentication

- All UI and export routes require HTTP Basic Authentication
- Credentials configured via `APP_USERNAME` and `APP_PASSWORD` environment variables
- Uses constant-time comparison to prevent timing attacks

### Production Checklist

- [ ] Change default password in `.env`
- [ ] Use HTTPS (Caddy auto-provisions SSL with domain)
- [ ] Set strong `POSTGRES_PASSWORD`
- [ ] Review firewall rules (ports 22, 80, 443 only)
- [ ] Enable automatic backups (see `scripts/setup_cron_backups.sh`)

## Development

### Adding New UI Pages

1. Create template in `src/scrapper/web/templates/`
2. Add route in `src/scrapper/web/app.py`
3. Update navigation in `dashboard.html`

### Modifying Excel Export

Edit `src/scrapper/export/exporter.py`:
- `export_to_xlsx()` method for main logic
- Adjust column order, formatting, or add new fields

### Styling

CSS is inline in `dashboard.html` for simplicity. For more complex UIs, consider:
- Moving styles to `src/scrapper/web/static/style.css`
- Using a CSS framework (Tailwind, Bootstrap)

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Jinja2 Templates](https://jinja.palletsprojects.com/)
- [openpyxl Documentation](https://openpyxl.readthedocs.io/)
- [Main README](../README.md)
- [Production Deployment](../README_PRODUCTION.md)
