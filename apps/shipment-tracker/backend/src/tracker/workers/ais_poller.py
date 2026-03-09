"""AIS position poller -- periodically fetches vessel positions from AIS provider.

Runs as a background asyncio task on a configurable interval (default 5 minutes).
For each active shipment's vessel, fetches the latest AIS position, updates the
database, evaluates risk zones, and broadcasts position updates via WebSocket.
"""

from __future__ import annotations

import asyncio

from loguru import logger

from tracker.config import get_settings
from tracker.db import get_conn
from tracker.integrations.ais import AISProvider, MockAISProvider, create_ais_provider
from tracker.services.vessel_tracker import (
    get_active_vessel_ids,
    update_vessel_position,
)
from tracker.services.risk_scorer import (
    score_vessel_risk,
    update_shipment_risk_levels,
)
from tracker.api.ws import broadcast_vessel_position

_task: asyncio.Task | None = None
_provider: AISProvider | None = None
_running = False


async def _poll_once() -> None:
    """Execute a single AIS polling cycle.

    1. Get vessels assigned to active shipments
    2. Batch-fetch positions from the AIS provider
    3. Update each vessel's position in the database
    4. Broadcast position updates via WebSocket
    5. Recalculate risk levels for all active shipments
    """
    global _provider
    if _provider is None:
        _provider = create_ais_provider()

    async with get_conn() as conn:
        active_vessels = await get_active_vessel_ids(conn)

    if not active_vessels:
        logger.debug("AIS poller: no active vessels to track")
        return

    imo_list = [v["imo_number"] for v in active_vessels]
    imo_to_vessel = {v["imo_number"]: v for v in active_vessels}

    logger.info("AIS poller: fetching positions for {} vessels", len(imo_list))

    # If the mock provider is used, seed it with known positions on first run
    if isinstance(_provider, MockAISProvider):
        async with get_conn() as conn:
            for vessel in active_vessels:
                cursor = await conn.execute(
                    """
                    SELECT
                        ST_Y(current_position::geometry) AS lat,
                        ST_X(current_position::geometry) AS lon,
                        current_speed, current_heading
                    FROM vessels WHERE id = %s AND current_position IS NOT NULL
                    """,
                    [str(vessel["id"])],
                )
                row = await cursor.fetchone()
                if row and row["lat"] is not None:
                    _provider.seed_position(
                        vessel["imo_number"],
                        row["lat"],
                        row["lon"],
                        row["current_speed"] or 0.0,
                        row["current_heading"] or 0.0,
                    )

    positions = await _provider.get_vessel_positions_batch(imo_list)

    async with get_conn() as conn:
        for pos in positions:
            vessel_info = imo_to_vessel.get(pos.imo_number)
            if vessel_info is None:
                continue

            # Update database
            updated = await update_vessel_position(
                conn,
                vessel_id=vessel_info["id"],
                lat=pos.lat,
                lon=pos.lon,
                speed=pos.speed,
                heading=pos.heading,
            )

            # Broadcast to WebSocket clients
            if updated:
                await broadcast_vessel_position(
                    vessel_id=str(vessel_info["id"]),
                    vessel_name=vessel_info["name"],
                    lat=pos.lat,
                    lon=pos.lon,
                    speed=pos.speed,
                    heading=pos.heading,
                )

        # Batch-update risk levels after all positions are refreshed
        await update_shipment_risk_levels(conn)

    logger.info("AIS poller: updated {} vessel positions", len(positions))


async def _poll_loop() -> None:
    """Main polling loop that runs until cancelled."""
    global _running
    settings = get_settings()
    interval = settings.ais_poll_interval_seconds

    logger.info("AIS poller started (interval={}s)", interval)
    _running = True

    while _running:
        try:
            await _poll_once()
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.exception("AIS poller error: {}", exc)

        try:
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            break

    logger.info("AIS poller stopped")


async def start_ais_poller() -> asyncio.Task:
    """Start the AIS polling background task."""
    global _task
    _task = asyncio.create_task(_poll_loop(), name="ais_poller")
    return _task


async def stop_ais_poller() -> None:
    """Stop the AIS polling background task gracefully."""
    global _task, _running
    _running = False
    if _task is not None and not _task.done():
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
    _task = None
