"""Endpoints for vessel tracking and position management."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from tracker.db import get_conn
from tracker.schemas.vessels import (
    VesselResponse,
    VesselPositionUpdate,
    VesselTrackResponse,
)
from tracker.services.vessel_tracker import (
    get_all_vessel_positions,
    get_vessel_by_id,
    get_vessel_track,
    update_vessel_position,
)

router = APIRouter()


@router.get("", response_model=list[VesselResponse])
async def list_vessels() -> list[VesselResponse]:
    """Get current positions for all tracked vessels."""
    async with get_conn() as conn:
        rows = await get_all_vessel_positions(conn)

    return [
        VesselResponse(
            id=r["id"],
            name=r["name"],
            imo_number=r["imo_number"],
            mmsi=r["mmsi"],
            vessel_type=r["vessel_type"],
            flag=r["flag"],
            dwt=r["dwt"],
            lat=r["lat"],
            lon=r["lon"],
            current_speed=r["current_speed"],
            current_heading=r["current_heading"],
            last_ais_update=r["last_ais_update"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
        )
        for r in rows
    ]


@router.get("/{vessel_id}", response_model=VesselResponse)
async def get_vessel(vessel_id: UUID) -> VesselResponse:
    """Get a single vessel by ID."""
    async with get_conn() as conn:
        row = await get_vessel_by_id(conn, vessel_id)

    if row is None:
        raise HTTPException(status_code=404, detail=f"Vessel {vessel_id} not found")

    return VesselResponse(
        id=row["id"],
        name=row["name"],
        imo_number=row["imo_number"],
        mmsi=row["mmsi"],
        vessel_type=row["vessel_type"],
        flag=row["flag"],
        dwt=row["dwt"],
        lat=row["lat"],
        lon=row["lon"],
        current_speed=row["current_speed"],
        current_heading=row["current_heading"],
        last_ais_update=row["last_ais_update"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.get("/{vessel_id}/track", response_model=VesselTrackResponse)
async def get_vessel_track_endpoint(
    vessel_id: UUID,
    hours: int = Query(default=24, ge=1, le=720, description="Hours of track history"),
) -> VesselTrackResponse:
    """Get historical voyage track for a vessel."""
    async with get_conn() as conn:
        vessel = await get_vessel_by_id(conn, vessel_id)
        if vessel is None:
            raise HTTPException(status_code=404, detail=f"Vessel {vessel_id} not found")

        points = await get_vessel_track(conn, vessel_id, hours=hours)

    return VesselTrackResponse(
        vessel_id=vessel_id,
        vessel_name=vessel["name"],
        points=[
            {
                "lat": p["lat"],
                "lon": p["lon"],
                "speed": p["speed"],
                "heading": p["heading"],
                "recorded_at": p["recorded_at"],
            }
            for p in points
        ],
        point_count=len(points),
    )


@router.patch("/{vessel_id}/position", response_model=VesselResponse)
async def update_vessel_position_endpoint(
    vessel_id: UUID,
    body: VesselPositionUpdate,
) -> VesselResponse:
    """Update a vessel's AIS position (manual or from integration)."""
    async with get_conn() as conn:
        row = await update_vessel_position(
            conn,
            vessel_id=vessel_id,
            lat=body.lat,
            lon=body.lon,
            speed=body.speed,
            heading=body.heading,
        )

    if not row:
        raise HTTPException(status_code=404, detail=f"Vessel {vessel_id} not found")

    logger.info(
        "Position updated for vessel {}: ({}, {})",
        row["name"],
        body.lat,
        body.lon,
    )

    return VesselResponse(
        id=row["id"],
        name=row["name"],
        imo_number=row["imo_number"],
        mmsi=row["mmsi"],
        vessel_type=row["vessel_type"],
        flag=row["flag"],
        dwt=row["dwt"],
        lat=row["lat"],
        lon=row["lon"],
        current_speed=row["current_speed"],
        current_heading=row["current_heading"],
        last_ais_update=row["last_ais_update"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
