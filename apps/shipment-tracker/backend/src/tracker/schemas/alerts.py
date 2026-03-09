"""Pydantic schemas for Alert endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


AlertTypeValue = Literal[
    "risk_zone_entry", "delay", "route_deviation", "email_received", "milestone"
]

AlertSeverityValue = Literal["info", "warning", "critical"]


class AlertResponse(BaseModel):
    """Full alert response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    shipment_id: UUID | None = None
    vessel_id: UUID | None = None
    deal_id: UUID | None = None
    alert_type: AlertTypeValue
    severity: AlertSeverityValue
    title: str
    message: str | None = None
    acknowledged: bool = False
    acknowledged_at: datetime | None = None
    created_at: datetime


class AlertAcknowledge(BaseModel):
    """Request body for acknowledging an alert."""

    acknowledged: bool = True


class AlertListResponse(BaseModel):
    """Paginated list of alerts."""

    items: list[AlertResponse]
    total: int
    page: int
    page_size: int


class AlertFilter(BaseModel):
    """Query parameters for filtering alerts."""

    severity: AlertSeverityValue | None = None
    alert_type: AlertTypeValue | None = None
    acknowledged: bool | None = None
    shipment_id: UUID | None = None
    vessel_id: UUID | None = None
    deal_id: UUID | None = None
