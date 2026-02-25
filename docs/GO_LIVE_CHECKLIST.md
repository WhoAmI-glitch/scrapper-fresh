# Go-Live Checklist

Complete checklist for deploying Scrapper to production on a VPS.

---

## Prerequisites

### 1. VPS Requirements

- [ ] **VPS Provider**: Hetzner, DigitalOcean, Linode, Vultr, or similar
  - **Recommended**: Hetzner Helsinki (RU-friendly, low latency)
  - **Minimum**: 1 vCPU, 1GB RAM, 25GB SSD
  - **Recommended**: 2 vCPU, 2GB RAM, 50GB SSD
  - **OS**: Ubuntu 22.04 LTS or 24.04 LTS

- [ ] **VPS Access**: SSH root access with password or key

### 2. Domain Setup

- [ ] **Domain name** registered (e.g., `scrapper.yourdomain.com`)
- [ ] **DNS Access**: Ability to create A records

### 3. External Services (Optional)

- [ ] **Bright Data** account (for Web Unlocker) - if using real scraping
- [ ] **Claude API** key (for LLM fallback) - if using AI parsing

---

## Deployment Steps

### Step 1: VPS Initial Setup

```bash
# 1. SSH into VPS as root
ssh root@YOUR_VPS_IP

# 2. Download and run bootstrap script
curl -fsSL https://raw.githubusercontent.com/YOUR_ORG/scrapper/main/scripts/vps_bootstrap_ubuntu.sh | sudo bash

# OR manually:
wget https://raw.githubusercontent.com/YOUR_ORG/scrapper/main/scripts/vps_bootstrap_ubuntu.sh
chmod +x vps_bootstrap_ubuntu.sh
sudo ./vps_bootstrap_ubuntu.sh
```

**Expected output:**
```
✅ Bootstrap complete!
System info:
  - Firewall: UFW enabled (SSH: 22, HTTP: 80, HTTPS: 443)
  - Docker: Docker version 24.x.x
  - User: scrapper (in docker group)
```

**Verify:**
```bash
# Check Docker
docker --version
docker compose version

# Check firewall
sudo ufw status

# Check user
id scrapper
```

---

### Step 2: DNS Configuration

Configure your DNS provider (Namecheap, Cloudflare, etc.):

```
Type: A
Name: scrapper (or @ for root domain)
Value: YOUR_VPS_IP
TTL: 300 (5 minutes)
```

**Example:**
```
A   scrapper.yourdomain.com   →   123.45.67.89
```

**Verify DNS propagation:**
```bash
# From your local machine
dig scrapper.yourdomain.com

# Or use online tool
https://dnschecker.org
```

**Wait for DNS**: 5-30 minutes (depending on TTL)

---

### Step 3: Deploy Application

```bash
# 1. Switch to scrapper user
sudo -i -u scrapper

# 2. Clone repository
cd ~
git clone https://github.com/YOUR_ORG/scrapper.git
cd scrapper

# 3. Configure environment
cp .env.production.example .env
nano .env
```

**Required .env changes:**

```bash
# CRITICAL: Set strong passwords
POSTGRES_PASSWORD=<generate with: openssl rand -base64 32>
APP_PASSWORD=<generate with: openssl rand -base64 32>

# Authentication
APP_USERNAME=admin  # Change to your preferred username

# Domain (for HTTPS via Caddy)
DOMAIN=scrapper.yourdomain.com  # Your actual domain

# Optional: External services
BRIGHTDATA_PROXY_URL=  # Leave empty if not using
CLAUDE_API_KEY=        # Leave empty if not using
```

**Generate strong passwords:**
```bash
openssl rand -base64 32
```

```bash
# 4. Deploy
./scripts/vps_deploy.sh
```

**Expected output:**
```
✅ Deployment complete!
Application URL:
  https://scrapper.yourdomain.com
```

---

### Step 4: Verify Deployment

```bash
# 1. Quick smoke test
make smoke-test
```

**Expected output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Quick Smoke Test
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Health check
✓ Stats endpoint
✓ Docker services (4 services running)
✓ Worker activity
✓ Database connectivity

  ✅ All smoke tests passed!
```

```bash
# 2. Full production check
make production-check
```

**Expected output:**
```
✓ Health check
✓ Stats endpoint
✓ Discovery run (8 candidates)
✓ Enrichment tasks created
✓ Worker processing
✓ Export downloaded
✓ Database backup created
```

---

### Step 5: Verify HTTPS

```bash
# From your local machine
curl -I https://scrapper.yourdomain.com/health
```

**Expected output:**
```
HTTP/2 200
server: Caddy
content-type: application/json
```

**If HTTPS fails:**

```bash
# Check Caddy logs
docker compose logs caddy

# Common issues:
# 1. DNS not propagated yet → Wait 5-30 minutes
# 2. Firewall blocking ports → Check: sudo ufw status
# 3. Domain not in .env → Check: cat .env | grep DOMAIN
```

---

### Step 6: Setup Monitoring

#### A. Health Check Monitoring

Use external service to monitor `/health` endpoint:

**Recommended: UptimeRobot (Free)**
1. Go to https://uptimerobot.com
2. Create monitor:
   - **Type**: HTTP(s)
   - **URL**: `https://scrapper.yourdomain.com/health`
   - **Interval**: 5 minutes
   - **Alert**: Email when down

**Alternative: Healthchecks.io**
```bash
# Add to crontab for ping-back style monitoring
*/5 * * * * curl -fsS https://hc-ping.com/YOUR_CHECK_UUID > /dev/null
```

#### B. Log Monitoring (Optional)

```bash
# Check logs regularly
docker compose logs -f worker | grep ERROR
docker compose logs -f api | grep ERROR
```

---

### Step 7: Setup Automated Backups

```bash
# Run backup setup script
./scripts/setup_cron_backups.sh
```

**Expected output:**
```
✅ Cron backups configured!
Schedule: Daily at 2:00 AM
Retention: 7 days
```

**Verify:**
```bash
# Check cron jobs
crontab -l

# View backups
ls -lh backups/

# View backup logs
tail -f logs/backup.log
```

---

## Post-Deployment Checklist

### Security

- [ ] **Strong passwords** set in `.env` (not defaults)
- [ ] **PostgreSQL port** NOT exposed (should be commented in docker-compose.yml)
- [ ] **API port 8000** NOT exposed directly (only via Caddy)
- [ ] **Firewall** enabled: `sudo ufw status`
- [ ] **SSH root login** disabled: `grep PermitRootLogin /etc/ssh/sshd_config`
- [ ] **fail2ban** installed (optional): `sudo systemctl status fail2ban`

### Services

- [ ] **Docker running**: `docker compose ps` shows 4 services (postgres, api, worker, caddy)
- [ ] **Health check passes**: `curl https://scrapper.yourdomain.com/health`
- [ ] **HTTPS working**: Certificate shows "Issued by: Let's Encrypt"
- [ ] **Worker processing**: `docker compose logs worker | grep "Claimed"`

### Data

- [ ] **Database initialized**: `docker compose exec postgres psql -U postgres scrapper -c "\dt"`
- [ ] **Directories created**: `ls -la data/` shows `raw/` and `exports/`
- [ ] **Backups configured**: `crontab -l` shows backup job

### Monitoring

- [ ] **External monitoring** configured (UptimeRobot, etc.)
- [ ] **Backup logs** writing: `ls -lh logs/backup.log`
- [ ] **API accessible** from browser: `https://scrapper.yourdomain.com/docs`

---

## Weekly Maintenance Tasks

Run these commands weekly to ensure system health:

```bash
# 1. Full production check (includes backup)
make production-check

# 2. Check disk usage
df -h
du -sh data/ backups/

# 3. Review error logs
docker compose logs --tail 500 | grep ERROR

# 4. Check backup count
ls -1 backups/*.sql | wc -l
```

---

## What "Healthy" Looks Like

### Service Status
```bash
$ docker compose ps
NAME                STATUS       PORTS
scrapper-api        Up (healthy)
scrapper-caddy      Up           80/tcp, 443/tcp
scrapper-postgres   Up (healthy)
scrapper-worker     Up
```

### Health Endpoint
```bash
$ curl https://scrapper.yourdomain.com/health
{
  "status": "ok",
  "database": "ok",
  "timestamp": "2024-02-13T22:30:00.123456"
}
```

### Worker Logs
```bash
$ docker compose logs worker --tail 10
[2024-02-13 22:30:05] Starting worker loop (poll_interval=5s, batch_size=10)
[2024-02-13 22:30:10] Claimed 3 tasks from queue
[2024-02-13 22:30:11] Task 123 → DONE (company: Test LLC)
[2024-02-13 22:30:12] Task 124 → DONE (company: Example Ltd)
```

### Firewall
```bash
$ sudo ufw status
Status: active
To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
```

---

## Troubleshooting

### Issue: HTTPS not working

**Symptoms:**
- `curl https://scrapper.yourdomain.com` fails with certificate error
- Caddy logs show "acme: error obtaining certificate"

**Solutions:**
1. **Check DNS**: `dig scrapper.yourdomain.com` → Should return VPS IP
2. **Check firewall**: `sudo ufw status` → 80/443 should be allowed
3. **Check domain in .env**: `cat .env | grep DOMAIN`
4. **Wait for DNS propagation**: Can take 5-30 minutes
5. **Check Caddy logs**: `docker compose logs caddy | grep acme`

---

### Issue: Worker not processing tasks

**Symptoms:**
- Stats show tasks stuck in NEW state
- Worker logs show no "Claimed" messages

**Solutions:**
1. **Check worker running**: `docker compose ps worker`
2. **Check worker logs**: `docker compose logs worker --tail 50`
3. **Check database connection**: `docker compose logs postgres`
4. **Restart worker**: `docker compose restart worker`
5. **Check tasks exist**: `make db-shell` → `SELECT COUNT(*) FROM enrichment_tasks WHERE state = 'NEW';`

---

### Issue: API returns 500 errors

**Symptoms:**
- `/health` returns 500
- API logs show database errors

**Solutions:**
1. **Check API logs**: `docker compose logs api --tail 50`
2. **Check database**: `docker compose ps postgres`
3. **Check DATABASE_URL**: `docker compose exec api env | grep DATABASE_URL`
4. **Restart services**: `docker compose restart`

---

## Emergency Procedures

### Restore from Backup

```bash
# 1. Stop services
docker compose down

# 2. Start only database
docker compose up -d postgres

# 3. Wait for postgres to be ready
sleep 10

# 4. Restore
docker compose exec -T postgres psql -U postgres scrapper < backups/scrapper_YYYY-MM-DD_HHMMSS.sql

# 5. Restart all services
docker compose up -d

# 6. Verify
make smoke-test
```

### Rollback Deployment

```bash
# 1. Check git history
git log --oneline -5

# 2. Rollback to previous version
git checkout <previous-commit-hash>

# 3. Redeploy
./scripts/vps_deploy.sh
```

---

## Success Criteria

✅ **Deployment is successful when:**

1. All 4 Docker services running (postgres, api, worker, caddy)
2. Health check returns 200 OK via HTTPS
3. Worker logs show task processing activity
4. API accessible from browser with valid HTTPS certificate
5. Stats endpoint returns pipeline metrics (with auth)
6. Smoke test passes
7. Production check passes
8. Daily backups running (check `crontab -l`)
9. External monitoring configured and receiving pings

---

## Customer Handoff

When handing off to customer, provide:

1. **Credentials**:
   ```
   URL: https://scrapper.yourdomain.com
   Username: <APP_USERNAME from .env>
   Password: <APP_PASSWORD from .env>
   ```

2. **Documentation**:
   - `docs/CUSTOMER_QUICKSTART.md` - How to use API
   - API docs: `https://scrapper.yourdomain.com/docs`

3. **Monitoring**:
   - UptimeRobot login (or other monitoring service)
   - How to check logs: `docker compose logs -f worker`

4. **Support**:
   - How to export leads: `curl -u user:pass https://scrapper.yourdomain.com/export -o leads.csv`
   - How to check stats: `curl -u user:pass https://scrapper.yourdomain.com/stats`
   - How to trigger discovery: See CUSTOMER_QUICKSTART.md

---

## Go-Live Commands (Copy-Paste)

```bash
# On VPS (as root)
curl -fsSL https://raw.githubusercontent.com/YOUR_ORG/scrapper/main/scripts/vps_bootstrap_ubuntu.sh | sudo bash

# Switch to scrapper user
sudo -i -u scrapper

# Clone and configure
cd ~
git clone https://github.com/YOUR_ORG/scrapper.git
cd scrapper
cp .env.production.example .env
nano .env  # Set DOMAIN, passwords

# Deploy
./scripts/vps_deploy.sh

# Setup backups
./scripts/setup_cron_backups.sh

# Verify
make production-check

# From local machine - verify HTTPS
curl -I https://scrapper.yourdomain.com/health
```

---

**Status**: Ready for production deployment ✅
