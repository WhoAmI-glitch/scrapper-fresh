"""Monitoring — health checks, stuck task detection, and optional Telegram alerts."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import httpx
from loguru import logger

from scrapper.config import get_settings
from scrapper.db.connection import get_connection


def get_monitoring_status() -> dict[str, Any]:
    """Return a comprehensive monitoring snapshot."""
    checks: list[dict[str, Any]] = []
    alerts: list[str] = []

    # 1. Database connectivity
    db_ok = _check_database()
    checks.append({"name": "database", "ok": db_ok})
    if not db_ok:
        alerts.append("Database is unreachable")
        return {
            "healthy": False,
            "checks": checks,
            "alerts": alerts,
            "timestamp": datetime.utcnow().isoformat(),
        }

    with get_connection() as conn:
        # 2. Stuck tasks (in FETCHING for > 30 minutes)
        stuck = _count_stuck_tasks(conn, minutes=30)
        checks.append({"name": "stuck_tasks", "ok": stuck == 0, "count": stuck})
        if stuck > 0:
            alerts.append(f"{stuck} tasks stuck in FETCHING for >30 min")

        # 3. Failure rate in last hour
        fail_rate = _failure_rate_1h(conn)
        checks.append({"name": "failure_rate_1h", "ok": fail_rate < 0.5, "rate": fail_rate})
        if fail_rate >= 0.5:
            alerts.append(f"High failure rate: {fail_rate:.0%} in the last hour")

        # 4. Queue depth
        queue = _queue_depth(conn)
        checks.append({"name": "queue_depth", "ok": True, **queue})

        # 5. Last discovery stats
        last_disc = _last_discovery(conn)
        checks.append({"name": "last_discovery", "ok": True, **last_disc})

    healthy = all(c["ok"] for c in checks)

    # Send Telegram alert if unhealthy
    if not healthy and alerts:
        _send_telegram_alert(alerts)

    return {
        "healthy": healthy,
        "checks": checks,
        "alerts": alerts,
        "timestamp": datetime.utcnow().isoformat(),
    }


def _check_database() -> bool:
    """Check if the database is reachable."""
    try:
        with get_connection() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        logger.warning("Database health check failed")
        return False


def _count_stuck_tasks(conn: Any, minutes: int = 30) -> int:
    """Count tasks in FETCHING state for longer than the threshold."""
    cutoff = datetime.utcnow() - timedelta(minutes=minutes)
    row = conn.execute(
        """
        SELECT COUNT(*) as cnt FROM enrichment_tasks
        WHERE state = 'FETCHING' AND updated_at < %s
        """,
        (cutoff,),
    ).fetchone()
    return row["cnt"] if row else 0


def _failure_rate_1h(conn: Any) -> float:
    """Calculate the fraction of tasks that failed in the last hour."""
    since = datetime.utcnow() - timedelta(hours=1)
    row = conn.execute(
        """
        SELECT
            COUNT(*) FILTER (WHERE state = 'FAILED') as failed,
            COUNT(*) as total
        FROM enrichment_tasks
        WHERE updated_at >= %s
        """,
        (since,),
    ).fetchone()
    if not row or row["total"] == 0:
        return 0.0
    result: float = row["failed"] / row["total"]
    return result


def _queue_depth(conn: Any) -> dict[str, int]:
    """Return task counts by state."""
    rows = conn.execute(
        "SELECT state, COUNT(*) as cnt FROM enrichment_tasks GROUP BY state"
    ).fetchall()
    return {r["state"]: r["cnt"] for r in rows}


def _last_discovery(conn: Any) -> dict[str, Any]:
    """Return info about the most recent candidate batch."""
    row = conn.execute(
        """
        SELECT source, COUNT(*) as cnt, MAX(created_at) as last_at
        FROM candidates
        GROUP BY source
        ORDER BY last_at DESC
        LIMIT 1
        """
    ).fetchone()
    if not row:
        return {"source": None, "count": 0, "last_at": None}
    return {
        "source": row["source"],
        "count": row["cnt"],
        "last_at": row["last_at"].isoformat() if row["last_at"] else None,
    }


def _send_telegram_alert(alerts: list[str]) -> None:
    """Send alerts via Telegram bot (if configured)."""
    settings = get_settings()
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return

    text = "⚠️ Scrapper Alert\n\n" + "\n".join(f"• {a}" for a in alerts)
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"

    try:
        resp = httpx.post(
            url,
            json={"chat_id": settings.telegram_chat_id, "text": text},
            timeout=10,
        )
        if not resp.is_success:
            logger.warning(f"Telegram alert failed: {resp.status_code}")
    except Exception as e:
        logger.warning(f"Telegram alert error: {e}")
