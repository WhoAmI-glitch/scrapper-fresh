"""Alert endpoints for querying, filtering, and acknowledging alerts."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from tracker.db import get_conn
from tracker.schemas.alerts import (
    AlertResponse,
    AlertAcknowledge,
    AlertListResponse,
)
from tracker.services.alert_engine import (
    get_alerts,
    acknowledge_alert,
)

router = APIRouter()


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    severity: str | None = Query(default=None, description="Filter by severity"),
    alert_type: str | None = Query(default=None, description="Filter by alert type"),
    acknowledged: bool | None = Query(default=None, description="Filter by ack status"),
    shipment_id: UUID | None = Query(default=None),
    vessel_id: UUID | None = Query(default=None),
    deal_id: UUID | None = Query(default=None),
) -> AlertListResponse:
    """List alerts with pagination and optional filters.

    By default, returns alerts ordered by creation time (newest first).
    """
    async with get_conn() as conn:
        items, total = await get_alerts(
            conn,
            page=page,
            page_size=page_size,
            severity=severity,
            alert_type=alert_type,
            acknowledged=acknowledged,
            shipment_id=shipment_id,
            vessel_id=vessel_id,
            deal_id=deal_id,
        )

    return AlertListResponse(
        items=[AlertResponse(**item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/unacknowledged", response_model=list[AlertResponse])
async def list_unacknowledged_alerts(
    limit: int = Query(default=50, ge=1, le=200),
) -> list[AlertResponse]:
    """Get the most recent unacknowledged alerts.

    Convenience endpoint for notification badges and alert panels.
    """
    async with get_conn() as conn:
        items, _ = await get_alerts(
            conn,
            page=1,
            page_size=limit,
            acknowledged=False,
        )

    return [AlertResponse(**item) for item in items]


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: UUID) -> AlertResponse:
    """Get a single alert by ID."""
    async with get_conn() as conn:
        cursor = await conn.execute(
            "SELECT * FROM alerts WHERE id = %s", [str(alert_id)]
        )
        row = await cursor.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

    return AlertResponse(**row)


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert_endpoint(
    alert_id: UUID,
    body: AlertAcknowledge | None = None,
) -> AlertResponse:
    """Acknowledge an alert, marking it as reviewed.

    Once acknowledged, the alert will no longer appear in the
    unacknowledged alerts list or trigger notification badges.
    """
    async with get_conn() as conn:
        row = await acknowledge_alert(conn, alert_id)

    if row is None:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

    return AlertResponse(**row)
