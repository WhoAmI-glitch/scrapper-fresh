"""Pydantic schemas for Vessel endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class VesselResponse(BaseModel):
    """Full vessel response including current position."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    imo_number: str
    mmsi: str
    vessel_type: str
    flag: str | None = None
    dwt: int | None = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)
    current_speed: float = 0.0
    current_heading: float = 0.0
    last_ais_update: datetime | None = None
    created_at: datetime
    updated_at: datetime


class VesselPositionUpdate(BaseModel):
    """Request body for updating a vessel's AIS position."""

    lat: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    lon: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    speed: float = Field(default=0.0, ge=0, description="Speed over ground in knots")
    heading: float = Field(
        default=0.0, ge=0, lt=360, description="Heading in degrees (0-359)"
    )


class VesselTrackPoint(BaseModel):
    """A single point in a vessel's voyage track."""

    model_config = ConfigDict(from_attributes=True)

    lat: float
    lon: float
    speed: float | None = None
    heading: float | None = None
    recorded_at: datetime


class VesselTrackResponse(BaseModel):
    """Response for vessel track history."""

    vessel_id: UUID
    vessel_name: str
    points: list[VesselTrackPoint]
    point_count: int
