#!/usr/bin/env python3
"""Background worker that continuously processes enrichment tasks.

Polls the database for NEW tasks and runs the enrichment pipeline.
Supports graceful shutdown via SIGTERM/SIGINT.

Usage:
    python scripts/worker.py
"""

from __future__ import annotations

import signal
import sys
import time
from pathlib import Path

# Ensure project root is on sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "src"))

from loguru import logger  # noqa: E402

from scrapper.config import get_settings  # noqa: E402
from scrapper.db.connection import close_pool, get_connection  # noqa: E402
from scrapper.db.queue import (  # noqa: E402
    claim_tasks,
    get_candidate_metadata,
    save_lead,
    update_task_state,
)
from scrapper.enrichment.fetcher import Fetcher  # noqa: E402
from scrapper.enrichment.parser import RussprofileParser  # noqa: E402
from scrapper.enrichment.resolver import ProfileResolver  # noqa: E402
from scrapper.enrichment.website_contacts import scrape_website_contacts  # noqa: E402
from scrapper.logging_ import setup_logging  # noqa: E402
from scrapper.normalizers import normalize_phone  # noqa: E402
from scrapper.storage.raw_pages import RawPageStore  # noqa: E402

_shutdown = False


def _handle_signal(signum: int, frame: object) -> None:
    """Handle shutdown signal gracefully."""
    global _shutdown
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    _shutdown = True


def _enrich_contacts(lead: object, candidate_id: int) -> None:
    """Fill missing phone/email/website from alternative sources."""
    from scrapper.db.models import Lead

    assert isinstance(lead, Lead)

    website_url = lead.website
    if not website_url:
        with get_connection() as conn:
            meta = get_candidate_metadata(conn, candidate_id)
        website_url = meta.get("url")

    if website_url and (not lead.phone or not lead.email):
        try:
            contacts = scrape_website_contacts(website_url)
            if not lead.phone and contacts.get("phones"):
                lead.phone = contacts["phones"][0]
                logger.info(f"Phone from website: {lead.phone}")
            if not lead.email and contacts.get("emails"):
                lead.email = contacts["emails"][0]
                logger.info(f"Email from website: {lead.email}")
            if not lead.website and contacts.get("websites"):
                lead.website = contacts["websites"][0]
        except Exception as e:
            logger.debug(f"Website contact scraping failed: {e}")

    if not lead.phone:
        with get_connection() as conn:
            meta = get_candidate_metadata(conn, candidate_id)
        for raw_phone in meta.get("phones", []):
            normalized = normalize_phone(raw_phone)
            if normalized:
                lead.phone = normalized
                logger.info(f"Phone from discovery metadata: {lead.phone}")
                break


def process_batch(
    resolver: ProfileResolver,
    fetcher: Fetcher,
    parser: RussprofileParser,
    store: RawPageStore,
    batch_size: int,
) -> int:
    """Process one batch of enrichment tasks. Returns number processed."""
    with get_connection() as conn:
        tasks = claim_tasks(conn, batch_size)
        conn.commit()

    if not tasks:
        return 0

    logger.info(f"Claimed {len(tasks)} tasks")
    processed = 0

    for task in tasks:
        if _shutdown:
            # Put unclaimed tasks back
            with get_connection() as conn:
                update_task_state(conn, task.id, "NEW")
                conn.commit()
            break

        try:
            search_url = resolver.resolve(task.company_name)
            if not search_url:
                raise ValueError(f"Could not build search URL for {task.company_name}")

            result = fetcher.fetch(search_url)
            if result.status_code != 200:
                raise ValueError(f"Fetch failed with status {result.status_code}")

            store.save(task.id, result.url, result.content, result.status_code)

            lead = parser.parse(result.content)
            lead.task_id = task.id
            if not lead.company_name:
                lead.company_name = task.company_name

            _enrich_contacts(lead, task.candidate_id)

            with get_connection() as conn:
                save_lead(conn, lead)
                update_task_state(conn, task.id, "DONE", profile_url=search_url)
                conn.commit()

            logger.info(f"Task {task.id} completed: {task.company_name}")
            processed += 1

        except Exception as e:
            logger.error(f"Task {task.id} failed: {e}")
            with get_connection() as conn:
                error_msg = str(e)[:500]
                update_task_state(conn, task.id, "FAILED", error_message=error_msg)
                conn.commit()

    return processed


def main() -> int:
    setup_logging()
    settings = get_settings()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    poll_interval = settings.worker_poll_interval
    batch_size = settings.task_batch_size

    logger.info(
        f"Worker started (poll={poll_interval}s, batch={batch_size})"
    )

    resolver = ProfileResolver()
    fetcher = Fetcher()
    parser = RussprofileParser()
    store = RawPageStore()

    try:
        while not _shutdown:
            processed = process_batch(resolver, fetcher, parser, store, batch_size)
            if processed == 0 and not _shutdown:
                time.sleep(poll_interval)
    finally:
        fetcher.close()
        close_pool()
        logger.info("Worker stopped")

    return 0


if __name__ == "__main__":
    sys.exit(main())
