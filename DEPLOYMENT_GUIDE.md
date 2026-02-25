# Production Deployment Guide

## 🎯 Target

- **VPS IP:** 89.167.62.47
- **OS:** Ubuntu 22.04
- **Repository:** https://github.com/WhoAmI-glitch/scrapper
- **Branch:** main

---

## 📋 Prerequisites

Before deploying, ensure you have:

1. SSH access to the VPS (root or sudo user)
2. Production credentials ready (.env.production.example)

---

## 🚀 Automated Deployment (Recommended)

### Option 1: Using deployment script

```bash
# Make script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

The script will:
- ✅ Install Docker, Docker Compose, Git
- ✅ Configure firewall (UFW)
- ✅ Clone repository
- ✅ Deploy .env file
- ✅ Start all services
- ✅ Verify deployment

---

## 🔧 Manual Deployment (Step-by-Step)

If the automated script fails or you prefer manual control:

### Step 1: SSH into VPS

```bash
ssh root@89.167.62.47
```

### Step 2: Install Docker

```bash
# Update package list
apt-get update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# Enable Docker
systemctl enable docker
systemctl start docker

# Verify installation
docker --version
docker compose version
```

### Step 3: Install Git

```bash
apt-get install -y git
git --version
```

### Step 4: Configure Firewall

```bash
# Install UFW
apt-get install -y ufw

# Reset to defaults
ufw --force reset

# Default policies
ufw default deny incoming
ufw default allow outgoing

# Allow required ports
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'

# Enable firewall
ufw --force enable

# Check status
ufw status verbose
```

**Expected output:**
```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW IN    Anywhere                   # SSH
80/tcp                     ALLOW IN    Anywhere                   # HTTP
443/tcp                    ALLOW IN    Anywhere                   # HTTPS
```

### Step 5: Clone Repository

```bash
# Create app directory
mkdir -p /opt/scrapper
cd /opt/scrapper

# Clone repository
git clone -b main https://github.com/WhoAmI-glitch/scrapper.git .

# Verify
git log -1 --oneline
ls -la
```

### Step 6: Configure Environment

```bash
# Copy production config
cp .env.production.example .env

# IMPORTANT: Edit .env if needed
nano .env
```

**Verify critical settings:**
```bash
cat .env | grep -E "(DOMAIN|APP_PASSWORD|POSTGRES_PASSWORD)"
```

**Expected:**
```
DOMAIN=89.167.62.47
APP_PASSWORD=Katrin814!
POSTGRES_PASSWORD=OaxuBSvqAXzFFHuquvDkDHnHHWnqRkRu
```

### Step 7: Create Data Directories

```bash
# Create directories
mkdir -p data/raw
mkdir -p data/exports

# Set permissions
chmod -R 755 data

# Verify
ls -la data/
```

### Step 8: Start Services

```bash
# Pull images
docker compose pull

# Build and start
docker compose up -d --build

# Wait for startup
sleep 15

# Check status
docker compose ps
```

**Expected output:**
```
NAME                IMAGE                COMMAND                  SERVICE    CREATED          STATUS                    PORTS
scrapper-api        scrapper-api         "uvicorn scrapper.we…"   api        30 seconds ago   Up 28 seconds (healthy)   8000/tcp
scrapper-caddy      caddy:2-alpine       "caddy run --config …"   caddy      30 seconds ago   Up 28 seconds             0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
scrapper-postgres   postgres:14-alpine   "docker-entrypoint.s…"   postgres   30 seconds ago   Up 29 seconds (healthy)   5432/tcp
scrapper-worker     scrapper-worker      "scrapper-worker"        worker     30 seconds ago   Up 28 seconds             8000/tcp
```

### Step 9: Initialize Database

```bash
# Check if database is initialized
docker compose exec postgres psql -U postgres -d scrapper -c "\dt"
```

**If tables don't exist:**
```bash
# Execute schema
docker compose exec -T postgres psql -U postgres -d scrapper < src/scrapper/db/schema.sql
```

### Step 10: Verify Deployment

```bash
# Check logs
docker compose logs api
docker compose logs worker

# Check health from inside VPS
curl http://localhost/health

# Check UI
curl -u admin:Katrin814! http://localhost/ui/ | head -20
```

---

## ✅ External Verification

**From your local machine or any external location:**

### 1. Health Check

```bash
curl http://89.167.62.47/health
```

**Expected:**
```json
{
  "status": "ok",
  "database": "ok",
  "timestamp": "2026-02-15T01:23:45.123456"
}
```

### 2. UI Access

```bash
curl -u admin:Katrin814! http://89.167.62.47/ui/ | grep "LeadFlow"
```

**Or open in browser:**
```
http://89.167.62.47/ui/
Username: admin
Password: Katrin814!
```

### 3. API Stats

```bash
curl -u admin:Katrin814! http://89.167.62.47/stats
```

### 4. CSV Export

```bash
curl -u admin:Katrin814! http://89.167.62.47/export -o leads.csv
```

### 5. Excel Export

```bash
curl -u admin:Katrin814! http://89.167.62.47/export.xlsx -o leads.xlsx
```

---

## 🔍 Troubleshooting

### Issue: Services not starting

```bash
# Check logs
docker compose logs

# Restart services
docker compose restart

# Rebuild if needed
docker compose up -d --build
```

### Issue: Database connection error

```bash
# Check postgres health
docker compose exec postgres pg_isready -U postgres

# Check database exists
docker compose exec postgres psql -U postgres -l

# Re-initialize schema
docker compose exec -T postgres psql -U postgres -d scrapper < src/scrapper/db/schema.sql
```

### Issue: Cannot access from outside

```bash
# Check firewall
ufw status verbose

# Check if ports are listening
netstat -tulpn | grep -E ':(80|443)'

# Check Caddy logs
docker compose logs caddy

# Test locally first
curl http://localhost/health
```

### Issue: 502 Bad Gateway

```bash
# Check API container health
docker compose ps api

# Check API logs
docker compose logs api

# Restart API
docker compose restart api
```

---

## 📊 Monitoring Commands

### View all logs (real-time)

```bash
cd /opt/scrapper
docker compose logs -f
```

### View specific service logs

```bash
docker compose logs -f api
docker compose logs -f worker
docker compose logs -f postgres
docker compose logs -f caddy
```

### Check container status

```bash
docker compose ps
```

### Check resource usage

```bash
docker stats
```

### Check disk usage

```bash
df -h
du -sh /opt/scrapper/data/*
```

---

## 🔄 Update Deployment

```bash
cd /opt/scrapper

# Pull latest code
git pull origin main

# Rebuild and restart
docker compose up -d --build

# Verify
docker compose ps
curl http://localhost/health
```

---

## 🛑 Stop Services

```bash
cd /opt/scrapper
docker compose down
```

**To also remove volumes (WARNING: deletes database):**
```bash
docker compose down -v
```

---

## 🔐 Security Checklist

- [x] Firewall enabled (UFW)
- [x] Only ports 22, 80, 443 open
- [x] Strong postgres password
- [x] Strong API password
- [ ] SSL/TLS enabled (requires domain)
- [ ] Regular security updates
- [ ] Database backups configured

---

## 📝 Next Steps

1. **Set up domain (optional but recommended):**
   - Point DNS A record to 89.167.62.47
   - Update DOMAIN in .env
   - Restart services (Caddy will auto-provision SSL)

2. **Set up backups:**
   - Database backup script
   - Cron job for regular backups
   - Off-site backup storage

3. **Monitoring:**
   - Set up uptime monitoring
   - Configure log aggregation
   - Set up alerts for errors

4. **Testing:**
   - Run discovery: POST /runs/discover
   - Verify enrichment worker
   - Test Excel export

---

## 🆘 Support

If you encounter issues:

1. Check logs: `docker compose logs`
2. Check this guide's troubleshooting section
3. Check GitHub issues
4. Check service health: `docker compose ps`

---

**Deployment Date:** 2026-02-15
**Version:** 0.1.0
**Deployed By:** Claude DevOps
