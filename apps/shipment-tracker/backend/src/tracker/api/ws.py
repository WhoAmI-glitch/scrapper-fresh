"""WebSocket endpoint for real-time vessel position updates and alerts.

Maintains a set of connected clients and provides a broadcast function
that workers call to push data to all clients simultaneously.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

ws_router = APIRouter()

# Global set of connected WebSocket clients
_connected_clients: set[WebSocket] = set()
_clients_lock = asyncio.Lock()


async def _add_client(ws: WebSocket) -> None:
    """Register a new WebSocket client."""
    async with _clients_lock:
        _connected_clients.add(ws)
    logger.info("WebSocket client connected (total: {})", len(_connected_clients))


async def _remove_client(ws: WebSocket) -> None:
    """Unregister a disconnected WebSocket client."""
    async with _clients_lock:
        _connected_clients.discard(ws)
    logger.info("WebSocket client disconnected (total: {})", len(_connected_clients))


def _serialize(data: Any) -> str:
    """JSON-serialise data with datetime handling."""

    def _default(obj: Any) -> str:
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    return json.dumps(data, default=_default)


async def broadcast(event_type: str, payload: dict[str, Any]) -> int:
    """Broadcast a message to all connected WebSocket clients.

    Returns the number of clients that received the message.
    The message format is: {"type": event_type, "data": payload}
    """
    if not _connected_clients:
        return 0

    message = _serialize({"type": event_type, "data": payload})

    # Copy the set to avoid modification during iteration
    async with _clients_lock:
        clients = set(_connected_clients)

    sent = 0
    dead_clients: list[WebSocket] = []

    for client in clients:
        try:
            await client.send_text(message)
            sent += 1
        except Exception:
            dead_clients.append(client)

    # Clean up dead connections
    if dead_clients:
        async with _clients_lock:
            for dc in dead_clients:
                _connected_clients.discard(dc)
        logger.debug("Removed {} dead WebSocket connections", len(dead_clients))

    return sent


async def broadcast_vessel_position(
    vessel_id: str,
    vessel_name: str,
    lat: float,
    lon: float,
    speed: float,
    heading: float,
) -> int:
    """Convenience: broadcast a vessel position update."""
    return await broadcast(
        "vessel_position",
        {
            "vessel_id": vessel_id,
            "vessel_name": vessel_name,
            "lat": lat,
            "lon": lon,
            "speed": speed,
            "heading": heading,
        },
    )


async def broadcast_alert(alert: dict[str, Any]) -> int:
    """Convenience: broadcast a new alert to all clients."""
    return await broadcast("alert", alert)


@ws_router.websocket("/ws/live")
async def websocket_live(ws: WebSocket) -> None:
    """WebSocket endpoint for real-time data streaming.

    Clients connect here to receive:
    - vessel_position: periodic AIS position updates
    - alert: new alert notifications

    The connection stays open until the client disconnects.
    Clients can send ping messages; the server responds with pong.
    """
    await ws.accept()
    await _add_client(ws)

    try:
        # Send initial welcome message
        await ws.send_text(
            _serialize(
                {
                    "type": "connected",
                    "data": {"message": "Connected to shipment tracker live feed"},
                }
            )
        )

        # Keep connection alive and handle incoming messages
        while True:
            try:
                data = await ws.receive_text()
                # Handle ping/pong for keep-alive
                try:
                    msg = json.loads(data)
                    if msg.get("type") == "ping":
                        await ws.send_text(
                            _serialize({"type": "pong", "data": {}})
                        )
                except json.JSONDecodeError:
                    pass
            except WebSocketDisconnect:
                break
    except Exception as exc:
        logger.debug("WebSocket error: {}", exc)
    finally:
        await _remove_client(ws)
