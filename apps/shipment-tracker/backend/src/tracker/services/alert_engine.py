"""Alert engine service -- canonical owner of alert generation and queries.

Provides functions to detect conditions that warrant alerts (risk zone
entry, delays, route deviations) and to create/query/acknowledge alerts.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

import psycopg
from loguru import logger


async def create_alert(
    conn: psycopg.AsyncConnection,
    *,
    alert_type: str,
    severity: str,
    title: str,
    message: str | None = None,
    shipment_id: UUID | None = None,
    vessel_id: UUID | None = None,
    deal_id: UUID | None = None,
) -> dict:
    """Insert a new alert record.

    Returns the newly created alert row. This is the only function
    that should create alerts -- all other modules delegate here.
    """
    query = """
        INSERT INTO alerts (
            alert_type, severity, title, message,
            shipment_id, vessel_id, deal_id
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING *
    """
    cursor = await conn.execute(
        query,
        [
            alert_type,
            severity,
            title,
            message,
            str(shipment_id) if shipment_id else None,
            str(vessel_id) if vessel_id else None,
            str(deal_id) if deal_id else None,
        ],
    )
    row = await cursor.fetchone()
    logger.info("Alert created: [{}] {} - {}", severity.upper(), alert_type, title)
    return row


async def get_alerts(
    conn: psycopg.AsyncConnection,
    *,
    page: int = 1,
    page_size: int = 20,
    severity: str | None = None,
    alert_type: str | None = None,
    acknowledged: bool | None = None,
    shipment_id: UUID | None = None,
    vessel_id: UUID | None = None,
    deal_id: UUID | None = None,
) -> tuple[list[dict], int]:
    """Fetch alerts with pagination and filtering.

    Returns a tuple of (items, total_count).
    """
    conditions: list[str] = []
    params: list[object] = []

    if severity is not None:
        conditions.append("severity = %s")
        params.append(severity)
    if alert_type is not None:
        conditions.append("alert_type = %s")
        params.append(alert_type)
    if acknowledged is not None:
        conditions.append("acknowledged = %s")
        params.append(acknowledged)
    if shipment_id is not None:
        conditions.append("shipment_id = %s")
        params.append(str(shipment_id))
    if vessel_id is not None:
        conditions.append("vessel_id = %s")
        params.append(str(vessel_id))
    if deal_id is not None:
        conditions.append("deal_id = %s")
        params.append(str(deal_id))

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    # Total count
    count_query = f"SELECT COUNT(*) AS total FROM alerts {where_clause}"
    cursor = await conn.execute(count_query, params)
    count_row = await cursor.fetchone()
    total = count_row["total"] if count_row else 0

    # Paginated results
    offset = (page - 1) * page_size
    data_query = f"""
        SELECT * FROM alerts
        {where_clause}
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
    """
    cursor = await conn.execute(data_query, params + [page_size, offset])
    items = await cursor.fetchall()

    return items, total


async def acknowledge_alert(
    conn: psycopg.AsyncConnection,
    alert_id: UUID,
) -> dict | None:
    """Mark an alert as acknowledged.

    Sets acknowledged=TRUE and records the acknowledgement timestamp.
    Returns the updated alert row, or None if not found.
    """
    query = """
        UPDATE alerts
        SET acknowledged = TRUE, acknowledged_at = NOW()
        WHERE id = %s
        RETURNING *
    """
    cursor = await conn.execute(query, [str(alert_id)])
    row = await cursor.fetchone()
    if row:
        logger.info("Alert {} acknowledged", alert_id)
    return row


async def check_risk_zone_alerts(conn: psycopg.AsyncConnection) -> list[dict]:
    """Detect vessels that are currently inside risk zones without an existing alert.

    Generates 'risk_zone_entry' alerts for vessel/zone combinations that
    do not already have an unacknowledged alert from the last 24 hours.
    """
    query = """
        SELECT
            v.id AS vessel_id, v.name AS vessel_name,
            v.imo_number,
            rz.id AS zone_id, rz.name AS zone_name,
            rz.risk_level, rz.zone_type,
            s.id AS shipment_id, s.deal_id
        FROM vessels v
        JOIN shipments s ON s.vessel_id = v.id
        JOIN risk_zones rz ON ST_Intersects(v.current_position, rz.geometry)
        WHERE s.status NOT IN ('arrived', 'discharged')
          AND rz.active = TRUE
          AND v.current_position IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM alerts a
              WHERE a.vessel_id = v.id
                AND a.alert_type = 'risk_zone_entry'
                AND a.title LIKE '%%' || rz.name || '%%'
                AND a.created_at > NOW() - INTERVAL '24 hours'
                AND a.acknowledged = FALSE
          )
    """
    cursor = await conn.execute(query)
    rows = await cursor.fetchall()

    created_alerts: list[dict] = []
    for row in rows:
        severity = "critical" if row["risk_level"] in ("critical", "high") else "warning"
        alert = await create_alert(
            conn,
            alert_type="risk_zone_entry",
            severity=severity,
            title=f"{row['vessel_name']} entered {row['zone_name']}",
            message=(
                f"Vessel {row['vessel_name']} (IMO {row['imo_number']}) "
                f"has entered {row['zone_name']} ({row['zone_type']} zone, "
                f"risk level: {row['risk_level']}). "
                f"Review security protocols and contact vessel master."
            ),
            shipment_id=row["shipment_id"],
            vessel_id=row["vessel_id"],
            deal_id=row["deal_id"],
        )
        created_alerts.append(alert)

    return created_alerts


async def check_delay_alerts(conn: psycopg.AsyncConnection) -> list[dict]:
    """Detect shipments where the ETA has passed without arrival.

    Generates 'delay' alerts for shipments that are overdue and do not
    already have a recent delay alert.
    """
    query = """
        SELECT
            s.id AS shipment_id, s.vessel_id, s.deal_id,
            s.eta,
            d.contract_id,
            v.name AS vessel_name
        FROM shipments s
        JOIN deals d ON s.deal_id = d.id
        LEFT JOIN vessels v ON s.vessel_id = v.id
        WHERE s.status NOT IN ('arrived', 'discharged')
          AND s.eta IS NOT NULL
          AND s.eta < NOW()
          AND s.actual_arrival IS NULL
          AND NOT EXISTS (
              SELECT 1 FROM alerts a
              WHERE a.shipment_id = s.id
                AND a.alert_type = 'delay'
                AND a.created_at > NOW() - INTERVAL '24 hours'
                AND a.acknowledged = FALSE
          )
    """
    cursor = await conn.execute(query)
    rows = await cursor.fetchall()

    created_alerts: list[dict] = []
    for row in rows:
        vessel_info = f" on {row['vessel_name']}" if row["vessel_name"] else ""
        alert = await create_alert(
            conn,
            alert_type="delay",
            severity="warning",
            title=f"Shipment {row['contract_id']} overdue",
            message=(
                f"Shipment for deal {row['contract_id']}{vessel_info} "
                f"has not arrived. ETA was {row['eta'].isoformat()}. "
                f"Investigate cause of delay and update ETA."
            ),
            shipment_id=row["shipment_id"],
            vessel_id=row["vessel_id"],
            deal_id=row["deal_id"],
        )
        created_alerts.append(alert)

    return created_alerts


async def check_route_deviation_alerts(
    conn: psycopg.AsyncConnection,
    threshold_nm: float = 50.0,
) -> list[dict]:
    """Detect vessels significantly deviating from the direct route.

    Computes the great-circle distance from the vessel's current position
    to the straight line between load port and discharge port. If this
    exceeds threshold_nm nautical miles, generates a 'route_deviation' alert.

    Nautical mile conversion: 1 NM = 1852 meters.
    """
    threshold_meters = threshold_nm * 1852.0

    query = """
        SELECT
            v.id AS vessel_id, v.name AS vessel_name,
            v.imo_number,
            s.id AS shipment_id, s.deal_id,
            d.contract_id,
            ST_Distance(
                v.current_position,
                ST_MakeLine(lp.location::geometry, dp.location::geometry)::geography
            ) AS deviation_meters
        FROM vessels v
        JOIN shipments s ON s.vessel_id = v.id
        JOIN deals d ON s.deal_id = d.id
        JOIN ports lp ON d.load_port_id = lp.id
        JOIN ports dp ON d.discharge_port_id = dp.id
        WHERE s.status IN ('departed', 'in_transit')
          AND v.current_position IS NOT NULL
          AND ST_Distance(
              v.current_position,
              ST_MakeLine(lp.location::geometry, dp.location::geometry)::geography
          ) > %s
          AND NOT EXISTS (
              SELECT 1 FROM alerts a
              WHERE a.vessel_id = v.id
                AND a.alert_type = 'route_deviation'
                AND a.created_at > NOW() - INTERVAL '24 hours'
                AND a.acknowledged = FALSE
          )
    """
    cursor = await conn.execute(query, [threshold_meters])
    rows = await cursor.fetchall()

    created_alerts: list[dict] = []
    for row in rows:
        deviation_nm = row["deviation_meters"] / 1852.0
        alert = await create_alert(
            conn,
            alert_type="route_deviation",
            severity="warning",
            title=f"{row['vessel_name']} deviating from planned route",
            message=(
                f"Vessel {row['vessel_name']} (IMO {row['imo_number']}) "
                f"for deal {row['contract_id']} is {deviation_nm:.1f} NM "
                f"off the direct route. Threshold is {threshold_nm} NM. "
                f"Verify with vessel master if deviation is intentional."
            ),
            shipment_id=row["shipment_id"],
            vessel_id=row["vessel_id"],
            deal_id=row["deal_id"],
        )
        created_alerts.append(alert)

    return created_alerts


async def cleanup_old_alerts(
    conn: psycopg.AsyncConnection,
    days: int = 30,
) -> int:
    """Delete acknowledged alerts older than the specified number of days.

    Returns the number of deleted rows.
    """
    query = """
        DELETE FROM alerts
        WHERE acknowledged = TRUE
          AND acknowledged_at < NOW() - make_interval(days => %s)
    """
    cursor = await conn.execute(query, [days])
    deleted = cursor.rowcount
    if deleted > 0:
        logger.info("Cleaned up {} old acknowledged alerts", deleted)
    return deleted
