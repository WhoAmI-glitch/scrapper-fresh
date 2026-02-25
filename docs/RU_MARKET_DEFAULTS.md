# Russian Market Default Configuration

Conservative defaults and recommendations for operating Scrapper in the Russian market.

---

## Overview

This document provides recommended configuration values optimized for:
- **RU market characteristics**: Network latency, data sources, regulatory requirements
- **Conservative resource usage**: Avoid overwhelming targets or infrastructure
- **Reliability**: Stable long-term operation with minimal intervention

---

## Environment Variables

### Core Settings

```bash
# ============================================================================
# CONSERVATIVE DEFAULTS FOR RU MARKET
# ============================================================================

# Domain (set to your actual domain for HTTPS)
DOMAIN=scrapper.yourdomain.com

# Database (use strong password)
DATABASE_URL=postgresql://postgres:STRONG_PASSWORD@postgres:5432/scrapper
POSTGRES_PASSWORD=STRONG_PASSWORD

# Authentication (use strong password)
APP_USERNAME=admin
APP_PASSWORD=STRONG_PASSWORD

# Worker Configuration
WORKER_POLL_INTERVAL=5          # Poll every 5 seconds (conservative)
TASK_BATCH_SIZE=10              # Process 10 tasks per batch (conservative)
MAX_TASK_ATTEMPTS=3             # Retry failed tasks 3 times

# Fetch Timeouts (RU network latency)
FETCH_TIMEOUT=30                # 30 seconds for page fetch (allows for slow responses)
CONNECT_TIMEOUT=10              # 10 seconds to establish connection

# Connection Pool
DB_MIN_POOL_SIZE=2              # Minimum connections (conservative)
DB_MAX_POOL_SIZE=10             # Maximum connections (prevents overload)

# Logging
LOG_LEVEL=INFO                  # INFO level (not DEBUG, to reduce log volume)

# Data Directories
RAW_DATA_DIR=data/raw           # Store raw HTML snapshots
EXPORT_DIR=data/exports         # Store CSV exports

# ============================================================================
# OPTIONAL: EXTERNAL SERVICES
# ============================================================================

# Bright Data Web Unlocker (for production scraping)
# Only set if you have an active subscription
BRIGHTDATA_PROXY_URL=

# Claude API (for LLM fallback parsing)
# Only set if you want AI-powered parsing as fallback
CLAUDE_API_KEY=

# ============================================================================
# PRODUCTION NOTES
# ============================================================================
# 1. Generate strong passwords: openssl rand -base64 32
# 2. Never commit this file to git (use .env.production.example as template)
# 3. Keep these values conservative to ensure stable operation
# 4. Monitor performance and adjust only if needed
# ============================================================================
```

---

## Worker Scaling Recommendations

### Small Deployment (100-500 candidates/day)

**Configuration:**
```bash
WORKER_POLL_INTERVAL=5
TASK_BATCH_SIZE=10
```

**Docker Compose:**
```yaml
# docker-compose.yml
services:
  worker:
    # No scaling needed - 1 worker sufficient
```

**Throughput:**
- 1 worker: ~720 tasks/hour
- Typical processing time: 5-10 seconds per task
- Daily capacity: ~5,000 tasks/day

**Use case:**
- Small-scale lead generation
- Testing and development
- Limited discovery sources

---

### Medium Deployment (500-2000 candidates/day)

**Configuration:**
```bash
WORKER_POLL_INTERVAL=5
TASK_BATCH_SIZE=15              # Slightly increased
```

**Docker Compose:**
```bash
# Scale to 2-3 workers
docker compose up -d --scale worker=3
```

**Throughput:**
- 3 workers: ~2,160 tasks/hour
- Daily capacity: ~15,000 tasks/day

**Use case:**
- Active lead generation
- Multiple discovery sources
- Regular enrichment runs

---

### Large Deployment (2000+ candidates/day)

**Configuration:**
```bash
WORKER_POLL_INTERVAL=3          # Faster polling
TASK_BATCH_SIZE=20              # Larger batches
```

**Docker Compose:**
```bash
# Scale to 5 workers
docker compose up -d --scale worker=5
```

**Throughput:**
- 5 workers: ~3,600 tasks/hour
- Daily capacity: ~25,000 tasks/day

**VPS Requirements:**
- **Minimum**: 2 vCPU, 4GB RAM
- **Recommended**: 4 vCPU, 8GB RAM

**Use case:**
- High-volume lead generation
- Multiple concurrent discovery sources
- Enterprise deployment

---

## Network Configuration for RU Market

### Fetch Timeouts

Russian websites and data sources may have variable response times. Recommended timeouts:

```bash
# Conservative (default)
FETCH_TIMEOUT=30
CONNECT_TIMEOUT=10

# For known-slow sources (government registries, etc.)
FETCH_TIMEOUT=60
CONNECT_TIMEOUT=15

# For fast sources (APIs, well-optimized sites)
FETCH_TIMEOUT=15
CONNECT_TIMEOUT=5
```

**Rationale:**
- Government websites: often slow, 30-60s timeout needed
- Yandex Maps: typically fast, 15s sufficient
- Network latency: Moscow-Helsinki ~50ms, Moscow-Europe ~100ms

---

### Retry Strategy

```bash
MAX_TASK_ATTEMPTS=3             # Retry up to 3 times

# Built-in retry delays (exponential backoff)
# Attempt 1: immediate
# Attempt 2: after 60 seconds
# Attempt 3: after 180 seconds (3 minutes)
```

**Rationale:**
- Temporary network issues: common in RU
- Server-side errors: may resolve after delay
- Rate limiting: exponential backoff prevents hammering

---

## Database Configuration

### Connection Pool

```bash
DB_MIN_POOL_SIZE=2              # Minimum connections (always open)
DB_MAX_POOL_SIZE=10             # Maximum connections (prevents overload)
```

**Sizing guidance:**
- 1 worker: min=2, max=5
- 3 workers: min=2, max=10
- 5 workers: min=5, max=15

**Rationale:**
- PostgreSQL can handle 100+ connections, but conservatively limit to prevent resource exhaustion
- Each worker needs 1-2 connections
- API needs 2-5 connections (depending on concurrent requests)

---

## Storage Configuration

### Raw Data Retention

```bash
RAW_DATA_DIR=data/raw           # Store HTML snapshots
```

**Recommendations:**
- **Keep indefinitely**: Useful for re-parsing if parser logic changes
- **Disk usage**: ~50-500KB per page
- **Estimation**: 1000 pages ≈ 100-500MB

**Cleanup (optional):**
```bash
# Delete raw pages older than 90 days
find data/raw -type f -name "*.html" -mtime +90 -delete
```

---

### Backup Retention

```bash
BACKUP_KEEP_DAYS=7              # Keep daily backups for 7 days
```

**Recommendations by scale:**
- **Small**: 7 days (default)
- **Medium**: 14 days
- **Large**: 30 days + monthly archives

**Backup size estimation:**
- Empty database: ~1MB
- 1,000 leads: ~5-10MB
- 10,000 leads: ~50-100MB
- 100,000 leads: ~500MB-1GB

---

## Rate Limiting Considerations

### For Public Sources (Yandex Maps, etc.)

**Conservative approach (default):**
```bash
WORKER_POLL_INTERVAL=5          # Process batches every 5 seconds
TASK_BATCH_SIZE=10              # 10 tasks per batch
# Effective rate: 2 requests/second
```

**Rationale:**
- Avoids triggering rate limits
- Appears as organic traffic
- Sustainable long-term
- No need for delays between requests (worker manages this via polling)

**⚠️ WARNING:**
- Do NOT reduce `WORKER_POLL_INTERVAL` below 3 seconds without careful testing
- Do NOT increase `TASK_BATCH_SIZE` above 20 without monitoring for rate limit errors
- Public sources may block IPs if request rate is too high

---

### For Paid Services (Bright Data, etc.)

If using Bright Data Web Unlocker:

```bash
BRIGHTDATA_PROXY_URL=your-proxy-url
FETCH_TIMEOUT=60                # Proxy can be slower
```

**Recommendations:**
- No artificial rate limiting needed (service handles this)
- Monitor quota usage to avoid overage charges
- Adjust batch size based on plan limits

---

## Logging Configuration

```bash
LOG_LEVEL=INFO                  # Default: INFO
```

**Log levels:**
- `DEBUG`: Verbose (use for troubleshooting only)
- `INFO`: Normal operation (recommended for production)
- `WARNING`: Only warnings and errors
- `ERROR`: Only errors

**Disk usage:**
- `INFO` level: ~10-50MB/day (1000 tasks/day)
- `DEBUG` level: ~100-500MB/day (very verbose)

**Log rotation (recommended):**
```bash
# Add to crontab
0 0 * * * find /home/scrapper/scrapper/logs -name "*.log" -mtime +14 -delete
```

---

## VPS Requirements by Scale

### Small Scale (1 worker)

```
CPU: 1 vCPU
RAM: 1GB
Disk: 25GB SSD
Bandwidth: 1TB/month
Cost: $5-7/month (Hetzner CX11)
```

**Suitable for:**
- 100-500 tasks/day
- Testing and development
- Limited budget

---

### Medium Scale (3 workers)

```
CPU: 2 vCPU
RAM: 2GB
Disk: 50GB SSD
Bandwidth: 1TB/month
Cost: $10-15/month (Hetzner CX21)
```

**Suitable for:**
- 500-2000 tasks/day
- Production deployment
- Multiple sources

---

### Large Scale (5 workers)

```
CPU: 4 vCPU
RAM: 4-8GB
Disk: 100GB SSD
Bandwidth: 2TB/month
Cost: $20-40/month (Hetzner CX31/CX41)
```

**Suitable for:**
- 2000+ tasks/day
- Enterprise deployment
- High-volume scraping

---

## Security Defaults

### Password Strength

```bash
# Generate strong passwords
openssl rand -base64 32

# Example output:
# rK5tX8fJ2mP9wQ4nL7cV3hB6zY1sA0uD5eR8tG4kI6j=
```

**Requirements:**
- Minimum 20 characters
- Mix of letters, numbers, symbols
- Never use default passwords in production

---

### Firewall Configuration

```bash
# UFW (configured by bootstrap script)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (Caddy redirects to HTTPS)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw default deny incoming
```

**Important:**
- PostgreSQL port 5432: NOT exposed (Docker network only)
- API port 8000: NOT exposed (Caddy reverse proxy only)

---

## Monitoring Defaults

### External Health Checks

**Recommended interval:**
```
Check frequency: 5 minutes
Alert threshold: 2 consecutive failures
```

**Services:**
- UptimeRobot (free tier: 5-minute checks)
- Healthchecks.io (free tier: 1-minute checks)

---

### Log Monitoring

**Error threshold:**
```bash
# Alert if more than 10 errors in last hour
docker compose logs worker --since 1h | grep ERROR | wc -l
```

**Recommended:** Set up daily summary email with error count

---

## Adjustment Guidelines

### When to Increase Worker Scale

**Indicators:**
- Queue depth > 100 tasks consistently
- Tasks taking > 1 hour to process
- New candidates not being enriched within 24 hours

**Action:**
```bash
# Scale to 3 workers
docker compose up -d --scale worker=3

# Monitor for 24 hours
docker compose logs worker | grep "Claimed"
```

---

### When to Increase Batch Size

**Indicators:**
- Worker logs show frequent "No tasks in queue"
- Queue depth < 10 tasks consistently
- Worker CPU usage < 20%

**Action:**
```bash
# Edit .env
TASK_BATCH_SIZE=15  # Increase from 10 to 15

# Restart worker
docker compose restart worker
```

---

### When to Decrease Batch Size

**Indicators:**
- High memory usage (> 80%)
- Frequent task failures
- Database connection errors

**Action:**
```bash
# Edit .env
TASK_BATCH_SIZE=5   # Decrease from 10 to 5

# Restart worker
docker compose restart worker
```

---

## Performance Monitoring

### Key Metrics to Track

```bash
# 1. Queue depth
curl -u user:pass https://scrapper.yourdomain.com/stats | jq '.queue_stats'

# 2. Worker throughput (tasks/hour)
docker compose logs worker --since 1h | grep "Task.*DONE" | wc -l

# 3. Error rate
docker compose logs worker --since 1h | grep ERROR | wc -l

# 4. Disk usage
df -h | grep /dev/sda1
du -sh data/ backups/
```

**Healthy values:**
- Queue depth: 0-50 (steady state)
- Worker throughput: > 10 tasks/hour per worker
- Error rate: < 5% of total tasks
- Disk usage: < 70%

---

## RU Market Specific Considerations

### 1. Network Latency

**Problem:** Variable latency to RU data sources

**Solution:**
- Use Hetzner Helsinki datacenter (lowest latency to RU)
- Set conservative timeouts (30s+)
- Implement retry logic (default: 3 attempts)

---

### 2. Data Source Reliability

**Problem:** Government registries, public databases may have downtime

**Solution:**
- Retry with exponential backoff (built-in)
- Don't fail entire batch on single failure (per-task error isolation)
- Monitor failed tasks: `SELECT COUNT(*) FROM enrichment_tasks WHERE state = 'FAILED'`

---

### 3. Character Encoding

**Problem:** Cyrillic text requires UTF-8 encoding

**Solution:**
- All code already uses UTF-8 (Python 3.11 default)
- PostgreSQL configured for UTF-8
- CSV exports include UTF-8 BOM for Excel compatibility

---

### 4. Legal Compliance

**Reminder:**
- Scrape only public data
- Respect robots.txt (if applicable)
- Do not use for spam or unauthorized marketing
- Comply with GDPR/local data protection laws

---

## Summary of Conservative Defaults

```bash
# Copy these to your .env file for conservative RU market operation
WORKER_POLL_INTERVAL=5
TASK_BATCH_SIZE=10
MAX_TASK_ATTEMPTS=3
FETCH_TIMEOUT=30
CONNECT_TIMEOUT=10
DB_MIN_POOL_SIZE=2
DB_MAX_POOL_SIZE=10
LOG_LEVEL=INFO
BACKUP_KEEP_DAYS=7
```

**These values provide:**
- ✅ Stable operation
- ✅ Low risk of rate limiting
- ✅ Reasonable resource usage
- ✅ Good error recovery
- ✅ Suitable for most use cases

**Adjust only when:**
- Monitoring shows bottlenecks
- Scale requirements increase
- Specific sources need tuning

---

**Last updated:** 2024-02-13
**Recommended review:** Quarterly or when scale changes significantly
