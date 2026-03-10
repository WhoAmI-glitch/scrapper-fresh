"""Post-meeting transcript processing pipeline.

Handles the full pipeline: assembly, AI extraction, action items,
deal update proposals, and embedding generation.
"""

from __future__ import annotations

from uuid import UUID

from loguru import logger

from tracker.db import get_conn
from tracker.services.meeting_service import get_transcript, update_meeting


async def process_meeting_transcript(meeting_id: UUID) -> None:
    """Process a complete meeting transcript through the AI pipeline.

    Steps:
    1. Assemble full transcript from segments
    2. Send to Claude for structured extraction
    3. Store meeting summary
    4. Create action items
    5. Create AI deal update proposals
    6. Generate embeddings for memory
    7. Finalize meeting status

    This function is called when a meeting transitions to 'processing' status.
    The actual AI processing is implemented in Phase 4 (ai_extractor).
    """
    logger.info("Processing transcript for meeting {}", meeting_id)

    async with get_conn() as conn:
        # Step 1: Assemble transcript
        segments = await get_transcript(conn, meeting_id)
        if not segments:
            logger.warning("No transcript segments found for meeting {}", meeting_id)
            await update_meeting(conn, meeting_id, status="failed")
            return

        # Assemble full text with speaker labels
        full_text_parts = []
        for seg in segments:
            timestamp = f"{seg['start_ms'] // 60000:02d}:{(seg['start_ms'] % 60000) // 1000:02d}"
            full_text_parts.append(f"[{seg['speaker_name']} {timestamp}] {seg['text']}")

        full_transcript = "\n".join(full_text_parts)
        logger.info(
            "Assembled transcript: {} segments, {} chars",
            len(segments),
            len(full_transcript),
        )

        # Steps 2-5: AI extraction (summary, action items, deal updates)
        try:
            from tracker.services.ai_extractor import extract_meeting_intelligence
            await extract_meeting_intelligence(conn, meeting_id, full_transcript)
        except ImportError:
            logger.info("AI extractor not available. Skipping AI processing.")
        except Exception as e:
            logger.error("AI extraction failed for meeting {}: {}", meeting_id, e)

        # Step 6: Generate embeddings for semantic search
        try:
            from tracker.services.memory_service import index_meeting_for_search
            chunks_indexed = await index_meeting_for_search(conn, meeting_id, full_transcript)
            logger.info("Indexed {} chunks for meeting {}", chunks_indexed, meeting_id)
        except Exception as e:
            logger.error("Embedding generation failed for meeting {}: {}", meeting_id, e)

        # Step 7: Finalize
        await update_meeting(conn, meeting_id, status="completed")
        logger.info("Meeting {} processing complete", meeting_id)
