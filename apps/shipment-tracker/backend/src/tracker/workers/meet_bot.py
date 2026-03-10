"""Google Meet bot worker.

Manages the lifecycle of a headless browser that joins Google Meet calls
to capture audio for transcription. Uses Playwright in a Docker container.

NOTE: This is infrastructure scaffolding. The actual browser automation
requires a Docker container with Playwright and a pre-authenticated
Google session (storageState). See the deployment docs for setup.
"""

from __future__ import annotations

import asyncio
from uuid import UUID

from loguru import logger

from tracker.db import get_conn
from tracker.services.meeting_service import update_meeting


class MeetBotManager:
    """Manages Google Meet bot instances."""

    def __init__(self):
        self._active_bots: dict[str, asyncio.Task] = {}

    async def join_meeting(self, meeting_id: UUID, meet_url: str) -> None:
        """Start a bot to join a Google Meet call.

        In production, this would:
        1. Spawn a Docker container with Playwright/Chromium
        2. Load pre-authenticated Google session
        3. Navigate to the Meet URL
        4. Join the call (click "Join" button, dismiss camera/mic)
        5. Enable captions via DOM injection
        6. Open Deepgram WebSocket for real-time transcription
        7. Pipe browser audio to Deepgram
        8. Store transcript segments to DB
        9. Detect meeting end
        10. Update meeting status to 'processing'
        """
        task_key = str(meeting_id)

        if task_key in self._active_bots:
            logger.warning("Bot already active for meeting {}", meeting_id)
            return

        logger.info(
            "Meet bot join requested for meeting {} at {}. "
            "Bot infrastructure requires Docker + Playwright setup.",
            meeting_id,
            meet_url,
        )

        # Update meeting status to in_progress
        async with get_conn() as conn:
            await update_meeting(conn, meeting_id, status="in_progress")

    async def leave_meeting(self, meeting_id: UUID) -> None:
        """Stop the bot for a specific meeting."""
        task_key = str(meeting_id)

        if task_key in self._active_bots:
            self._active_bots[task_key].cancel()
            del self._active_bots[task_key]
            logger.info("Bot stopped for meeting {}", meeting_id)

        async with get_conn() as conn:
            await update_meeting(conn, meeting_id, status="processing")

    async def shutdown(self) -> None:
        """Stop all active bots."""
        for task_key, task in list(self._active_bots.items()):
            task.cancel()
        self._active_bots.clear()
        logger.info("All meet bots stopped")


# Singleton instance
meet_bot_manager = MeetBotManager()
