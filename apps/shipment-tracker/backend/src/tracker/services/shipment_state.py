"""Shipment state service -- canonical owner of shipment queries and transitions.

All shipment-related database queries live here. API handlers and workers
delegate to these functions rather than writing their own SQL.
"""

from __future__ import annotations

from uuid import UUID

import psycopg
from loguru import logger


async def get_active_shipments(conn: psycopg.AsyncConnection) -> list[dict]:
    """Fetch all active shipments from the active_shipments view.

    Returns a list of dicts matching the ActiveShipmentResponse schema.
    """
    query = "SELECT * FROM active_shipments ORDER BY eta ASC NULLS LAST"
    cursor = await conn.execute(query)
    rows = await cursor.fetchall()
    return rows


async def get_shipment_by_id(conn: psycopg.AsyncConnection, shipment_id: UUID) -> dict | None:
    """Fetch a single shipment by ID with joined deal data."""
    query = """
        SELECT
            s.*,
            d.contract_id,
            d.buyer,
            d.seller,
            d.commodity
        FROM shipments s
        JOIN deals d ON s.deal_id = d.id
        WHERE s.id = %s
    """
    cursor = await conn.execute(query, [str(shipment_id)])
    return await cursor.fetchone()


async def create_shipment(
    conn: psycopg.AsyncConnection,
    *,
    deal_id: UUID,
    vessel_id: UUID | None,
    cargo_quantity_tons: float,
    bill_of_lading: str | None,
    load_date: str | None,
    departure_date: str | None,
    eta: str | None,
    status: str = "loading",
) -> dict:
    """Insert a new shipment record and return it."""
    query = """
        INSERT INTO shipments (
            deal_id, vessel_id, cargo_quantity_tons, bill_of_lading,
            load_date, departure_date, eta, status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *
    """
    cursor = await conn.execute(
        query,
        [
            str(deal_id),
            str(vessel_id) if vessel_id else None,
            cargo_quantity_tons,
            bill_of_lading,
            load_date,
            departure_date,
            eta,
            status,
        ],
    )
    row = await cursor.fetchone()
    logger.info("Created shipment {} for deal {}", row["id"], deal_id)
    return row


async def update_shipment(
    conn: psycopg.AsyncConnection,
    shipment_id: UUID,
    **fields: object,
) -> dict | None:
    """Update specified fields on a shipment. Returns the updated row.

    Only non-None values in fields are applied.
    """
    allowed = {
        "vessel_id", "cargo_quantity_tons", "bill_of_lading",
        "load_date", "departure_date", "eta", "actual_arrival", "status",
    }
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not updates:
        return await get_shipment_by_id(conn, shipment_id)

    set_clause = ", ".join(f"{k} = %s" for k in updates)
    values = list(updates.values()) + [str(shipment_id)]

    query = f"""
        UPDATE shipments
        SET {set_clause}, updated_at = NOW()
        WHERE id = %s
        RETURNING *
    """
    cursor = await conn.execute(query, values)
    row = await cursor.fetchone()
    if row:
        logger.info("Updated shipment {} fields: {}", shipment_id, list(updates.keys()))
    return row


async def update_shipment_status(
    conn: psycopg.AsyncConnection,
    shipment_id: UUID,
    status: str,
) -> dict | None:
    """Update shipment status and generate a milestone alert.

    This is the canonical way to transition shipment state -- it ensures
    an alert is always created for status changes.
    """
    from tracker.services.alert_engine import create_alert

    row = await update_shipment(conn, shipment_id, status=status)
    if row is None:
        return None

    # Generate a milestone alert for the status change
    await create_alert(
        conn,
        alert_type="milestone",
        severity="info",
        title=f"Shipment status changed to {status}",
        message=f"Shipment {shipment_id} transitioned to status: {status}",
        shipment_id=shipment_id,
        vessel_id=row.get("vessel_id"),
        deal_id=row.get("deal_id"),
    )
    return row


async def calculate_exposure(conn: psycopg.AsyncConnection) -> dict:
    """Fetch dashboard metrics from the dashboard_metrics view."""
    cursor = await conn.execute("SELECT * FROM dashboard_metrics")
    row = await cursor.fetchone()
    if row is None:
        return {
            "active_shipments": 0,
            "total_tons_at_sea": 0.0,
            "total_value_at_sea": 0.0,
            "vessels_in_risk_zones": 0,
            "active_vessels": 0,
        }
    return row


async def get_exposure_by_region(conn: psycopg.AsyncConnection) -> list[dict]:
    """Aggregate cargo exposure by discharge port country/region."""
    query = """
        SELECT
            dp.country AS region,
            COALESCE(SUM(s.cargo_quantity_tons), 0) AS total_tons,
            COALESCE(SUM(d.contract_value), 0) AS total_value,
            COUNT(*) AS shipment_count
        FROM shipments s
        JOIN deals d ON s.deal_id = d.id
        JOIN ports dp ON d.discharge_port_id = dp.id
        WHERE s.status NOT IN ('arrived', 'discharged')
        GROUP BY dp.country
        ORDER BY total_value DESC
    """
    cursor = await conn.execute(query)
    rows = await cursor.fetchall()
    return rows
