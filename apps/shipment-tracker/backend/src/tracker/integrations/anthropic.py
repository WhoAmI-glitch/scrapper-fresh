"""Anthropic Claude API integration for AI extraction and summarization."""

from __future__ import annotations

import json

import httpx
from loguru import logger

from tracker.config import get_settings

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-4-5-20250514"


class AnthropicClient:
    """Client for the Anthropic Messages API."""

    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL):
        self.api_key = api_key or get_settings().anthropic_api_key
        self.model = model

    async def generate(
        self,
        *,
        system: str,
        user_message: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> str:
        """Send a message to Claude and return the text response."""
        if not self.api_key:
            logger.warning("Anthropic API key not configured. Returning mock response.")
            return '{"summary": "Mock summary - configure TRACKER_ANTHROPIC_API_KEY for real AI"}'

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                ANTHROPIC_API_URL,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "system": system,
                    "messages": [{"role": "user", "content": user_message}],
                },
            )
            response.raise_for_status()
            data = response.json()

        # Extract text from response
        content_blocks = data.get("content", [])
        text_parts = [b["text"] for b in content_blocks if b.get("type") == "text"]
        return "\n".join(text_parts)

    async def extract_json(
        self,
        *,
        system: str,
        user_message: str,
        max_tokens: int = 4096,
    ) -> dict:
        """Send a message and parse the response as JSON."""
        text = await self.generate(
            system=system,
            user_message=user_message,
            max_tokens=max_tokens,
            temperature=0.1,
        )

        # Try to extract JSON from the response
        # Claude sometimes wraps JSON in ```json ... ``` blocks
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last lines (```json and ```)
            json_lines = []
            in_block = False
            for line in lines:
                if line.startswith("```") and not in_block:
                    in_block = True
                    continue
                if line.startswith("```") and in_block:
                    break
                json_lines.append(line)
            text = "\n".join(json_lines)

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse Claude response as JSON")
            return {"raw_text": text, "parse_error": True}
