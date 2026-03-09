"""Risk scoring service -- canonical owner of geographic risk assessment.

Uses PostGIS spatial queries to determine which risk zones a vessel
is currently inside, and assigns an appropriate risk level.
"""

from __future__ import annotations

from uuid import UUID

import psycopg
from loguru import logger


async def score_vessel_risk(
    conn: psycopg.AsyncConnection,
    vessel_id: UUID,
) -> str:
    """Evaluate the risk level for a vessel based on its current position.

    Checks the vessel's current_position against all active risk_zones
    using PostGIS ST_Intersects. Returns the highest risk level found,
    or 'low' if the vessel is not in any risk zone.

    Risk level precedence: critical > high > medium > low
    """
    query = """
        SELECT rz.risk_level
        FROM vessels v
        JOIN risk_zones rz
            ON ST_Intersects(v.current_position, rz.geometry)
        WHERE v.id = %s
          AND rz.active = TRUE
        ORDER BY
            CASE rz.risk_level
                WHEN 'critical' THEN 4
                WHEN 'high'     THEN 3
                WHEN 'medium'   THEN 2
                WHEN 'low'      THEN 1
            END DESC
        LIMIT 1
    """
    cursor = await conn.execute(query, [str(vessel_id)])
    row = await cursor.fetchone()
    risk = row["risk_level"] if row else "low"
    logger.debug("Vessel {} risk score: {}", vessel_id, risk)
    return risk


async def get_zones_for_position(
    conn: psycopg.AsyncConnection,
    lat: float,
    lon: float,
) -> list[dict]:
    """Find all active risk zones that contain the given point.

    Returns a list of dicts with zone details (id, name, zone_type,
    risk_level, description).
    """
    query = """
        SELECT
            id, name, zone_type, risk_level, description, source
        FROM risk_zones
        WHERE active = TRUE
          AND ST_Intersects(
              geometry,
              ST_GeogFromText('POINT(' || %s || ' ' || %s || ')')
          )
        ORDER BY
            CASE risk_level
                WHEN 'critical' THEN 4
                WHEN 'high'     THEN 3
                WHEN 'medium'   THEN 2
                WHEN 'low'      THEN 1
            END DESC
    """
    cursor = await conn.execute(query, [lon, lat])
    rows = await cursor.fetchall()
    return rows


async def get_zones_for_vessel(
    conn: psycopg.AsyncConnection,
    vessel_id: UUID,
) -> list[dict]:
    """Find all active risk zones containing the vessel's current position."""
    query = """
        SELECT
            rz.id, rz.name, rz.zone_type, rz.risk_level,
            rz.description, rz.source
        FROM vessels v
        JOIN risk_zones rz
            ON ST_Intersects(v.current_position, rz.geometry)
        WHERE v.id = %s
          AND rz.active = TRUE
        ORDER BY
            CASE rz.risk_level
                WHEN 'critical' THEN 4
                WHEN 'high'     THEN 3
                WHEN 'medium'   THEN 2
                WHEN 'low'      THEN 1
            END DESC
    """
    cursor = await conn.execute(query, [str(vessel_id)])
    rows = await cursor.fetchall()
    return rows


async def update_shipment_risk_levels(conn: psycopg.AsyncConnection) -> int:
    """Batch-update risk levels for all active shipments.

    For each active shipment with an assigned vessel, re-evaluates the
    vessel's position against risk zones and updates the shipment's
    current_risk_level accordingly.

    Returns the number of shipments whose risk level changed.
    """
    # Fetch active shipments that have a vessel assigned
    query = """
        SELECT s.id AS shipment_id, s.vessel_id, s.current_risk_level
        FROM shipments s
        WHERE s.status NOT IN ('arrived', 'discharged')
          AND s.vessel_id IS NOT NULL
    """
    cursor = await conn.execute(query)
    shipments = await cursor.fetchall()

    changed = 0
    for shipment in shipments:
        new_risk = await score_vessel_risk(conn, shipment["vessel_id"])
        if new_risk != shipment["current_risk_level"]:
            await conn.execute(
                """
                UPDATE shipments
                SET current_risk_level = %s, updated_at = NOW()
                WHERE id = %s
                """,
                [new_risk, str(shipment["shipment_id"])],
            )
            changed += 1
            logger.info(
                "Shipment {} risk level changed: {} -> {}",
                shipment["shipment_id"],
                shipment["current_risk_level"],
                new_risk,
            )

    if changed > 0:
        logger.info("Updated risk levels for {} shipments", changed)
    return changed
