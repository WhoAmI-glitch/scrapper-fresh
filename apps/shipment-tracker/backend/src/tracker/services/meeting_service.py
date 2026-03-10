"""Meeting management service.

CRUD operations for meetings, participants, transcripts, and linked entities.
"""

from __future__ import annotations

from uuid import UUID

import psycopg
from loguru import logger


async def get_meetings(
    conn: psycopg.AsyncConnection,
    *,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
) -> tuple[list[dict], int]:
    """Fetch meetings with pagination. Returns (items, total_count)."""
    conditions: list[str] = []
    params: list[object] = []

    if status:
        conditions.append("m.status = %s")
        params.append(status)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    cursor = await conn.execute(f"SELECT COUNT(*) AS total FROM meetings m {where}", params)
    total = (await cursor.fetchone())["total"]

    offset = (page - 1) * page_size
    cursor = await conn.execute(
        f"""
        SELECT m.* FROM meetings m {where}
        ORDER BY m.scheduled_start DESC
        LIMIT %s OFFSET %s
        """,
        params + [page_size, offset],
    )
    rows = await cursor.fetchall()
    return rows, total


async def get_meeting_by_id(conn: psycopg.AsyncConnection, meeting_id: UUID) -> dict | None:
    """Fetch a single meeting with all related data."""
    cursor = await conn.execute("SELECT * FROM meetings WHERE id = %s", [str(meeting_id)])
    meeting = await cursor.fetchone()
    if not meeting:
        return None

    # Participants
    cursor = await conn.execute(
        "SELECT * FROM meeting_participants WHERE meeting_id = %s ORDER BY name",
        [str(meeting_id)],
    )
    meeting["participants"] = await cursor.fetchall()

    # Summary
    cursor = await conn.execute(
        "SELECT * FROM meeting_summaries WHERE meeting_id = %s ORDER BY generated_at DESC LIMIT 1",
        [str(meeting_id)],
    )
    meeting["summary"] = await cursor.fetchone()

    # Action items
    cursor = await conn.execute(
        "SELECT * FROM action_items WHERE meeting_id = %s ORDER BY created_at",
        [str(meeting_id)],
    )
    meeting["action_items"] = await cursor.fetchall()

    # Linked deals
    cursor = await conn.execute(
        "SELECT deal_id FROM meeting_deals WHERE meeting_id = %s",
        [str(meeting_id)],
    )
    deal_rows = await cursor.fetchall()
    meeting["linked_deal_ids"] = [str(r["deal_id"]) for r in deal_rows]

    return meeting


async def create_meeting(
    conn: psycopg.AsyncConnection,
    *,
    title: str,
    scheduled_start: str,
    scheduled_end: str | None = None,
    google_calendar_event_id: str | None = None,
    google_meet_url: str | None = None,
) -> dict:
    """Create a new meeting record."""
    cursor = await conn.execute(
        """
        INSERT INTO meetings (title, scheduled_start, scheduled_end,
                              google_calendar_event_id, google_meet_url)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING *
        """,
        [title, scheduled_start, scheduled_end, google_calendar_event_id, google_meet_url],
    )
    row = await cursor.fetchone()
    logger.info("Created meeting {} ({})", row["id"], title)
    return row


async def update_meeting(
    conn: psycopg.AsyncConnection,
    meeting_id: UUID,
    **fields: object,
) -> dict | None:
    """Update meeting fields."""
    allowed = {"title", "status", "actual_duration_seconds", "recording_url", "recording_storage_path"}
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not updates:
        return await get_meeting_by_id(conn, meeting_id)

    set_clause = ", ".join(f"{k} = %s" for k in updates)
    values = list(updates.values()) + [str(meeting_id)]

    cursor = await conn.execute(
        f"UPDATE meetings SET {set_clause}, updated_at = NOW() WHERE id = %s RETURNING *",
        values,
    )
    return await cursor.fetchone()


async def add_participant(
    conn: psycopg.AsyncConnection,
    meeting_id: UUID,
    *,
    name: str,
    email: str | None = None,
    role: str = "attendee",
) -> dict:
    """Add a participant to a meeting."""
    cursor = await conn.execute(
        """
        INSERT INTO meeting_participants (meeting_id, name, email, role)
        VALUES (%s, %s, %s, %s)
        RETURNING *
        """,
        [str(meeting_id), name, email, role],
    )
    return await cursor.fetchone()


async def link_meeting_deal(
    conn: psycopg.AsyncConnection,
    meeting_id: UUID,
    deal_id: UUID,
) -> None:
    """Link a meeting to a deal."""
    await conn.execute(
        """
        INSERT INTO meeting_deals (meeting_id, deal_id)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
        """,
        [str(meeting_id), str(deal_id)],
    )


async def get_transcript(
    conn: psycopg.AsyncConnection,
    meeting_id: UUID,
) -> list[dict]:
    """Fetch transcript segments for a meeting."""
    cursor = await conn.execute(
        "SELECT * FROM meeting_transcripts WHERE meeting_id = %s ORDER BY start_ms",
        [str(meeting_id)],
    )
    return await cursor.fetchall()


async def store_transcript_segment(
    conn: psycopg.AsyncConnection,
    meeting_id: UUID,
    *,
    speaker_name: str,
    speaker_email: str | None,
    text: str,
    start_ms: int,
    end_ms: int,
    confidence: float | None = None,
) -> dict:
    """Store a single transcript segment."""
    cursor = await conn.execute(
        """
        INSERT INTO meeting_transcripts
            (meeting_id, speaker_name, speaker_email, text, start_ms, end_ms, confidence)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING *
        """,
        [str(meeting_id), speaker_name, speaker_email, text, start_ms, end_ms, confidence],
    )
    return await cursor.fetchone()
