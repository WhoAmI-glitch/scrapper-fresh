"""Background worker for Google Calendar synchronization.

Polls calendar for trading-related meetings with Google Meet links
and creates meeting records in the database.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from loguru import logger

from tracker.config import get_settings
from tracker.db import get_conn
from tracker.integrations.google_calendar import GoogleCalendarClient
from tracker.services.meeting_service import create_meeting, add_participant

_task: asyncio.Task | None = None
_stop_event = asyncio.Event()


async def _sync_once() -> None:
    """Perform a single calendar sync cycle."""
    settings = get_settings()

    try:
        client = GoogleCalendarClient(
            credentials_path=settings.gmail_credentials_path,
            token_path=settings.gmail_token_path,
        )
    except Exception as e:
        logger.debug("Calendar client not available: {}", e)
        return

    events = client.get_upcoming_events(max_results=20)
    if not events:
        return

    logger.info("Found {} upcoming calendar events", len(events))

    for event in events:
        if not GoogleCalendarClient.is_trading_meeting(event):
            continue

        event_id = event.get("id")
        if not event_id:
            continue

        async with get_conn() as conn:
            # Check if we already have this event
            cursor = await conn.execute(
                "SELECT id FROM meetings WHERE google_calendar_event_id = %s",
                [event_id],
            )
            if await cursor.fetchone():
                continue

            # Extract meeting details
            title = event.get("summary", "Untitled Meeting")
            start_dt = event.get("start", {}).get("dateTime")
            end_dt = event.get("end", {}).get("dateTime")
            meet_url = GoogleCalendarClient.extract_meet_url(event)

            if not start_dt:
                continue

            meeting = await create_meeting(
                conn,
                title=title,
                scheduled_start=start_dt,
                scheduled_end=end_dt,
                google_calendar_event_id=event_id,
                google_meet_url=meet_url,
            )

            # Add participants
            attendees = GoogleCalendarClient.extract_attendees(event)
            for att in attendees:
                await add_participant(
                    conn,
                    meeting["id"],
                    name=att["name"],
                    email=att["email"],
                    role="organizer" if att["organizer"] else "attendee",
                )

            # Try to link to deals via attendee emails
            for att in attendees:
                if att["email"]:
                    cursor = await conn.execute(
                        """
                        SELECT d.id FROM deals d
                        JOIN counterparties cp ON (d.buyer_id = cp.id OR d.seller_id = cp.id)
                        WHERE cp.primary_contact_email = %s
                        AND d.status NOT IN ('cancelled', 'completed')
                        """,
                        [att["email"]],
                    )
                    deal_rows = await cursor.fetchall()
                    for dr in deal_rows:
                        await conn.execute(
                            "INSERT INTO meeting_deals (meeting_id, deal_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                            [str(meeting["id"]), str(dr["id"])],
                        )

            logger.info("Synced meeting: {} ({})", title, event_id)


async def _sync_loop() -> None:
    """Run calendar sync on a loop."""
    settings = get_settings()
    interval = getattr(settings, "calendar_sync_interval_seconds", 300)

    while not _stop_event.is_set():
        try:
            await _sync_once()
        except Exception as e:
            logger.error("Calendar sync error: {}", e)

        try:
            await asyncio.wait_for(_stop_event.wait(), timeout=interval)
        except asyncio.TimeoutError:
            pass


async def start_calendar_sync() -> asyncio.Task:
    """Start the calendar sync background worker."""
    global _task
    _stop_event.clear()
    _task = asyncio.create_task(_sync_loop(), name="calendar_sync")
    logger.info("Calendar sync worker started")
    return _task


async def stop_calendar_sync() -> None:
    """Stop the calendar sync worker."""
    _stop_event.set()
    if _task and not _task.done():
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
    logger.info("Calendar sync worker stopped")
