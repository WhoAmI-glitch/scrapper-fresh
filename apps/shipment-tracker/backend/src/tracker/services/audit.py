"""Audit logging service.

Records all entity mutations for compliance and traceability.
"""

from __future__ import annotations

from uuid import UUID

import psycopg
from loguru import logger


async def log_activity(
    conn: psycopg.AsyncConnection,
    *,
    entity_type: str,
    entity_id: UUID,
    action: str,
    field_name: str | None = None,
    old_value: str | None = None,
    new_value: str | None = None,
    actor: str = "system",
    source: str = "api",
) -> None:
    """Insert an audit log entry."""
    await conn.execute(
        """
        INSERT INTO audit_log (entity_type, entity_id, action, field_name, old_value, new_value, actor, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        [entity_type, str(entity_id), action, field_name, old_value, new_value, actor, source],
    )


async def log_entity_changes(
    conn: psycopg.AsyncConnection,
    *,
    entity_type: str,
    entity_id: UUID,
    old_row: dict | None,
    new_values: dict,
    actor: str = "system",
    source: str = "api",
) -> None:
    """Log field-level changes between old row and new values."""
    action = "create" if old_row is None else "update"

    if old_row is None:
        await log_activity(
            conn,
            entity_type=entity_type,
            entity_id=entity_id,
            action="create",
            actor=actor,
            source=source,
        )
        return

    for field, new_val in new_values.items():
        old_val = old_row.get(field)
        if str(old_val) != str(new_val):
            await log_activity(
                conn,
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                field_name=field,
                old_value=str(old_val) if old_val is not None else None,
                new_value=str(new_val) if new_val is not None else None,
                actor=actor,
                source=source,
            )


async def get_entity_audit_log(
    conn: psycopg.AsyncConnection,
    entity_type: str,
    entity_id: UUID,
    limit: int = 50,
) -> list[dict]:
    """Fetch audit log entries for a specific entity."""
    cursor = await conn.execute(
        """
        SELECT * FROM audit_log
        WHERE entity_type = %s AND entity_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """,
        [entity_type, str(entity_id), limit],
    )
    return await cursor.fetchall()


async def get_recent_activity(
    conn: psycopg.AsyncConnection,
    limit: int = 50,
) -> list[dict]:
    """Fetch recent audit log entries across all entities."""
    cursor = await conn.execute(
        "SELECT * FROM audit_log ORDER BY created_at DESC LIMIT %s",
        [limit],
    )
    return await cursor.fetchall()
