"""Alert checker -- periodic background task for detecting alert conditions.

Runs on a configurable interval (default 10 minutes) and checks for:
1. Delayed shipments (ETA passed without arrival)
2. Route deviations (vessels significantly off the direct route)
3. Old alert cleanup (remove acknowledged alerts past retention period)

Risk zone alerts are handled by the AIS poller after each position update,
so they are not duplicated here.
"""

from __future__ import annotations

import asyncio

from loguru import logger

from tracker.config import get_settings
from tracker.db import get_conn
from tracker.services.alert_engine import (
    check_delay_alerts,
    check_route_deviation_alerts,
    cleanup_old_alerts,
)
from tracker.api.ws import broadcast_alert

_task: asyncio.Task | None = None
_running = False


async def _check_once() -> None:
    """Execute a single alert checking cycle."""
    settings = get_settings()

    async with get_conn() as conn:
        # Check for delayed shipments
        delay_alerts = await check_delay_alerts(conn)
        if delay_alerts:
            logger.info("Alert checker: generated {} delay alerts", len(delay_alerts))
            for alert in delay_alerts:
                await broadcast_alert(alert)

        # Check for route deviations
        deviation_alerts = await check_route_deviation_alerts(
            conn,
            threshold_nm=settings.route_deviation_threshold_nm,
        )
        if deviation_alerts:
            logger.info(
                "Alert checker: generated {} route deviation alerts",
                len(deviation_alerts),
            )
            for alert in deviation_alerts:
                await broadcast_alert(alert)

        # Clean up old acknowledged alerts
        deleted = await cleanup_old_alerts(
            conn, days=settings.old_alert_cleanup_days
        )
        if deleted > 0:
            logger.info("Alert checker: cleaned up {} old alerts", deleted)


async def _check_loop() -> None:
    """Main checking loop that runs until cancelled."""
    global _running
    settings = get_settings()
    interval = settings.alert_check_interval_seconds

    logger.info("Alert checker started (interval={}s)", interval)
    _running = True

    while _running:
        try:
            await _check_once()
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.exception("Alert checker error: {}", exc)

        try:
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            break

    logger.info("Alert checker stopped")


async def start_alert_checker() -> asyncio.Task:
    """Start the alert checking background task."""
    global _task
    _task = asyncio.create_task(_check_loop(), name="alert_checker")
    return _task


async def stop_alert_checker() -> None:
    """Stop the alert checking background task gracefully."""
    global _task, _running
    _running = False
    if _task is not None and not _task.done():
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
    _task = None
