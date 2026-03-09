"""Email poller -- periodically checks Gmail for new shipment-related emails.

Runs as a background asyncio task on a configurable interval (default 2 minutes).
Fetches new messages, parses them for shipment data, links them to deals,
and generates alerts for linked emails.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta

from loguru import logger

from tracker.config import get_settings
from tracker.db import get_conn
from tracker.integrations.gmail import GmailClient, create_gmail_client
from tracker.services.email_parser import (
    categorize_email,
    link_email_to_deal,
    parse_shipment_email,
    store_email,
)
from tracker.services.alert_engine import create_alert
from tracker.api.ws import broadcast_alert

_task: asyncio.Task | None = None
_client: GmailClient | None = None
_running = False
_last_check: datetime | None = None


async def _poll_once() -> None:
    """Execute a single email polling cycle.

    1. Fetch new messages from Gmail since last check
    2. For each message, get full details
    3. Parse and categorize the email
    4. Store in database
    5. Link to existing deals/shipments
    6. Generate an alert if linked
    """
    global _client, _last_check

    settings = get_settings()

    if _client is None:
        _client = create_gmail_client()
        try:
            _client.connect(settings.gmail_credentials_path, settings.gmail_token_path)
        except Exception as exc:
            logger.warning("Gmail connection failed (expected in dev without credentials): {}", exc)
            return

    if not _client.is_connected():
        logger.debug("Email poller: Gmail not connected, skipping")
        return

    # Determine the time window for new messages
    after = _last_check or (datetime.now(timezone.utc) - timedelta(hours=1))

    messages = _client.fetch_new_messages(
        after_timestamp=after,
        query_filter=settings.gmail_query_filter,
        max_results=50,
    )

    if not messages:
        logger.debug("Email poller: no new messages")
        _last_check = datetime.now(timezone.utc)
        return

    logger.info("Email poller: processing {} new messages", len(messages))

    for msg_stub in messages:
        gmail_id = msg_stub["id"]

        try:
            detail = _client.get_message_detail(gmail_id)
        except Exception as exc:
            logger.error("Failed to fetch message {}: {}", gmail_id, exc)
            continue

        subject = detail["subject"]
        body = detail["body_text"]
        sender = detail["sender"]
        recipients = detail["recipients"]
        received_at = detail["received_at"]

        # Parse structured data from the email
        parsed_data = parse_shipment_email(subject, body, sender)

        # Categorize the email
        category = categorize_email(subject, body)

        async with get_conn() as conn:
            # Store the email
            email_row = await store_email(
                conn,
                gmail_id=gmail_id,
                subject=subject,
                sender=sender,
                recipients=recipients,
                body_text=body,
                received_at=received_at,
                category=category,
                parsed_data=parsed_data,
            )

            if not email_row:
                # Already existed (duplicate gmail_id)
                continue

            email_id = email_row["id"]

            # Link to deal/shipment
            link_result = await link_email_to_deal(conn, email_id, parsed_data)

            # Generate alert if the email was linked to a deal
            if link_result.get("deal_id"):
                alert = await create_alert(
                    conn,
                    alert_type="email_received",
                    severity="info",
                    title=f"Email received: {subject[:80]}",
                    message=(
                        f"From: {sender}\n"
                        f"Category: {category}\n"
                        f"Contract IDs: {', '.join(parsed_data.get('contract_ids', []))}\n"
                        f"Vessel names: {', '.join(parsed_data.get('vessel_names', []))}"
                    ),
                    shipment_id=link_result.get("shipment_id"),
                    deal_id=link_result.get("deal_id"),
                )

                # Broadcast the alert via WebSocket
                await broadcast_alert(alert)

    _last_check = datetime.now(timezone.utc)
    logger.info("Email poller: processed {} messages", len(messages))


async def _poll_loop() -> None:
    """Main polling loop that runs until cancelled."""
    global _running
    settings = get_settings()
    interval = settings.gmail_poll_interval_seconds

    logger.info("Email poller started (interval={}s)", interval)
    _running = True

    while _running:
        try:
            await _poll_once()
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.exception("Email poller error: {}", exc)

        try:
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            break

    logger.info("Email poller stopped")


async def start_email_poller() -> asyncio.Task:
    """Start the email polling background task."""
    global _task
    _task = asyncio.create_task(_poll_loop(), name="email_poller")
    return _task


async def stop_email_poller() -> None:
    """Stop the email polling background task gracefully."""
    global _task, _running
    _running = False
    if _task is not None and not _task.done():
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
    _task = None
