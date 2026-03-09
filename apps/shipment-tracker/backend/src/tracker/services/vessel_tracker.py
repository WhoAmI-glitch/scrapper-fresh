"""Vessel tracking service -- canonical owner of vessel position data.

Handles AIS position updates, voyage track storage, and position queries.
"""

from __future__ import annotations

from uuid import UUID

import psycopg
from loguru import logger


async def update_vessel_position(
    conn: psycopg.AsyncConnection,
    vessel_id: UUID,
    lat: float,
    lon: float,
    speed: float = 0.0,
    heading: float = 0.0,
) -> dict:
    """Update a vessel's current position and record a voyage track point.

    This is a two-step atomic operation:
    1. Update the vessels table with the latest position
    2. Insert a new row into voyage_tracks for historical tracking

    Returns the updated vessel row.
    """
    # Update the vessel's current position
    update_query = """
        UPDATE vessels
        SET
            current_position = ST_GeogFromText('POINT(' || %s || ' ' || %s || ')'),
            current_speed = %s,
            current_heading = %s,
            last_ais_update = NOW(),
            updated_at = NOW()
        WHERE id = %s
        RETURNING
            id, name, imo_number, mmsi, vessel_type, flag, dwt,
            ST_Y(current_position::geometry) AS lat,
            ST_X(current_position::geometry) AS lon,
            current_speed, current_heading, last_ais_update,
            created_at, updated_at
    """
    cursor = await conn.execute(
        update_query, [lon, lat, speed, heading, str(vessel_id)]
    )
    vessel = await cursor.fetchone()

    if vessel is None:
        logger.warning("Vessel {} not found for position update", vessel_id)
        return {}

    # Insert voyage track point
    track_query = """
        INSERT INTO voyage_tracks (vessel_id, position, speed, heading, recorded_at)
        VALUES (%s, ST_GeogFromText('POINT(' || %s || ' ' || %s || ')'), %s, %s, NOW())
    """
    await conn.execute(track_query, [str(vessel_id), lon, lat, speed, heading])

    logger.debug(
        "Updated vessel {} position: ({}, {}), speed={} kn, heading={}",
        vessel["name"],
        lat,
        lon,
        speed,
        heading,
    )
    return vessel


async def get_vessel_track(
    conn: psycopg.AsyncConnection,
    vessel_id: UUID,
    hours: int = 24,
) -> list[dict]:
    """Retrieve historical voyage track points for a vessel.

    Returns the last N hours of positions ordered chronologically
    (oldest first) for polyline rendering on maps.
    """
    query = """
        SELECT
            ST_Y(position::geometry) AS lat,
            ST_X(position::geometry) AS lon,
            speed,
            heading,
            recorded_at
        FROM voyage_tracks
        WHERE vessel_id = %s
          AND recorded_at >= NOW() - make_interval(hours => %s)
        ORDER BY recorded_at ASC
    """
    cursor = await conn.execute(query, [str(vessel_id), hours])
    rows = await cursor.fetchall()
    return rows


async def get_all_vessel_positions(conn: psycopg.AsyncConnection) -> list[dict]:
    """Get current positions for all tracked vessels.

    Returns vessels that have a current_position set, typically those
    assigned to active shipments.
    """
    query = """
        SELECT
            v.id,
            v.name,
            v.imo_number,
            v.mmsi,
            v.vessel_type,
            v.flag,
            v.dwt,
            ST_Y(v.current_position::geometry) AS lat,
            ST_X(v.current_position::geometry) AS lon,
            v.current_speed,
            v.current_heading,
            v.last_ais_update,
            v.created_at,
            v.updated_at
        FROM vessels v
        WHERE v.current_position IS NOT NULL
        ORDER BY v.name
    """
    cursor = await conn.execute(query)
    rows = await cursor.fetchall()
    return rows


async def get_vessel_by_id(
    conn: psycopg.AsyncConnection,
    vessel_id: UUID,
) -> dict | None:
    """Fetch a single vessel by its primary key."""
    query = """
        SELECT
            id, name, imo_number, mmsi, vessel_type, flag, dwt,
            ST_Y(current_position::geometry) AS lat,
            ST_X(current_position::geometry) AS lon,
            current_speed, current_heading, last_ais_update,
            created_at, updated_at
        FROM vessels
        WHERE id = %s
    """
    cursor = await conn.execute(query, [str(vessel_id)])
    return await cursor.fetchone()


async def get_vessel_by_imo(
    conn: psycopg.AsyncConnection,
    imo_number: str,
) -> dict | None:
    """Fetch a single vessel by IMO number."""
    query = """
        SELECT
            id, name, imo_number, mmsi, vessel_type, flag, dwt,
            ST_Y(current_position::geometry) AS lat,
            ST_X(current_position::geometry) AS lon,
            current_speed, current_heading, last_ais_update,
            created_at, updated_at
        FROM vessels
        WHERE imo_number = %s
    """
    cursor = await conn.execute(query, [imo_number])
    return await cursor.fetchone()


async def get_active_vessel_ids(conn: psycopg.AsyncConnection) -> list[dict]:
    """Get vessel IDs and IMO numbers for vessels assigned to active shipments.

    Used by the AIS poller to know which vessels to track.
    """
    query = """
        SELECT DISTINCT v.id, v.imo_number, v.mmsi, v.name
        FROM vessels v
        JOIN shipments s ON s.vessel_id = v.id
        WHERE s.status NOT IN ('arrived', 'discharged')
          AND v.id IS NOT NULL
    """
    cursor = await conn.execute(query)
    rows = await cursor.fetchall()
    return rows
