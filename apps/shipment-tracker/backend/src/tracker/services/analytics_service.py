"""Cross-meeting and platform analytics service.

Aggregates data across meetings, deals, and shipments to provide
dashboard metrics and trend analysis.
"""

from __future__ import annotations

from loguru import logger


async def get_meeting_analytics(conn) -> dict:
    """Get aggregate meeting analytics."""
    cursor = await conn.execute(
        """
        SELECT
            COUNT(*) as total_meetings,
            COUNT(*) FILTER (WHERE status = 'completed') as completed,
            COUNT(*) FILTER (WHERE status = 'scheduled') as scheduled,
            COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress,
            AVG(actual_duration_seconds) FILTER (WHERE actual_duration_seconds > 0) as avg_duration_secs
        FROM meetings
        """
    )
    row = await cursor.fetchone()

    # Action item stats
    cursor = await conn.execute(
        """
        SELECT
            COUNT(*) as total_items,
            COUNT(*) FILTER (WHERE status = 'open') as open_items,
            COUNT(*) FILTER (WHERE status = 'done') as done_items,
            COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress_items,
            COUNT(*) FILTER (WHERE due_date < CURRENT_DATE AND status IN ('open', 'in_progress')) as overdue_items
        FROM action_items
        """
    )
    action_row = await cursor.fetchone()

    # AI update stats
    cursor = await conn.execute(
        """
        SELECT
            COUNT(*) as total_proposals,
            COUNT(*) FILTER (WHERE status = 'pending') as pending,
            COUNT(*) FILTER (WHERE status = 'approved') as approved,
            COUNT(*) FILTER (WHERE status = 'rejected') as rejected,
            AVG(confidence) as avg_confidence
        FROM ai_deal_updates
        """
    )
    ai_row = await cursor.fetchone()

    return {
        "meetings": {
            "total": row["total_meetings"],
            "completed": row["completed"],
            "scheduled": row["scheduled"],
            "in_progress": row["in_progress"],
            "avg_duration_minutes": round((row["avg_duration_secs"] or 0) / 60, 1),
        },
        "action_items": {
            "total": action_row["total_items"],
            "open": action_row["open_items"],
            "done": action_row["done_items"],
            "in_progress": action_row["in_progress_items"],
            "overdue": action_row["overdue_items"],
            "completion_rate": round(
                action_row["done_items"] / max(action_row["total_items"], 1) * 100, 1
            ),
        },
        "ai_updates": {
            "total_proposals": ai_row["total_proposals"],
            "pending": ai_row["pending"],
            "approved": ai_row["approved"],
            "rejected": ai_row["rejected"],
            "approval_rate": round(
                ai_row["approved"] / max(ai_row["approved"] + ai_row["rejected"], 1) * 100, 1
            ),
            "avg_confidence": round(float(ai_row["avg_confidence"] or 0), 3),
        },
    }


async def get_participant_activity(conn, limit: int = 20) -> list[dict]:
    """Get most active meeting participants."""
    cursor = await conn.execute(
        """
        SELECT
            mp.name,
            mp.email,
            COUNT(DISTINCT mp.meeting_id) as meeting_count,
            AVG(mp.sentiment_score) as avg_sentiment,
            COUNT(DISTINCT ai.id) FILTER (WHERE ai.assignee_name ILIKE '%%' || mp.name || '%%') as action_items_assigned
        FROM meeting_participants mp
        LEFT JOIN action_items ai ON ai.meeting_id = mp.meeting_id
        GROUP BY mp.name, mp.email
        ORDER BY meeting_count DESC
        LIMIT %s
        """,
        [limit],
    )
    rows = await cursor.fetchall()

    return [
        {
            "name": r["name"],
            "email": r["email"],
            "meeting_count": r["meeting_count"],
            "avg_sentiment": round(float(r["avg_sentiment"] or 0.5), 2),
            "action_items_assigned": r["action_items_assigned"],
        }
        for r in rows
    ]


async def get_deal_intelligence_summary(conn) -> list[dict]:
    """Get deals with the most AI activity and intelligence gathered."""
    cursor = await conn.execute(
        """
        SELECT
            d.id, d.contract_id, d.commodity, d.buyer, d.seller, d.status,
            d.contract_value, d.ai_update_count,
            COUNT(DISTINCT md.meeting_id) as meeting_count,
            COUNT(DISTINCT adu.id) as ai_proposals,
            COUNT(DISTINCT adu.id) FILTER (WHERE adu.status = 'approved') as approved_updates
        FROM deals d
        LEFT JOIN meeting_deals md ON d.id = md.deal_id
        LEFT JOIN ai_deal_updates adu ON d.id = adu.deal_id
        WHERE d.status NOT IN ('cancelled')
        GROUP BY d.id
        HAVING COUNT(DISTINCT md.meeting_id) > 0 OR COUNT(DISTINCT adu.id) > 0
        ORDER BY meeting_count DESC, ai_proposals DESC
        LIMIT 20
        """,
    )
    rows = await cursor.fetchall()

    return [
        {
            "deal_id": str(r["id"]),
            "contract_id": r["contract_id"],
            "commodity": r["commodity"],
            "buyer": r["buyer"],
            "seller": r["seller"],
            "status": r["status"],
            "contract_value": float(r["contract_value"]),
            "meeting_count": r["meeting_count"],
            "ai_proposals": r["ai_proposals"],
            "approved_updates": r["approved_updates"],
            "ai_update_count": r["ai_update_count"] or 0,
        }
        for r in rows
    ]
