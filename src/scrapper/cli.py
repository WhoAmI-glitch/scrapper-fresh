"""CLI entrypoint for the scrapper pipeline."""

from __future__ import annotations

import click
from loguru import logger

from scrapper.logging_ import setup_logging


@click.group()
def cli() -> None:
    """Scrapper — Russian construction company lead generator."""
    setup_logging()


@cli.command("init-db")
def init_db() -> None:
    """Create database tables."""
    from scrapper.db.connection import execute_schema
    execute_schema()
    click.echo("Database schema applied successfully.")


@cli.command()
@click.option(
    "--source",
    type=click.Choice(["fake", "yandex_maps", "twogis", "zakupki"]),
    default="fake",
    help="Discovery source",
)
@click.option("--no-tasks", is_flag=True, help="Don't create enrichment tasks")
@click.option(
    "--region",
    type=str,
    default=None,
    help="Comma-separated region slugs (e.g. moscow,spb)",
)
def discover(source: str, no_tasks: bool, region: str | None) -> None:
    """Discover company candidates from a source."""
    from scrapper.db.connection import get_connection
    from scrapper.db.queue import create_enrichment_task, save_candidate
    from scrapper.discovery.sources import SOURCES

    source_cls = SOURCES[source]
    kwargs: dict[str, object] = {}
    if region is not None and source in ("yandex_maps", "twogis", "zakupki"):
        kwargs["regions"] = [r.strip() for r in region.split(",") if r.strip()]
    src = source_cls(**kwargs)
    count = 0
    tasks_created = 0

    with get_connection() as conn:
        for hint in src.discover():
            cand_id = save_candidate(conn, hint)
            if cand_id is not None:
                count += 1
                if not no_tasks:
                    create_enrichment_task(conn, cand_id)
                    tasks_created += 1
                logger.info(f"Saved candidate: {hint.company_name}")
            else:
                logger.debug(f"Duplicate skipped: {hint.company_name}")
        conn.commit()

    click.echo(f"Discovered {count} new candidates, created {tasks_created} enrichment tasks.")


@cli.command()
@click.option("--batch-size", type=int, default=10, help="Tasks to process")
@click.option("--dry-run", is_flag=True, help="Don't fetch — just claim and show tasks")
def enrich(batch_size: int, dry_run: bool) -> None:
    """Process enrichment tasks: resolve → fetch → parse → save."""
    from scrapper.db.connection import get_connection
    from scrapper.db.queue import (
        claim_tasks,
        save_lead,
        update_task_state,
    )
    from scrapper.enrichment.fetcher import Fetcher
    from scrapper.enrichment.parser import RussprofileParser
    from scrapper.enrichment.resolver import ProfileResolver
    from scrapper.enrichment.website_contacts import scrape_website_contacts
    from scrapper.normalizers import normalize_phone
    from scrapper.storage.raw_pages import RawPageStore

    resolver = ProfileResolver()
    fetcher = Fetcher()
    parser = RussprofileParser()
    store = RawPageStore()

    with get_connection() as conn:
        tasks = claim_tasks(conn, batch_size)
        conn.commit()

    if not tasks:
        click.echo("No tasks in queue.")
        return

    click.echo(f"Claimed {len(tasks)} tasks.")
    success = 0
    failed = 0

    for task in tasks:
        try:
            if dry_run:
                click.echo(f"  [DRY RUN] Task {task.id}: {task.company_name}")
                with get_connection() as conn:
                    update_task_state(conn, task.id, "NEW")  # put back
                    conn.commit()
                continue

            # Step 1: Resolve
            search_url = resolver.resolve(task.company_name)
            if not search_url:
                raise ValueError(f"Could not build search URL for {task.company_name}")

            # Step 2: Fetch
            result = fetcher.fetch(search_url)
            if result.status_code != 200:
                raise ValueError(f"Fetch failed with status {result.status_code}")

            # Save raw HTML
            store.save(task.id, result.url, result.content, result.status_code)

            # Step 3: Parse
            lead = parser.parse(result.content)
            lead.task_id = task.id
            if not lead.company_name:
                lead.company_name = task.company_name

            # Step 4: Enrich contacts from alternative sources
            _enrich_contacts(lead, task.candidate_id, scrape_website_contacts, normalize_phone)

            # Step 5: Save
            with get_connection() as conn:
                save_lead(conn, lead)
                update_task_state(conn, task.id, "DONE", profile_url=search_url)
                conn.commit()

            logger.info(f"Task {task.id} completed: {task.company_name}")
            success += 1

        except Exception as e:
            logger.error(f"Task {task.id} failed: {e}")
            with get_connection() as conn:
                error_msg = str(e)[:500]
                update_task_state(conn, task.id, "FAILED", error_message=error_msg)
                conn.commit()
            failed += 1

    click.echo(f"Done. Success: {success}, Failed: {failed}")


def _enrich_contacts(
    lead: object,
    candidate_id: int,
    scrape_fn: object,
    normalize_fn: object,
) -> None:
    """Fill missing phone/email/website from website scraper and Yandex Maps metadata."""
    from scrapper.db.connection import get_connection
    from scrapper.db.models import Lead
    from scrapper.db.queue import get_candidate_metadata

    assert isinstance(lead, Lead)

    # Try website contact scraping if phone or email is missing
    website_url = lead.website
    if not website_url:
        # Check candidate metadata for URL from Yandex Maps
        with get_connection() as conn:
            meta = get_candidate_metadata(conn, candidate_id)
        website_url = meta.get("url")

    if website_url and (not lead.phone or not lead.email):
        try:
            contacts = scrape_fn(website_url)  # type: ignore[operator]
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

    # Fallback: use Yandex Maps phone data from candidate metadata
    if not lead.phone:
        with get_connection() as conn:
            meta = get_candidate_metadata(conn, candidate_id)
        yandex_phones = meta.get("phones", [])
        for raw_phone in yandex_phones:
            normalized = normalize_fn(raw_phone)  # type: ignore[operator]
            if normalized:
                lead.phone = normalized
                logger.info(f"Phone from Yandex Maps: {lead.phone}")
                break


@cli.command()
@click.option("--format", "fmt", type=click.Choice(["csv", "json", "xlsx"]), default="xlsx")
@click.option("--limit", type=int, default=None, help="Max records to export")
@click.option("--output", type=click.Path(), default=None, help="Output file path")
@click.option("--include-raw", is_flag=True, help="Include raw_data (JSON only)")
def export(fmt: str, limit: int | None, output: str | None, include_raw: bool) -> None:
    """Export leads to CSV, JSON, or Excel."""
    from pathlib import Path

    from scrapper.export.exporter import export_csv, export_json, export_xlsx

    out_path = Path(output) if output else None

    if fmt == "csv":
        result = export_csv(out_path, limit)
    elif fmt == "json":
        result = export_json(out_path, limit, include_raw)
    else:
        result = export_xlsx(out_path, limit)

    click.echo(f"Exported to: {result}")


@cli.command()
def stats() -> None:
    """Show pipeline statistics."""
    from scrapper.db.connection import get_connection
    from scrapper.db.queue import get_candidates_count, get_leads_count, get_queue_stats

    with get_connection() as conn:
        queue = get_queue_stats(conn)
        leads = get_leads_count(conn)
        candidates = get_candidates_count(conn)

    click.echo("=== Pipeline Statistics ===")
    click.echo(f"Candidates: {candidates}")
    click.echo(f"Leads:      {leads}")
    click.echo("Queue:")
    for state, cnt in sorted(queue.items()):
        click.echo(f"  {state}: {cnt}")
    if not queue:
        click.echo("  (empty)")


@cli.command()
def healthcheck() -> None:
    """Verify database connectivity."""
    try:
        from scrapper.db.connection import get_connection
        with get_connection() as conn:
            row = conn.execute("SELECT 1 AS ok").fetchone()
            if row and row["ok"] == 1:
                click.echo("Database: OK")
            else:
                click.echo("Database: UNEXPECTED RESPONSE")
    except Exception as e:
        click.echo(f"Database: FAILED — {e}")
        raise SystemExit(1) from e
