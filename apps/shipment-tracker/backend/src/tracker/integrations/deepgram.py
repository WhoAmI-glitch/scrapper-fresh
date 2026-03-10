"""Deepgram real-time transcription integration.

Provides WebSocket-based streaming transcription with speaker diarization.
"""

from __future__ import annotations

import json
from typing import AsyncIterator

from loguru import logger

try:
    import websockets
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False


DEEPGRAM_WS_URL = "wss://api.deepgram.com/v1/listen"


class DeepgramTranscriber:
    """Real-time transcription client using Deepgram's streaming API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._ws = None

    async def connect(
        self,
        *,
        language: str = "en",
        model: str = "nova-2",
        diarize: bool = True,
        punctuate: bool = True,
        smart_format: bool = True,
    ) -> None:
        """Open a WebSocket connection to Deepgram."""
        if not WS_AVAILABLE:
            raise RuntimeError("websockets package required for Deepgram transcription")

        params = (
            f"?language={language}"
            f"&model={model}"
            f"&diarize={str(diarize).lower()}"
            f"&punctuate={str(punctuate).lower()}"
            f"&smart_format={str(smart_format).lower()}"
        )
        url = f"{DEEPGRAM_WS_URL}{params}"

        self._ws = await websockets.connect(
            url,
            extra_headers={"Authorization": f"Token {self.api_key}"},
        )
        logger.info("Connected to Deepgram transcription service")

    async def send_audio(self, audio_data: bytes) -> None:
        """Send an audio chunk to Deepgram for transcription."""
        if self._ws is None:
            raise RuntimeError("Not connected. Call connect() first.")
        await self._ws.send(audio_data)

    async def receive_transcripts(self) -> AsyncIterator[dict]:
        """Yield transcript results from Deepgram.

        Each result contains:
        - transcript: str
        - confidence: float
        - speaker: int (speaker index from diarization)
        - start: float (seconds)
        - end: float (seconds)
        - is_final: bool
        """
        if self._ws is None:
            raise RuntimeError("Not connected. Call connect() first.")

        async for message in self._ws:
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                continue

            # Extract from Deepgram response format
            channel = data.get("channel", {})
            alternatives = channel.get("alternatives", [])
            if not alternatives:
                continue

            alt = alternatives[0]
            transcript = alt.get("transcript", "").strip()
            if not transcript:
                continue

            # Get word-level diarization info
            words = alt.get("words", [])
            speaker = words[0].get("speaker", 0) if words else 0
            start_time = words[0].get("start", 0.0) if words else 0.0
            end_time = words[-1].get("end", 0.0) if words else 0.0

            yield {
                "transcript": transcript,
                "confidence": alt.get("confidence", 0.0),
                "speaker": speaker,
                "start": start_time,
                "end": end_time,
                "is_final": data.get("is_final", False),
            }

    async def close(self) -> None:
        """Close the WebSocket connection."""
        if self._ws is not None:
            await self._ws.close()
            self._ws = None
            logger.info("Disconnected from Deepgram")
