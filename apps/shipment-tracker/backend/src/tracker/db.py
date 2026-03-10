"""Database connection pool management using psycopg3.

Provides a singleton connection pool and convenience helpers for
obtaining connections and executing schema migrations.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from loguru import logger

from tracker.config import get_settings

# Module-level pool reference; initialised at application startup.
_pool: AsyncConnectionPool | None = None


async def init_pool() -> AsyncConnectionPool:
    """Create and open the async connection pool.

    Called once during application lifespan startup.
    """
    global _pool
    settings = get_settings()
    logger.info(
        "Initialising database pool: host={} db={} pool_size={}-{}",
        settings.db_host,
        settings.db_name,
        settings.db_min_pool_size,
        settings.db_max_pool_size,
    )
    _pool = AsyncConnectionPool(
        conninfo=settings.database_url,
        min_size=settings.db_min_pool_size,
        max_size=settings.db_max_pool_size,
        kwargs={"row_factory": dict_row, "autocommit": False},
        open=False,
    )
    await _pool.open()
    await _pool.check()
    logger.info("Database pool ready")
    return _pool


async def close_pool() -> None:
    """Gracefully close the connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("Database pool closed")


def get_pool() -> AsyncConnectionPool:
    """Return the active connection pool.

    Raises RuntimeError if the pool has not been initialised.
    """
    if _pool is None:
        raise RuntimeError(
            "Database pool is not initialised. "
            "Ensure init_pool() is called during application startup."
        )
    return _pool


@asynccontextmanager
async def get_conn() -> AsyncIterator[psycopg.AsyncConnection]:
    """Yield a connection from the pool as an async context manager.

    The connection is returned to the pool automatically. Commits on
    success, rolls back on exception.
    """
    pool = get_pool()
    async with pool.connection() as conn:
        try:
            yield conn
            await conn.commit()
        except Exception:
            await conn.rollback()
            raise


async def execute_schema(conn: psycopg.AsyncConnection) -> None:
    """Execute the SQL schema file against the given connection.

    This is idempotent for CREATE IF NOT EXISTS / CREATE OR REPLACE
    statements, but will raise on conflicts with existing objects
    that differ in definition.
    """
    settings = get_settings()
    schema_sql = settings.schema_path.read_text(encoding="utf-8")
    logger.info("Executing schema from {}", settings.schema_path)
    await conn.execute(schema_sql)  # type: ignore[arg-type]
    await conn.commit()
    logger.info("Schema applied successfully")


async def run_migrations(conn: psycopg.AsyncConnection) -> None:
    """Run pending SQL migrations from the migrations directory.

    Tracks applied migrations in a _migrations table. Each migration
    runs exactly once, in alphabetical order.
    """
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            name TEXT PRIMARY KEY,
            applied_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    await conn.commit()

    migrations_dir = Path(__file__).parent / "models" / "migrations"
    if not migrations_dir.exists():
        return

    sql_files = sorted(migrations_dir.glob("*.sql"))
    for sql_file in sql_files:
        cursor = await conn.execute(
            "SELECT 1 FROM _migrations WHERE name = %s", [sql_file.name]
        )
        if await cursor.fetchone():
            continue

        logger.info("Applying migration: {}", sql_file.name)
        migration_sql = sql_file.read_text(encoding="utf-8")
        await conn.execute(migration_sql)  # type: ignore[arg-type]
        await conn.execute(
            "INSERT INTO _migrations (name) VALUES (%s)", [sql_file.name]
        )
        await conn.commit()
        logger.info("Migration {} applied successfully", sql_file.name)


async def execute_seed(conn: psycopg.AsyncConnection) -> None:
    """Execute the SQL seed file to populate sample data.

    Only intended for development / demo environments.
    """
    settings = get_settings()
    seed_sql = settings.seed_path.read_text(encoding="utf-8")
    logger.info("Executing seed data from {}", settings.seed_path)
    await conn.execute(seed_sql)  # type: ignore[arg-type]
    await conn.commit()
    logger.info("Seed data applied successfully")
