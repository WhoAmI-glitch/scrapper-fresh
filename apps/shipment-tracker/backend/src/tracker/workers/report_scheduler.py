"""Scheduled report generation worker.

Runs on a loop, checks report_schedules table for due reports,
generates them, and stores/sends results.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from loguru import logger

from tracker.db import get_conn
from tracker.services.report_generator import (
    generate_trading_book_report,
    generate_shipment_progress_report,
)

_task: asyncio.Task | None = None
_stop_event = asyncio.Event()

REPORT_GENERATORS = {
    "trading_book": generate_trading_book_report,
    "shipment_progress": generate_shipment_progress_report,
}


async def _check_schedules() -> None:
    """Check for due report schedules and generate reports."""
    async with get_conn() as conn:
        cursor = await conn.execute(
            """
            SELECT id, report_type, schedule_cron, last_run_at, recipient_emails, is_active
            FROM report_schedules
            WHERE is_active = TRUE
            AND (last_run_at IS NULL OR last_run_at < NOW() - INTERVAL '1 hour')
            ORDER BY last_run_at ASC NULLS FIRST
            """
        )
        schedules = await cursor.fetchall()

        if not schedules:
            return

        for sched in schedules:
            report_type = sched["report_type"]
            generator = REPORT_GENERATORS.get(report_type)
            if not generator:
                logger.warning("Unknown report type: {}", report_type)
                continue

            # Check if it's time to run based on simple interval logic
            # (Full cron parsing would use croniter library)
            if not _should_run(sched):
                continue

            try:
                logger.info("Generating scheduled report: {} ({})", report_type, sched["id"])
                report_bytes = await generator(conn)

                # Store the generated report
                await conn.execute(
                    """
                    INSERT INTO generated_reports (schedule_id, report_type, file_data, file_name, generated_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    ON CONFLICT DO NOTHING
                    """,
                    [
                        str(sched["id"]),
                        report_type,
                        report_bytes.getvalue(),
                        f"{report_type}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.xlsx",
                    ],
                )

                # Update last_run_at
                await conn.execute(
                    "UPDATE report_schedules SET last_run_at = NOW() WHERE id = %s",
                    [str(sched["id"])],
                )

                logger.info("Report {} generated successfully", report_type)

            except Exception as e:
                logger.error("Failed to generate report {}: {}", report_type, e)


def _should_run(schedule: dict) -> bool:
    """Simple check if a schedule should run now.

    For production, use croniter to parse cron expressions.
    Here we use a simplified approach based on last_run_at.
    """
    cron = schedule.get("schedule_cron", "")
    last_run = schedule.get("last_run_at")

    if last_run is None:
        return True

    now = datetime.now(timezone.utc)
    if last_run.tzinfo is None:
        from datetime import timezone as tz
        last_run = last_run.replace(tzinfo=tz.utc)

    elapsed = (now - last_run).total_seconds()

    # Parse simple intervals from cron-like expressions
    if "daily" in cron or cron == "0 8 * * *":
        return elapsed >= 86400  # 24 hours
    if "weekly" in cron or cron == "0 8 * * 1":
        return elapsed >= 604800  # 7 days
    if "hourly" in cron:
        return elapsed >= 3600

    # Default: run every 24 hours
    return elapsed >= 86400


async def _scheduler_loop() -> None:
    """Run the report scheduler on a loop."""
    while not _stop_event.is_set():
        try:
            await _check_schedules()
        except Exception as e:
            logger.error("Report scheduler error: {}", e)

        try:
            await asyncio.wait_for(_stop_event.wait(), timeout=300)  # Check every 5 minutes
        except asyncio.TimeoutError:
            pass


async def start_report_scheduler() -> asyncio.Task:
    """Start the report scheduler background worker."""
    global _task
    _stop_event.clear()
    _task = asyncio.create_task(_scheduler_loop(), name="report_scheduler")
    logger.info("Report scheduler started")
    return _task


async def stop_report_scheduler() -> None:
    """Stop the report scheduler."""
    _stop_event.set()
    if _task and not _task.done():
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
    logger.info("Report scheduler stopped")
