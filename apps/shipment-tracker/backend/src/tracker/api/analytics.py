"""Cross-platform analytics endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from tracker.db import get_conn
from tracker.services.analytics_service import (
    get_meeting_analytics,
    get_participant_activity,
    get_deal_intelligence_summary,
)

router = APIRouter()


@router.get("/meetings")
async def meeting_analytics():
    """Get aggregate meeting, action item, and AI update analytics."""
    async with get_conn() as conn:
        return await get_meeting_analytics(conn)


@router.get("/participants")
async def participant_activity(limit: int = 20):
    """Get most active meeting participants with sentiment data."""
    async with get_conn() as conn:
        return await get_participant_activity(conn, limit)


@router.get("/deal-intelligence")
async def deal_intelligence():
    """Get deals ranked by AI activity and intelligence gathered."""
    async with get_conn() as conn:
        return await get_deal_intelligence_summary(conn)
