#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# Cron Job Setup — Scrapper automated tasks
#
# Installs cron jobs for:
#   - Daily discovery run (6 AM Moscow time)
#   - Daily database backup (2 AM Moscow time)
#   - Weekly old backup cleanup (Sunday 3 AM)
#
# Usage: sudo ./scripts/setup_cron.sh
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Setting up cron jobs ==="
echo "Project directory: $PROJECT_DIR"
echo ""

# Create backup directory
BACKUP_DIR="$PROJECT_DIR/data/backups"
mkdir -p "$BACKUP_DIR"

# Build crontab entries
CRON_FILE=$(mktemp)

# Preserve existing crontab
crontab -l 2>/dev/null | grep -v "scrapper" > "$CRON_FILE" || true

cat >> "$CRON_FILE" <<CRON
# --- Scrapper automated tasks ---

# Daily discovery: Yandex Maps (6:00 AM Moscow / 3:00 UTC)
0 3 * * * cd $PROJECT_DIR && docker compose exec -T api scrapper discover --source yandex_maps >> $PROJECT_DIR/data/logs/discovery.log 2>&1

# Daily discovery: 2GIS (6:30 AM Moscow / 3:30 UTC)
30 3 * * * cd $PROJECT_DIR && docker compose exec -T api scrapper discover --source twogis >> $PROJECT_DIR/data/logs/discovery.log 2>&1

# Daily discovery: Zakupki (7:00 AM Moscow / 4:00 UTC)
0 4 * * * cd $PROJECT_DIR && docker compose exec -T api scrapper discover --source zakupki >> $PROJECT_DIR/data/logs/discovery.log 2>&1

# Daily database backup (2:00 AM Moscow / 23:00 UTC previous day)
0 23 * * * cd $PROJECT_DIR && docker compose exec -T db pg_dump -U postgres scrapper | gzip > $BACKUP_DIR/scrapper_\$(date +\%Y\%m\%d).sql.gz 2>> $PROJECT_DIR/data/logs/backup.log

# Weekly cleanup: remove backups older than 7 days (Sunday 3:00 AM Moscow / 0:00 UTC)
0 0 * * 0 find $BACKUP_DIR -name "scrapper_*.sql.gz" -mtime +7 -delete 2>> $PROJECT_DIR/data/logs/backup.log

# --- End scrapper tasks ---
CRON

# Install crontab
crontab "$CRON_FILE"
rm "$CRON_FILE"

# Create log directory
mkdir -p "$PROJECT_DIR/data/logs"

echo "Cron jobs installed:"
echo ""
crontab -l | grep "scrapper"
echo ""
echo "Log files:"
echo "  Discovery: $PROJECT_DIR/data/logs/discovery.log"
echo "  Backup:    $PROJECT_DIR/data/logs/backup.log"
echo ""
echo "Backup directory: $BACKUP_DIR"
echo ""
echo "Done."
