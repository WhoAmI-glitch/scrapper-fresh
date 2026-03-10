"""AI-powered meeting intelligence extraction using Claude.

Processes meeting transcripts through a multi-stage pipeline:
1. Structured summary extraction
2. Action item detection
3. Deal update proposals
4. Market intelligence capture
"""

from __future__ import annotations

import json
from uuid import UUID

from loguru import logger

from tracker.integrations.anthropic import AnthropicClient

SYSTEM_PROMPT = """You are an expert trade intelligence analyst specializing in the charcoal commodity market.
You analyze meeting transcripts between traders, brokers, and counterparties to extract actionable intelligence.

You MUST respond with valid JSON only, no other text. Follow the exact schema requested."""

EXTRACTION_PROMPT = """Analyze this trading meeting transcript and extract structured intelligence.

<transcript>
{transcript}
</transcript>

Return a JSON object with this exact schema:
{{
  "summary": {{
    "text": "2-4 sentence executive summary of the meeting",
    "key_decisions": ["list of concrete decisions made"],
    "market_intelligence": ["list of market insights, price signals, supply/demand info"]
  }},
  "action_items": [
    {{
      "title": "clear action title",
      "description": "detailed description",
      "assignee_name": "person responsible or null",
      "due_date": "YYYY-MM-DD or null",
      "priority": "urgent|high|medium|low",
      "deal_related": true
    }}
  ],
  "deal_updates": [
    {{
      "contract_id": "referenced contract/deal ID if mentioned, or null",
      "field": "status|price_per_ton|quantity_tons|payment_terms|notes|risk_notes|laycan_start|laycan_end",
      "current_value_mentioned": "what they said the current value is",
      "proposed_value": "new value discussed",
      "confidence": 0.0-1.0,
      "reasoning": "why this update was proposed based on the transcript"
    }}
  ],
  "participant_insights": [
    {{
      "name": "participant name",
      "sentiment": "positive|neutral|negative|mixed",
      "key_statements": ["notable quotes or positions taken"]
    }}
  ],
  "risks_identified": ["list of risks or concerns raised"],
  "follow_up_meetings": ["any mentioned follow-up meetings or deadlines"]
}}

Extract ALL actionable intelligence. Be thorough but precise. Only include items that are clearly supported by the transcript content."""


async def extract_meeting_intelligence(
    conn,
    meeting_id: UUID,
    transcript: str,
) -> dict:
    """Run the full AI extraction pipeline on a meeting transcript.

    Returns the extracted intelligence dict. Also persists results to the database.
    """
    client = AnthropicClient()

    logger.info("Starting AI extraction for meeting {}", meeting_id)

    # Step 1: Extract structured intelligence
    intelligence = await client.extract_json(
        system=SYSTEM_PROMPT,
        user_message=EXTRACTION_PROMPT.format(transcript=transcript),
        max_tokens=8192,
    )

    if intelligence.get("parse_error"):
        logger.warning("AI extraction returned unparseable response for meeting {}", meeting_id)
        return intelligence

    # Step 2: Store meeting summary
    summary_data = intelligence.get("summary", {})
    if summary_data:
        await _store_summary(conn, meeting_id, summary_data, client.model)

    # Step 3: Store action items
    action_items = intelligence.get("action_items", [])
    for item in action_items:
        await _store_action_item(conn, meeting_id, item)

    # Step 4: Create AI deal update proposals
    deal_updates = intelligence.get("deal_updates", [])
    for update in deal_updates:
        await _store_deal_update_proposal(conn, meeting_id, update)

    # Step 5: Store participant insights
    participant_insights = intelligence.get("participant_insights", [])
    for insight in participant_insights:
        await _update_participant_sentiment(conn, meeting_id, insight)

    logger.info(
        "AI extraction complete for meeting {}: {} action items, {} deal updates",
        meeting_id,
        len(action_items),
        len(deal_updates),
    )

    return intelligence


async def _store_summary(conn, meeting_id: UUID, summary: dict, model: str) -> None:
    """Persist the AI-generated meeting summary."""
    await conn.execute(
        """
        INSERT INTO meeting_summaries (meeting_id, summary_text, decisions, market_intelligence, model_used)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (meeting_id) DO UPDATE SET
            summary_text = EXCLUDED.summary_text,
            decisions = EXCLUDED.decisions,
            market_intelligence = EXCLUDED.market_intelligence,
            model_used = EXCLUDED.model_used,
            generated_at = NOW()
        """,
        [
            str(meeting_id),
            summary.get("text", ""),
            json.dumps(summary.get("key_decisions", [])),
            json.dumps(summary.get("market_intelligence", [])),
            model,
        ],
    )
    logger.debug("Stored summary for meeting {}", meeting_id)


async def _store_action_item(conn, meeting_id: UUID, item: dict) -> None:
    """Persist an AI-extracted action item."""
    priority = item.get("priority", "medium")
    if priority not in ("urgent", "high", "medium", "low"):
        priority = "medium"

    await conn.execute(
        """
        INSERT INTO action_items (
            meeting_id, title, description, assignee_name,
            due_date, priority, source, confidence
        ) VALUES (%s, %s, %s, %s, %s, %s, 'ai', 0.8)
        """,
        [
            str(meeting_id),
            item.get("title", "Untitled action"),
            item.get("description"),
            item.get("assignee_name"),
            item.get("due_date"),
            priority,
        ],
    )


async def _store_deal_update_proposal(conn, meeting_id: UUID, update: dict) -> None:
    """Create an AI deal update proposal for human review."""
    contract_id = update.get("contract_id")
    if not contract_id:
        return

    # Find the deal by contract_id
    cursor = await conn.execute(
        "SELECT id FROM deals WHERE contract_id = %s",
        [contract_id],
    )
    row = await cursor.fetchone()
    if not row:
        logger.debug("Deal not found for contract_id {}", contract_id)
        return

    deal_id = row["id"]
    confidence = min(max(float(update.get("confidence", 0.5)), 0.0), 1.0)

    await conn.execute(
        """
        INSERT INTO ai_deal_updates (
            meeting_id, deal_id, field_name, old_value,
            proposed_value, confidence, reasoning
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        [
            str(meeting_id),
            str(deal_id),
            update.get("field", "notes"),
            update.get("current_value_mentioned"),
            update.get("proposed_value", ""),
            confidence,
            update.get("reasoning", ""),
        ],
    )


async def _update_participant_sentiment(conn, meeting_id: UUID, insight: dict) -> None:
    """Update participant sentiment score based on AI analysis."""
    sentiment_map = {"positive": 0.8, "neutral": 0.5, "negative": 0.2, "mixed": 0.5}
    sentiment_name = insight.get("sentiment", "neutral")
    score = sentiment_map.get(sentiment_name, 0.5)

    name = insight.get("name")
    if not name:
        return

    await conn.execute(
        """
        UPDATE meeting_participants SET sentiment_score = %s
        WHERE meeting_id = %s AND name ILIKE %s
        """,
        [score, str(meeting_id), f"%{name}%"],
    )


async def generate_pre_meeting_briefing(conn, meeting_id: UUID) -> dict:
    """Generate a pre-meeting briefing with context from related deals and past meetings.

    Pulls deal history, recent action items, and past meeting summaries
    for all participants to help prepare for the upcoming meeting.
    """
    # Get meeting details
    cursor = await conn.execute(
        "SELECT * FROM meetings WHERE id = %s",
        [str(meeting_id)],
    )
    meeting = await cursor.fetchone()
    if not meeting:
        return {"error": "Meeting not found"}

    # Get participants
    cursor = await conn.execute(
        "SELECT name, email, role FROM meeting_participants WHERE meeting_id = %s",
        [str(meeting_id)],
    )
    participants = await cursor.fetchall()

    # Get linked deals
    cursor = await conn.execute(
        """
        SELECT d.contract_id, d.commodity, d.buyer, d.seller, d.status,
               d.quantity_tons, d.price_per_ton, d.contract_value, d.risk_notes
        FROM deals d
        JOIN meeting_deals md ON d.id = md.deal_id
        WHERE md.meeting_id = %s
        """,
        [str(meeting_id)],
    )
    deals = await cursor.fetchall()

    # Get open action items for participants
    participant_emails = [p["email"] for p in participants if p.get("email")]
    open_actions = []
    if participant_emails:
        placeholders = ", ".join(["%s"] * len(participant_emails))
        cursor = await conn.execute(
            f"""
            SELECT title, assignee_name, due_date, priority, status
            FROM action_items
            WHERE assignee_email IN ({placeholders})
            AND status IN ('open', 'in_progress')
            ORDER BY due_date ASC NULLS LAST
            LIMIT 20
            """,
            participant_emails,
        )
        open_actions = await cursor.fetchall()

    # Get past meeting summaries with same participants
    past_summaries = []
    if participant_emails:
        placeholders = ", ".join(["%s"] * len(participant_emails))
        cursor = await conn.execute(
            f"""
            SELECT ms.summary_text, ms.decisions, m.title, m.scheduled_start
            FROM meeting_summaries ms
            JOIN meetings m ON m.id = ms.meeting_id
            WHERE ms.meeting_id IN (
                SELECT mp.meeting_id FROM meeting_participants mp
                WHERE mp.email IN ({placeholders})
            )
            AND ms.meeting_id != %s
            ORDER BY m.scheduled_start DESC
            LIMIT 5
            """,
            [*participant_emails, str(meeting_id)],
        )
        past_summaries = await cursor.fetchall()

    # Build briefing context
    context_parts = [
        f"Meeting: {meeting['title']}",
        f"Scheduled: {meeting['scheduled_start']}",
        f"Participants: {', '.join(p['name'] for p in participants)}",
    ]

    if deals:
        context_parts.append("\n--- Related Deals ---")
        for d in deals:
            context_parts.append(
                f"  {d['contract_id']}: {d['commodity']} "
                f"({d['buyer']} → {d['seller']}) "
                f"Status={d['status']}, "
                f"{d['quantity_tons']}t @ ${d['price_per_ton']}/t"
            )
            if d.get("risk_notes"):
                context_parts.append(f"    Risks: {d['risk_notes']}")

    if open_actions:
        context_parts.append("\n--- Open Action Items ---")
        for a in open_actions:
            context_parts.append(
                f"  [{a['priority']}] {a['title']} "
                f"(assigned: {a['assignee_name']}, due: {a['due_date']})"
            )

    if past_summaries:
        context_parts.append("\n--- Recent Meeting History ---")
        for s in past_summaries:
            context_parts.append(f"  {s['title']} ({s['scheduled_start']})")
            context_parts.append(f"    {s['summary_text'][:200]}")

    context = "\n".join(context_parts)

    # Generate briefing via AI
    client = AnthropicClient()
    briefing_prompt = f"""Based on this meeting context, generate a concise pre-meeting briefing.

{context}

Return a JSON object:
{{
  "executive_summary": "1-2 sentence overview of what this meeting is about and what to expect",
  "key_topics": ["list of expected discussion topics"],
  "talking_points": ["suggested points to raise"],
  "open_questions": ["unresolved questions from previous interactions"],
  "deal_status_snapshot": [
    {{
      "contract_id": "...",
      "status": "...",
      "key_concern": "main issue to address"
    }}
  ],
  "preparation_notes": "any prep work recommended before the meeting"
}}"""

    briefing = await client.extract_json(
        system=SYSTEM_PROMPT,
        user_message=briefing_prompt,
        max_tokens=4096,
    )

    return briefing


async def approve_deal_update(conn, update_id: UUID, approved_by: str) -> bool:
    """Approve and apply an AI-proposed deal update."""
    cursor = await conn.execute(
        "SELECT * FROM ai_deal_updates WHERE id = %s AND status = 'pending'",
        [str(update_id)],
    )
    update = await cursor.fetchone()
    if not update:
        return False

    # Apply the update to the deal
    field = update["field_name"]
    allowed_fields = {
        "status", "price_per_ton", "quantity_tons", "payment_terms",
        "notes", "risk_notes", "laycan_start", "laycan_end",
    }
    if field not in allowed_fields:
        logger.warning("AI tried to update disallowed field: {}", field)
        return False

    await conn.execute(
        f"UPDATE deals SET {field} = %s, ai_last_updated_at = NOW(), ai_update_count = COALESCE(ai_update_count, 0) + 1 WHERE id = %s",
        [update["proposed_value"], str(update["deal_id"])],
    )

    # Mark update as approved
    await conn.execute(
        "UPDATE ai_deal_updates SET status = 'approved', reviewed_by = %s, reviewed_at = NOW() WHERE id = %s",
        [approved_by, str(update_id)],
    )

    logger.info("AI deal update {} approved by {}", update_id, approved_by)
    return True


async def reject_deal_update(conn, update_id: UUID, rejected_by: str) -> bool:
    """Reject an AI-proposed deal update."""
    result = await conn.execute(
        "UPDATE ai_deal_updates SET status = 'rejected', reviewed_by = %s, reviewed_at = NOW() WHERE id = %s AND status = 'pending'",
        [rejected_by, str(update_id)],
    )
    return result.rowcount > 0
