"""Meeting memory service using pgvector embeddings.

Provides semantic search across meeting transcripts and summaries
to surface relevant context for pre-meeting briefings and deal analysis.
"""

from __future__ import annotations

import hashlib
import json
from uuid import UUID

import httpx
from loguru import logger

from tracker.config import get_settings


# We use a simple embedding approach: hash-based pseudo-embeddings for development,
# real embeddings via Anthropic/OpenAI in production.
EMBEDDING_DIM = 1536


async def generate_embedding(text: str) -> list[float]:
    """Generate an embedding vector for the given text.

    In production, this would call an embedding API (e.g., OpenAI text-embedding-3-small).
    For development, we generate a deterministic pseudo-embedding from the text hash.
    """
    settings = get_settings()

    # If we have an API key, use a real embedding service
    if settings.anthropic_api_key:
        try:
            return await _real_embedding(text)
        except Exception as e:
            logger.warning("Embedding API failed, falling back to hash: {}", e)

    return _hash_embedding(text)


def _hash_embedding(text: str) -> list[float]:
    """Generate a deterministic pseudo-embedding from text hash.

    NOT suitable for real semantic search, but provides consistent
    vectors for development and testing.
    """
    # Create a deterministic sequence from the text
    h = hashlib.sha512(text.encode()).digest()
    # Extend to fill EMBEDDING_DIM
    extended = h * (EMBEDDING_DIM // len(h) + 1)
    # Convert bytes to normalized floats in [-1, 1]
    vec = [(b / 127.5 - 1.0) for b in extended[:EMBEDDING_DIM]]
    # Normalize to unit length
    norm = sum(v * v for v in vec) ** 0.5
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


async def _real_embedding(text: str) -> list[float]:
    """Get a real embedding from OpenAI's API.

    Uses text-embedding-3-small which produces 1536-dim vectors.
    Falls back if OPENAI_API_KEY isn't set.
    """
    import os
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return _hash_embedding(text)

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "text-embedding-3-small",
                "input": text[:8000],  # Truncate to fit context
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["data"][0]["embedding"]


async def store_meeting_embedding(
    conn,
    meeting_id: UUID,
    chunk_text: str,
    chunk_type: str = "transcript",
    chunk_index: int = 0,
) -> None:
    """Generate and store an embedding for a meeting text chunk."""
    embedding = await generate_embedding(chunk_text)
    embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"

    await conn.execute(
        """
        INSERT INTO meeting_embeddings (meeting_id, chunk_text, chunk_type, chunk_index, embedding)
        VALUES (%s, %s, %s, %s, %s::vector)
        ON CONFLICT (meeting_id, chunk_type, chunk_index) DO UPDATE SET
            chunk_text = EXCLUDED.chunk_text,
            embedding = EXCLUDED.embedding
        """,
        [str(meeting_id), chunk_text, chunk_type, chunk_index, embedding_str],
    )


async def search_meeting_memory(
    conn,
    query: str,
    limit: int = 10,
    meeting_id: UUID | None = None,
) -> list[dict]:
    """Search meeting memory using semantic similarity.

    Returns the most relevant meeting chunks for the query.
    """
    query_embedding = await generate_embedding(query)
    embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"

    meeting_filter = ""
    params = [embedding_str, limit]
    if meeting_id:
        meeting_filter = "AND me.meeting_id = %s"
        params = [embedding_str, str(meeting_id), limit]

    cursor = await conn.execute(
        f"""
        SELECT
            me.meeting_id,
            me.chunk_text,
            me.chunk_type,
            me.chunk_index,
            m.title as meeting_title,
            m.scheduled_start,
            1 - (me.embedding <=> %s::vector) as similarity
        FROM meeting_embeddings me
        JOIN meetings m ON m.id = me.meeting_id
        WHERE 1=1 {meeting_filter}
        ORDER BY me.embedding <=> %s::vector
        LIMIT %s
        """,
        [*params[:-1], params[0], params[-1]],
    )
    rows = await cursor.fetchall()

    return [
        {
            "meeting_id": str(row["meeting_id"]),
            "meeting_title": row["meeting_title"],
            "chunk_text": row["chunk_text"],
            "chunk_type": row["chunk_type"],
            "similarity": round(row["similarity"], 4),
            "scheduled_start": str(row["scheduled_start"]) if row["scheduled_start"] else None,
        }
        for row in rows
    ]


async def index_meeting_for_search(conn, meeting_id: UUID, transcript: str) -> int:
    """Break a transcript into chunks and index them for semantic search.

    Returns the number of chunks indexed.
    """
    # Split transcript into ~500 char chunks with overlap
    chunks = _chunk_text(transcript, chunk_size=500, overlap=50)

    for i, chunk in enumerate(chunks):
        await store_meeting_embedding(
            conn, meeting_id, chunk, chunk_type="transcript", chunk_index=i
        )

    # Also index the summary if available
    cursor = await conn.execute(
        "SELECT summary_text FROM meeting_summaries WHERE meeting_id = %s",
        [str(meeting_id)],
    )
    summary_row = await cursor.fetchone()
    if summary_row:
        await store_meeting_embedding(
            conn, meeting_id, summary_row["summary_text"],
            chunk_type="summary", chunk_index=0
        )

    logger.info("Indexed {} transcript chunks for meeting {}", len(chunks), meeting_id)
    return len(chunks)


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks for embedding."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence-ending punctuation near the boundary
            for boundary in [". ", ".\n", "? ", "! "]:
                last_boundary = text.rfind(boundary, start + chunk_size // 2, end)
                if last_boundary > 0:
                    end = last_boundary + len(boundary)
                    break

        chunks.append(text[start:end].strip())
        start = end - overlap

    return [c for c in chunks if c]
