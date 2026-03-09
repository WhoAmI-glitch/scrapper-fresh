"""CRUD endpoints for shipments and the active shipments view."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from tracker.db import get_conn
from tracker.schemas.shipments import (
    ShipmentCreate,
    ShipmentUpdate,
    ShipmentResponse,
    ActiveShipmentResponse,
)
from tracker.services.shipment_state import (
    create_shipment,
    get_active_shipments,
    get_shipment_by_id,
    update_shipment,
    update_shipment_status,
)

router = APIRouter()


@router.get("/active", response_model=list[ActiveShipmentResponse])
async def list_active_shipments() -> list[ActiveShipmentResponse]:
    """Get all active (non-arrived, non-discharged) shipments.

    Returns a denormalised view including deal, vessel, and port data.
    """
    async with get_conn() as conn:
        rows = await get_active_shipments(conn)

    return [ActiveShipmentResponse(**row) for row in rows]


@router.get("/{shipment_id}", response_model=ShipmentResponse)
async def get_shipment(shipment_id: UUID) -> ShipmentResponse:
    """Get a single shipment by ID."""
    async with get_conn() as conn:
        row = await get_shipment_by_id(conn, shipment_id)

    if row is None:
        raise HTTPException(status_code=404, detail=f"Shipment {shipment_id} not found")

    return ShipmentResponse(
        id=row["id"],
        deal_id=row["deal_id"],
        vessel_id=row["vessel_id"],
        cargo_quantity_tons=float(row["cargo_quantity_tons"]),
        bill_of_lading=row["bill_of_lading"],
        load_date=row["load_date"],
        departure_date=row["departure_date"],
        eta=row["eta"],
        actual_arrival=row["actual_arrival"],
        status=row["status"],
        current_risk_level=row["current_risk_level"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.get("", response_model=list[ShipmentResponse])
async def list_shipments(
    deal_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
) -> list[ShipmentResponse]:
    """List shipments with optional filters."""
    async with get_conn() as conn:
        conditions: list[str] = []
        params: list[object] = []

        if deal_id is not None:
            conditions.append("deal_id = %s")
            params.append(str(deal_id))
        if status is not None:
            conditions.append("status = %s")
            params.append(status)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        query = f"""
            SELECT * FROM shipments {where_clause}
            ORDER BY created_at DESC
        """
        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()

    return [
        ShipmentResponse(
            id=r["id"],
            deal_id=r["deal_id"],
            vessel_id=r["vessel_id"],
            cargo_quantity_tons=float(r["cargo_quantity_tons"]),
            bill_of_lading=r["bill_of_lading"],
            load_date=r["load_date"],
            departure_date=r["departure_date"],
            eta=r["eta"],
            actual_arrival=r["actual_arrival"],
            status=r["status"],
            current_risk_level=r["current_risk_level"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
        )
        for r in rows
    ]


@router.post("", response_model=ShipmentResponse, status_code=201)
async def create_shipment_endpoint(body: ShipmentCreate) -> ShipmentResponse:
    """Create a new shipment linked to a deal."""
    async with get_conn() as conn:
        # Validate deal exists
        cursor = await conn.execute(
            "SELECT id FROM deals WHERE id = %s", [str(body.deal_id)]
        )
        if await cursor.fetchone() is None:
            raise HTTPException(
                status_code=400, detail=f"Deal {body.deal_id} not found"
            )

        # Validate vessel if provided
        if body.vessel_id is not None:
            cursor = await conn.execute(
                "SELECT id FROM vessels WHERE id = %s", [str(body.vessel_id)]
            )
            if await cursor.fetchone() is None:
                raise HTTPException(
                    status_code=400, detail=f"Vessel {body.vessel_id} not found"
                )

        row = await create_shipment(
            conn,
            deal_id=body.deal_id,
            vessel_id=body.vessel_id,
            cargo_quantity_tons=body.cargo_quantity_tons,
            bill_of_lading=body.bill_of_lading,
            load_date=str(body.load_date) if body.load_date else None,
            departure_date=body.departure_date.isoformat() if body.departure_date else None,
            eta=body.eta.isoformat() if body.eta else None,
            status=body.status,
        )

    return ShipmentResponse(
        id=row["id"],
        deal_id=row["deal_id"],
        vessel_id=row["vessel_id"],
        cargo_quantity_tons=float(row["cargo_quantity_tons"]),
        bill_of_lading=row["bill_of_lading"],
        load_date=row["load_date"],
        departure_date=row["departure_date"],
        eta=row["eta"],
        actual_arrival=row["actual_arrival"],
        status=row["status"],
        current_risk_level=row["current_risk_level"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.patch("/{shipment_id}", response_model=ShipmentResponse)
async def update_shipment_endpoint(
    shipment_id: UUID,
    body: ShipmentUpdate,
) -> ShipmentResponse:
    """Update an existing shipment. Only provided fields are changed."""
    fields = body.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Convert datetime objects to ISO strings where needed
    for key in ("departure_date", "eta", "actual_arrival"):
        if key in fields and fields[key] is not None:
            fields[key] = fields[key].isoformat() if hasattr(fields[key], "isoformat") else fields[key]
    if "load_date" in fields and fields["load_date"] is not None:
        fields["load_date"] = str(fields["load_date"])
    if "vessel_id" in fields and fields["vessel_id"] is not None:
        fields["vessel_id"] = str(fields["vessel_id"])

    async with get_conn() as conn:
        # If status is being changed, use the state machine function
        if "status" in fields:
            row = await update_shipment_status(conn, shipment_id, fields.pop("status"))
            if row is None:
                raise HTTPException(
                    status_code=404, detail=f"Shipment {shipment_id} not found"
                )
            # Apply remaining fields if any
            if fields:
                row = await update_shipment(conn, shipment_id, **fields)
        else:
            row = await update_shipment(conn, shipment_id, **fields)

    if row is None:
        raise HTTPException(status_code=404, detail=f"Shipment {shipment_id} not found")

    return ShipmentResponse(
        id=row["id"],
        deal_id=row["deal_id"],
        vessel_id=row["vessel_id"],
        cargo_quantity_tons=float(row["cargo_quantity_tons"]),
        bill_of_lading=row["bill_of_lading"],
        load_date=row["load_date"],
        departure_date=row["departure_date"],
        eta=row["eta"],
        actual_arrival=row["actual_arrival"],
        status=row["status"],
        current_risk_level=row["current_risk_level"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
