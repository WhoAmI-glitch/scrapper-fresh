"""AI Intelligence API endpoints.

Provides endpoints for:
- AI deal update approval/rejection
- Pre-meeting briefings
- Semantic search across meeting memory
- Meeting re-processing
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel

from tracker.db import get_conn
from tracker.services.ai_extractor import (
    approve_deal_update,
    reject_deal_update,
    generate_pre_meeting_briefing,
)
from tracker.services.memory_service import search_meeting_memory

router = APIRouter()


class DealUpdateAction(BaseModel):
    reviewer: str = "admin"


@router.get("/deal-updates")
async def list_pending_deal_updates(
    status: str = Query("pending", pattern="^(pending|approved|rejected|all)$"),
    limit: int = Query(50, ge=1, le=200),
):
    """List AI-proposed deal updates, optionally filtered by status."""
    async with get_conn() as conn:
        status_filter = ""
        params: list = [limit]
        if status != "all":
            status_filter = "WHERE adu.status = %s"
            params = [status, limit]

        cursor = await conn.execute(
            f"""
            SELECT
                adu.*,
                d.contract_id,
                d.commodity,
                d.buyer,
                d.seller,
                m.title as meeting_title,
                m.scheduled_start as meeting_date
            FROM ai_deal_updates adu
            JOIN deals d ON d.id = adu.deal_id
            JOIN meetings m ON m.id = adu.meeting_id
            {status_filter}
            ORDER BY adu.created_at DESC
            LIMIT %s
            """,
            params,
        )
        rows = await cursor.fetchall()

    return {
        "items": [
            {
                "id": str(r["id"]),
                "meeting_id": str(r["meeting_id"]),
                "deal_id": str(r["deal_id"]),
                "contract_id": r["contract_id"],
                "commodity": r["commodity"],
                "buyer": r["buyer"],
                "seller": r["seller"],
                "meeting_title": r["meeting_title"],
                "meeting_date": str(r["meeting_date"]) if r["meeting_date"] else None,
                "field_name": r["field_name"],
                "old_value": r["old_value"],
                "proposed_value": r["proposed_value"],
                "confidence": float(r["confidence"]),
                "reasoning": r["reasoning"],
                "status": r["status"],
                "created_at": str(r["created_at"]),
            }
            for r in rows
        ],
        "count": len(rows),
    }


@router.post("/deal-updates/{update_id}/approve")
async def approve_update(update_id: UUID, body: DealUpdateAction):
    """Approve an AI-proposed deal update and apply it."""
    async with get_conn() as conn:
        success = await approve_deal_update(conn, update_id, body.reviewer)
    if not success:
        raise HTTPException(404, "Update not found or already reviewed")
    return {"status": "approved", "id": str(update_id)}


@router.post("/deal-updates/{update_id}/reject")
async def reject_update(update_id: UUID, body: DealUpdateAction):
    """Reject an AI-proposed deal update."""
    async with get_conn() as conn:
        success = await reject_deal_update(conn, update_id, body.reviewer)
    if not success:
        raise HTTPException(404, "Update not found or already reviewed")
    return {"status": "rejected", "id": str(update_id)}


@router.get("/briefing/{meeting_id}")
async def get_pre_meeting_briefing(meeting_id: UUID):
    """Generate a pre-meeting briefing with context from deals and history."""
    async with get_conn() as conn:
        briefing = await generate_pre_meeting_briefing(conn, meeting_id)
    if briefing.get("error"):
        raise HTTPException(404, briefing["error"])
    return briefing


@router.get("/memory/search")
async def search_memory(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    meeting_id: UUID | None = Query(None),
):
    """Semantic search across meeting transcripts and summaries."""
    async with get_conn() as conn:
        results = await search_meeting_memory(
            conn, query=q, limit=limit, meeting_id=meeting_id
        )
    return {"query": q, "results": results, "count": len(results)}


@router.post("/meetings/{meeting_id}/reprocess")
async def reprocess_meeting(meeting_id: UUID):
    """Trigger re-processing of a meeting transcript through the AI pipeline."""
    from tracker.workers.transcript_worker import process_meeting_transcript

    async with get_conn() as conn:
        cursor = await conn.execute(
            "SELECT id, status FROM meetings WHERE id = %s",
            [str(meeting_id)],
        )
        meeting = await cursor.fetchone()
        if not meeting:
            raise HTTPException(404, "Meeting not found")

        # Reset to processing status
        await conn.execute(
            "UPDATE meetings SET status = 'processing' WHERE id = %s",
            [str(meeting_id)],
        )

    # Trigger async processing
    import asyncio
    asyncio.create_task(process_meeting_transcript(meeting_id))

    return {"status": "reprocessing", "meeting_id": str(meeting_id)}
