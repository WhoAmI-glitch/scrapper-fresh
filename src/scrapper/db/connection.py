"""PostgreSQL connection management using psycopg3 connection pool."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from loguru import logger
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from scrapper.config import get_settings

if TYPE_CHECKING:
    from collections.abc import Generator

    import psycopg

# Module-level pool (lazy init)
_pool: ConnectionPool | None = None


def _get_pool() -> ConnectionPool:
    """Return or create the global connection pool."""
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = ConnectionPool(
            conninfo=settings.database_url,
            min_size=2,
            max_size=10,
            kwargs={"row_factory": dict_row},
        )
        logger.info("Database connection pool created")
    return _pool


@contextmanager
def get_connection() -> Generator[psycopg.Connection, None, None]:
    """Yield a database connection from the pool."""
    pool = _get_pool()
    with pool.connection() as conn:
        yield conn


def execute_schema() -> None:
    """Run the DDL schema file to create tables."""
    from importlib.resources import files

    schema_sql = files("scrapper.db").joinpath("schema.sql").read_text(encoding="utf-8")
    with get_connection() as conn:
        conn.execute(schema_sql)
        conn.commit()
    logger.info("Database schema applied")


def close_pool() -> None:
    """Close the connection pool."""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None
        logger.info("Database connection pool closed")
