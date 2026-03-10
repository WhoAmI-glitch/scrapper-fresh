"""Meeting CRUD and intelligence endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from tracker.db import get_conn
from tracker.schemas.meetings import (
    MeetingCreate,
    MeetingUpdate,
    MeetingResponse,
    MeetingListResponse,
    ActionItemCreate,
    ActionItemResponse,
    TranscriptSegment,
)
from tracker.services.meeting_service import (
    get_meetings,
    get_meeting_by_id,
    create_meeting,
    update_meeting,
    get_transcript,
)

router = APIRouter()


def _build_meeting_response(meeting: dict) -> MeetingResponse:
    """Convert a meeting dict to a MeetingResponse."""
    return MeetingResponse(
        id=meeting["id"],
        title=meeting["title"],
        scheduled_start=meeting["scheduled_start"],
        scheduled_end=meeting.get("scheduled_end"),
        actual_duration_seconds=meeting.get("actual_duration_seconds"),
        google_calendar_event_id=meeting.get("google_calendar_event_id"),
        google_meet_url=meeting.get("google_meet_url"),
        status=meeting["status"],
        recording_url=meeting.get("recording_url"),
        participants=meeting.get("participants", []),
        summary=meeting.get("summary"),
        action_items=meeting.get("action_items", []),
        linked_deal_ids=meeting.get("linked_deal_ids", []),
        created_at=meeting["created_at"],
        updated_at=meeting["updated_at"],
    )


@router.get("", response_model=MeetingListResponse)
async def list_meetings(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
) -> MeetingListResponse:
    """List meetings with pagination."""
    async with get_conn() as conn:
        rows, total = await get_meetings(conn, page=page, page_size=page_size, status=status)

    items = []
    for row in rows:
        items.append(MeetingResponse(
            id=row["id"],
            title=row["title"],
            scheduled_start=row["scheduled_start"],
            scheduled_end=row.get("scheduled_end"),
            actual_duration_seconds=row.get("actual_duration_seconds"),
            google_calendar_event_id=row.get("google_calendar_event_id"),
            google_meet_url=row.get("google_meet_url"),
            status=row["status"],
            recording_url=row.get("recording_url"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        ))

    return MeetingListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(meeting_id: UUID) -> MeetingResponse:
    """Get a single meeting with all related data."""
    async with get_conn() as conn:
        meeting = await get_meeting_by_id(conn, meeting_id)

    if meeting is None:
        raise HTTPException(status_code=404, detail=f"Meeting {meeting_id} not found")

    return _build_meeting_response(meeting)


@router.post("", response_model=MeetingResponse, status_code=201)
async def create_meeting_endpoint(body: MeetingCreate) -> MeetingResponse:
    """Create a new meeting."""
    async with get_conn() as conn:
        meeting = await create_meeting(
            conn,
            title=body.title,
            scheduled_start=body.scheduled_start.isoformat(),
            scheduled_end=body.scheduled_end.isoformat() if body.scheduled_end else None,
            google_calendar_event_id=body.google_calendar_event_id,
            google_meet_url=body.google_meet_url,
        )

    return MeetingResponse(
        id=meeting["id"],
        title=meeting["title"],
        scheduled_start=meeting["scheduled_start"],
        scheduled_end=meeting.get("scheduled_end"),
        status=meeting["status"],
        created_at=meeting["created_at"],
        updated_at=meeting["updated_at"],
    )


@router.patch("/{meeting_id}", response_model=MeetingResponse)
async def update_meeting_endpoint(meeting_id: UUID, body: MeetingUpdate) -> MeetingResponse:
    """Update a meeting."""
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    async with get_conn() as conn:
        row = await update_meeting(conn, meeting_id, **updates)
        if row is None:
            raise HTTPException(status_code=404, detail=f"Meeting {meeting_id} not found")
        meeting = await get_meeting_by_id(conn, meeting_id)

    return _build_meeting_response(meeting)


@router.get("/{meeting_id}/transcript", response_model=list[TranscriptSegment])
async def get_meeting_transcript(meeting_id: UUID) -> list[TranscriptSegment]:
    """Get transcript segments for a meeting."""
    async with get_conn() as conn:
        segments = await get_transcript(conn, meeting_id)

    return [
        TranscriptSegment(
            id=s["id"],
            speaker_name=s["speaker_name"],
            speaker_email=s.get("speaker_email"),
            text=s["text"],
            start_ms=s["start_ms"],
            end_ms=s["end_ms"],
            confidence=s.get("confidence"),
            sentiment=s.get("sentiment"),
        )
        for s in segments
    ]


@router.get("/{meeting_id}/action-items", response_model=list[ActionItemResponse])
async def get_meeting_action_items(meeting_id: UUID) -> list[ActionItemResponse]:
    """Get action items for a meeting."""
    async with get_conn() as conn:
        cursor = await conn.execute(
            "SELECT * FROM action_items WHERE meeting_id = %s ORDER BY created_at",
            [str(meeting_id)],
        )
        rows = await cursor.fetchall()

    return [ActionItemResponse(**row) for row in rows]


@router.post("/action-items", response_model=ActionItemResponse, status_code=201)
async def create_action_item(body: ActionItemCreate) -> ActionItemResponse:
    """Create a manual action item."""
    async with get_conn() as conn:
        cursor = await conn.execute(
            """
            INSERT INTO action_items (title, description, assignee_name, assignee_email,
                                      due_date, meeting_id, deal_id, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'manual')
            RETURNING *
            """,
            [
                body.title,
                body.description,
                body.assignee_name,
                body.assignee_email,
                str(body.due_date) if body.due_date else None,
                str(body.meeting_id) if body.meeting_id else None,
                str(body.deal_id) if body.deal_id else None,
            ],
        )
        row = await cursor.fetchone()

    return ActionItemResponse(**row)
