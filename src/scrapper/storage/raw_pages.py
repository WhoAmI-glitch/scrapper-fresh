"""RawPageStore — persist raw HTML snapshots to disk and record metadata in DB."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from loguru import logger

from scrapper.config import get_settings
from scrapper.db.connection import get_connection


class RawPageStore:
    """Saves and loads raw HTML page snapshots.

    HTML files are stored on disk under ``data/raw/YYYY-MM-DD/task_{id}.html``.
    Metadata (URL, file path, HTTP status, content length) is recorded in the
    ``raw_pages`` database table.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._base_dir: Path = settings.raw_data_dir

    def save(
        self,
        task_id: int,
        url: str,
        content: str,
        http_status: int,
    ) -> str:
        """Save HTML content to disk and record metadata in the database.

        Args:
            task_id: The enrichment task ID this page belongs to.
            url: The URL that was fetched.
            content: Raw HTML content to save.
            http_status: The HTTP status code from the fetch.

        Returns:
            The file path (relative to project root) where the HTML was saved.
        """
        # Build the directory: data/raw/YYYY-MM-DD/
        today = date.today().isoformat()
        day_dir = self._base_dir / today
        day_dir.mkdir(parents=True, exist_ok=True)

        # Write HTML to disk
        filename = f"task_{task_id}.html"
        file_path = day_dir / filename
        file_path.write_text(content, encoding="utf-8")

        # Store as a relative-ish path string for the database
        relative_path = str(file_path)
        content_length = len(content)

        logger.info(
            "Saved raw page for task {}: {} ({} chars, HTTP {})",
            task_id,
            relative_path,
            content_length,
            http_status,
        )

        # Record metadata in the raw_pages table
        try:
            with get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO raw_pages (task_id, url, file_path, http_status, content_length)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (task_id, url, relative_path, http_status, content_length),
                )
                conn.commit()

            logger.debug(
                "Recorded raw_pages metadata for task {}",
                task_id,
            )
        except Exception:
            logger.exception(
                "Failed to record raw_pages metadata for task {} "
                "(file was saved to disk)",
                task_id,
            )
            # Re-raise so callers know the DB write failed,
            # even though the file was saved successfully
            raise

        return relative_path

    def load(self, file_path: str) -> str | None:
        """Load HTML content from a previously saved file.

        Args:
            file_path: The file path as returned by ``save()``.

        Returns:
            The HTML content as a string, or None if the file does not exist.
        """
        path = Path(file_path)

        if not path.exists():
            logger.warning("Raw page file not found: {}", file_path)
            return None

        content = path.read_text(encoding="utf-8")
        logger.debug(
            "Loaded raw page from {} ({} chars)",
            file_path,
            len(content),
        )
        return content
