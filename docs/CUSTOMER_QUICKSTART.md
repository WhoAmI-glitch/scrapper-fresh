# Customer Quick Start Guide

Welcome to Scrapper! This guide will help you use the API to discover, enrich, and export leads.

---

## Quick Reference

**Your API:**
```
https://scrapper.yourdomain.com
```

**Interactive Docs:**
```
https://scrapper.yourdomain.com/docs
```

**Authentication:**
- All endpoints (except `/health` and `/docs`) require HTTP Basic Authentication
- Username and password provided by your administrator

---

## Endpoints Overview

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | No | Check system health |
| `/stats` | GET | Yes | View pipeline statistics |
| `/runs/discover` | POST | Yes | Trigger candidate discovery |
| `/runs/enrich` | POST | Yes | Check enrichment status |
| `/export` | GET | Yes | Download leads as CSV |
| `/docs` | GET | No | Interactive API documentation |

---

## Basic Usage

### 1. Health Check (No Auth)

Check if the service is running:

```bash
curl https://scrapper.yourdomain.com/health
```

**Response:**
```json
{
  "status": "ok",
  "database": "ok",
  "timestamp": "2024-02-13T22:30:00.123456"
}
```

---

### 2. View Statistics

See current pipeline status:

```bash
curl -u username:password https://scrapper.yourdomain.com/stats
```

**Example response:**
```json
{
  "queue_stats": {
    "NEW": 5,
    "FETCHING": 2,
    "DONE": 103,
    "FAILED": 1
  },
  "candidates_by_source": {
    "fake": 8,
    "yandex_maps": 100
  },
  "total_leads": 103,
  "total_raw_pages": 103
}
```

**What it means:**
- `NEW`: Tasks waiting to be processed
- `FETCHING`: Tasks currently being processed
- `DONE`: Tasks completed successfully
- `FAILED`: Tasks that failed (will retry)
- `total_leads`: Number of enriched leads ready for export

---

### 3. Trigger Discovery

Discover new candidates from a source:

```bash
curl -X POST -u username:password \
  https://scrapper.yourdomain.com/runs/discover \
  -H "Content-Type: application/json" \
  -d '{
    "source": "fake",
    "create_tasks": true
  }'
```

**Parameters:**
- `source` (required): Discovery source name
  - `"fake"` - test data (8 candidates)
  - `"yandex_maps"` - Yandex Maps scraper (if implemented)
  - `"government_registry"` - Government data (if implemented)
- `create_tasks` (optional): Create enrichment tasks automatically (default: true)

**Response:**
```json
{
  "candidates_discovered": 8,
  "tasks_created": 8,
  "queue_stats": {
    "NEW": 8
  }
}
```

**What happens next:**
- Candidates are saved to database
- Enrichment tasks are created automatically
- Background worker starts processing tasks
- You can check progress with `/stats`

---

### 4. Check Enrichment Status

See how many tasks are queued:

```bash
curl -X POST -u username:password \
  https://scrapper.yourdomain.com/runs/enrich
```

**Response:**
```json
{
  "tasks_queued": 5,
  "queue_stats": {
    "NEW": 5,
    "FETCHING": 2,
    "DONE": 103
  }
}
```

---

### 5. Export Leads

Download all enriched leads as CSV:

```bash
curl -u username:password \
  https://scrapper.yourdomain.com/export \
  -o leads.csv
```

**Output file:** `leads.csv`

**CSV columns:**
```csv
company_name,inn,company_name_short,legal_address,site,phone,email,director_name,okved,registration_date,revenue_2023,staff_count
```

**Example:**
```csv
company_name,inn,company_name_short,legal_address,site,phone,email,director_name,okved,registration_date,revenue_2023,staff_count
ООО "Строй-Инвест",7701234567,Строй-Инвест,"г. Москва, ул. Ленина, д. 1",http://example.com,+7-495-123-4567,info@example.com,Иванов И.И.,41.20,2015-03-15,50000000,25
```

---

## Complete Workflow Example

### Scenario: Discover and export new leads

```bash
# 1. Check current stats
curl -u username:password https://scrapper.yourdomain.com/stats | jq

# Output:
# {
#   "queue_stats": {"NEW": 0, "DONE": 0},
#   "total_leads": 0
# }

# 2. Trigger discovery
curl -X POST -u username:password \
  https://scrapper.yourdomain.com/runs/discover \
  -H "Content-Type: application/json" \
  -d '{"source": "fake", "create_tasks": true}' | jq

# Output:
# {
#   "candidates_discovered": 8,
#   "tasks_created": 8,
#   "queue_stats": {"NEW": 8}
# }

# 3. Wait for worker to process (typically 1-5 minutes for 8 tasks)
sleep 60

# 4. Check progress
curl -u username:password https://scrapper.yourdomain.com/stats | jq

# Output:
# {
#   "queue_stats": {"NEW": 0, "DONE": 8},
#   "total_leads": 8
# }

# 5. Export leads
curl -u username:password \
  https://scrapper.yourdomain.com/export \
  -o leads_$(date +%Y%m%d).csv

# 6. View exported file
cat leads_20240213.csv
```

---

## Using the Interactive API Docs

The easiest way to test the API is using the built-in Swagger UI:

1. **Open in browser:**
   ```
   https://scrapper.yourdomain.com/docs
   ```

2. **Authenticate:**
   - Click the green "Authorize" button at the top right
   - Enter your username and password
   - Click "Authorize"

3. **Try endpoints:**
   - Expand any endpoint (e.g., `POST /runs/discover`)
   - Click "Try it out"
   - Fill in parameters
   - Click "Execute"
   - View response

---

## Advanced Usage

### Using with Python

```python
import requests
from requests.auth import HTTPBasicAuth

API_URL = "https://scrapper.yourdomain.com"
USERNAME = "your-username"
PASSWORD = "your-password"

auth = HTTPBasicAuth(USERNAME, PASSWORD)

# 1. Check stats
response = requests.get(f"{API_URL}/stats", auth=auth)
stats = response.json()
print(f"Total leads: {stats['total_leads']}")

# 2. Trigger discovery
response = requests.post(
    f"{API_URL}/runs/discover",
    auth=auth,
    json={"source": "fake", "create_tasks": True}
)
result = response.json()
print(f"Discovered: {result['candidates_discovered']} candidates")

# 3. Wait for processing
import time
time.sleep(60)

# 4. Export leads
response = requests.get(f"{API_URL}/export", auth=auth)
with open("leads.csv", "wb") as f:
    f.write(response.content)
print("Leads exported to leads.csv")
```

---

### Using with JavaScript/Node.js

```javascript
const API_URL = "https://scrapper.yourdomain.com";
const USERNAME = "your-username";
const PASSWORD = "your-password";

const auth = Buffer.from(`${USERNAME}:${PASSWORD}`).toString('base64');
const headers = {
  'Authorization': `Basic ${auth}`,
  'Content-Type': 'application/json'
};

// 1. Check stats
const statsResponse = await fetch(`${API_URL}/stats`, { headers });
const stats = await statsResponse.json();
console.log(`Total leads: ${stats.total_leads}`);

// 2. Trigger discovery
const discoverResponse = await fetch(`${API_URL}/runs/discover`, {
  method: 'POST',
  headers,
  body: JSON.stringify({ source: "fake", create_tasks: true })
});
const result = await discoverResponse.json();
console.log(`Discovered: ${result.candidates_discovered} candidates`);

// 3. Export leads
const exportResponse = await fetch(`${API_URL}/export`, { headers });
const blob = await exportResponse.blob();
// Save to file or process data
```

---

### Scheduled Discovery (Cron)

Run discovery automatically every day:

```bash
# Edit crontab
crontab -e

# Add line (runs daily at 9 AM):
0 9 * * * curl -X POST -u username:password https://scrapper.yourdomain.com/runs/discover -H "Content-Type: application/json" -d '{"source":"fake","create_tasks":true}' >> /var/log/scrapper_discovery.log 2>&1
```

---

## Monitoring

### Check Worker Activity

See what the worker is doing:

```bash
# From VPS (requires SSH access)
ssh scrapper-user@your-vps
cd ~/scrapper
docker compose logs -f worker
```

**Healthy output:**
```
[2024-02-13 22:30:05] Starting worker loop (poll_interval=5s, batch_size=10)
[2024-02-13 22:30:10] Claimed 3 tasks from queue
[2024-02-13 22:30:11] Task 123 → DONE (company: Test LLC)
[2024-02-13 22:30:12] Task 124 → DONE (company: Example Ltd)
```

### Check API Logs

```bash
docker compose logs -f api
```

---

## Troubleshooting

### Issue: 401 Unauthorized

**Problem:** Wrong username or password

**Solution:**
```bash
# Verify credentials with admin
# Ensure no typos in password
curl -u correct-username:correct-password https://scrapper.yourdomain.com/stats
```

---

### Issue: Discovery returns 0 candidates

**Problem:** No new candidates found by the source

**Possible causes:**
1. Source has no new data
2. Candidates already exist in database (duplicates filtered)
3. Source is not configured correctly

**Solution:**
- Check logs: `docker compose logs worker`
- Try different source: `{"source": "yandex_maps"}`
- Contact admin if issue persists

---

### Issue: Tasks stuck in NEW state

**Problem:** Worker not processing tasks

**Solution:**
1. Check worker is running:
   ```bash
   docker compose ps worker
   ```

2. Restart worker:
   ```bash
   docker compose restart worker
   ```

3. Contact admin if issue persists

---

### Issue: Export returns empty CSV

**Problem:** No leads have been enriched yet

**Solution:**
1. Check stats:
   ```bash
   curl -u user:pass https://scrapper.yourdomain.com/stats
   ```

2. If `total_leads: 0`, trigger discovery:
   ```bash
   curl -X POST -u user:pass https://scrapper.yourdomain.com/runs/discover \
     -H "Content-Type: application/json" \
     -d '{"source": "fake", "create_tasks": true}'
   ```

3. Wait for worker to process (check stats periodically)

---

## Best Practices

### 1. Check Stats Before Discovery

Always check current state before triggering new discovery:

```bash
curl -u user:pass https://scrapper.yourdomain.com/stats
```

This prevents queuing too many tasks at once.

---

### 2. Monitor Queue Depth

Ideal queue depth: 10-100 tasks

- **Too few** (0-5): Worker idle, discover more
- **Good** (10-100): Healthy processing
- **Too many** (1000+): May slow down, wait before discovering more

---

### 3. Export Regularly

Export leads at least weekly to avoid data loss:

```bash
# Export with timestamp
curl -u user:pass https://scrapper.yourdomain.com/export \
  -o leads_$(date +%Y%m%d).csv
```

---

### 4. Use Descriptive Source Names

When implementing custom sources, use clear names:

```bash
# Good
{"source": "yandex_maps_moscow"}
{"source": "government_registry_contractors"}

# Bad
{"source": "source1"}
{"source": "test"}
```

---

## Rate Limits and Performance

### Current Configuration

- **Worker poll interval**: 5 seconds
- **Batch size**: 10 tasks per poll
- **Max throughput**: ~720 tasks/hour (1 worker)

### Scaling

To process more tasks faster, contact admin to:
- Increase worker instances (2-5 workers)
- Adjust batch size (10-50 tasks)

**Example:** 3 workers = ~2,160 tasks/hour

---

## Data Retention

- **Raw pages**: Stored indefinitely in `data/raw/`
- **Leads**: Stored indefinitely in database
- **Database backups**: Kept for 7 days (rotated daily)

To clear old data, contact admin.

---

## Security Notes

1. **Never share credentials** - each user should have unique login
2. **Use HTTPS** - always access via `https://`, never `http://`
3. **Secure API access** - do not embed credentials in client-side code
4. **Export sensitivity** - CSV files contain business data, handle securely

---

## Support

For issues or questions:

1. Check this guide
2. Review API docs: `https://scrapper.yourdomain.com/docs`
3. Contact system administrator
4. Review logs (if SSH access): `docker compose logs -f worker`

---

## Example Scripts

### Daily Discovery + Export

```bash
#!/usr/bin/env bash
set -euo pipefail

API_URL="https://scrapper.yourdomain.com"
USERNAME="your-username"
PASSWORD="your-password"

# 1. Trigger discovery
echo "Triggering discovery..."
curl -X POST -u "$USERNAME:$PASSWORD" \
  "$API_URL/runs/discover" \
  -H "Content-Type: application/json" \
  -d '{"source": "fake", "create_tasks": true}'

# 2. Wait for processing (adjust time based on expected candidates)
echo "Waiting for processing..."
sleep 300  # 5 minutes

# 3. Export leads
echo "Exporting leads..."
curl -u "$USERNAME:$PASSWORD" \
  "$API_URL/export" \
  -o "leads_$(date +%Y%m%d_%H%M%S).csv"

echo "Done!"
```

---

**Happy scraping!** 🚀
