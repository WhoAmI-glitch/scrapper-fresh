"""CRUD endpoints for deals (commercial contracts)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from tracker.db import get_conn
from tracker.schemas.deals import (
    DealCreate,
    DealUpdate,
    DealResponse,
    DealListResponse,
)

router = APIRouter()


@router.get("", response_model=DealListResponse)
async def list_deals(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(default=None),
) -> DealListResponse:
    """List deals with pagination and optional status filter."""
    async with get_conn() as conn:
        conditions: list[str] = []
        params: list[object] = []

        if status is not None:
            conditions.append("d.status = %s")
            params.append(status)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # Total count
        count_query = f"SELECT COUNT(*) AS total FROM deals d {where_clause}"
        cursor = await conn.execute(count_query, params)
        count_row = await cursor.fetchone()
        total = count_row["total"] if count_row else 0

        # Fetch with port info
        offset = (page - 1) * page_size
        data_query = f"""
            SELECT
                d.*,
                lp.id AS lp_id, lp.name AS lp_name,
                lp.country AS lp_country, lp.unlocode AS lp_unlocode,
                dp.id AS dp_id, dp.name AS dp_name,
                dp.country AS dp_country, dp.unlocode AS dp_unlocode
            FROM deals d
            JOIN ports lp ON d.load_port_id = lp.id
            JOIN ports dp ON d.discharge_port_id = dp.id
            {where_clause}
            ORDER BY d.created_at DESC
            LIMIT %s OFFSET %s
        """
        cursor = await conn.execute(data_query, params + [page_size, offset])
        rows = await cursor.fetchall()

    items = []
    for row in rows:
        deal = DealResponse(
            id=row["id"],
            contract_id=row["contract_id"],
            commodity=row["commodity"],
            buyer=row["buyer"],
            seller=row["seller"],
            quantity_tons=float(row["quantity_tons"]),
            price_per_ton=float(row["price_per_ton"]),
            contract_value=float(row["contract_value"]) if row["contract_value"] else None,
            incoterms=row["incoterms"],
            load_port_id=row["load_port_id"],
            discharge_port_id=row["discharge_port_id"],
            load_port={
                "id": row["lp_id"],
                "name": row["lp_name"],
                "country": row["lp_country"],
                "unlocode": row["lp_unlocode"],
            },
            discharge_port={
                "id": row["dp_id"],
                "name": row["dp_name"],
                "country": row["dp_country"],
                "unlocode": row["dp_unlocode"],
            },
            status=row["status"],
            notes=row["notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        items.append(deal)

    return DealListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{deal_id}", response_model=DealResponse)
async def get_deal(deal_id: UUID) -> DealResponse:
    """Get a single deal by ID."""
    async with get_conn() as conn:
        query = """
            SELECT
                d.*,
                lp.id AS lp_id, lp.name AS lp_name,
                lp.country AS lp_country, lp.unlocode AS lp_unlocode,
                dp.id AS dp_id, dp.name AS dp_name,
                dp.country AS dp_country, dp.unlocode AS dp_unlocode
            FROM deals d
            JOIN ports lp ON d.load_port_id = lp.id
            JOIN ports dp ON d.discharge_port_id = dp.id
            WHERE d.id = %s
        """
        cursor = await conn.execute(query, [str(deal_id)])
        row = await cursor.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Deal {deal_id} not found")

    return DealResponse(
        id=row["id"],
        contract_id=row["contract_id"],
        commodity=row["commodity"],
        buyer=row["buyer"],
        seller=row["seller"],
        quantity_tons=float(row["quantity_tons"]),
        price_per_ton=float(row["price_per_ton"]),
        contract_value=float(row["contract_value"]) if row["contract_value"] else None,
        incoterms=row["incoterms"],
        load_port_id=row["load_port_id"],
        discharge_port_id=row["discharge_port_id"],
        load_port={
            "id": row["lp_id"],
            "name": row["lp_name"],
            "country": row["lp_country"],
            "unlocode": row["lp_unlocode"],
        },
        discharge_port={
            "id": row["dp_id"],
            "name": row["dp_name"],
            "country": row["dp_country"],
            "unlocode": row["dp_unlocode"],
        },
        status=row["status"],
        notes=row["notes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.post("", response_model=DealResponse, status_code=201)
async def create_deal(body: DealCreate) -> DealResponse:
    """Create a new deal."""
    async with get_conn() as conn:
        # Validate ports exist
        for port_id, label in [
            (body.load_port_id, "load port"),
            (body.discharge_port_id, "discharge port"),
        ]:
            cursor = await conn.execute("SELECT id FROM ports WHERE id = %s", [str(port_id)])
            if await cursor.fetchone() is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid {label} ID: {port_id}",
                )

        query = """
            INSERT INTO deals (
                contract_id, commodity, buyer, seller,
                quantity_tons, price_per_ton, incoterms,
                load_port_id, discharge_port_id, status, notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        try:
            cursor = await conn.execute(
                query,
                [
                    body.contract_id,
                    body.commodity,
                    body.buyer,
                    body.seller,
                    body.quantity_tons,
                    body.price_per_ton,
                    body.incoterms,
                    str(body.load_port_id),
                    str(body.discharge_port_id),
                    body.status,
                    body.notes,
                ],
            )
        except Exception as exc:
            error_msg = str(exc)
            if "unique" in error_msg.lower() or "duplicate" in error_msg.lower():
                raise HTTPException(
                    status_code=409,
                    detail=f"Deal with contract_id '{body.contract_id}' already exists",
                )
            logger.exception("Failed to create deal")
            raise HTTPException(status_code=500, detail="Failed to create deal")

        row = await cursor.fetchone()

    logger.info("Created deal {} ({})", row["id"], row["contract_id"])
    return DealResponse(
        id=row["id"],
        contract_id=row["contract_id"],
        commodity=row["commodity"],
        buyer=row["buyer"],
        seller=row["seller"],
        quantity_tons=float(row["quantity_tons"]),
        price_per_ton=float(row["price_per_ton"]),
        contract_value=float(row["contract_value"]) if row["contract_value"] else None,
        incoterms=row["incoterms"],
        load_port_id=row["load_port_id"],
        discharge_port_id=row["discharge_port_id"],
        status=row["status"],
        notes=row["notes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.patch("/{deal_id}", response_model=DealResponse)
async def update_deal(deal_id: UUID, body: DealUpdate) -> DealResponse:
    """Update an existing deal. Only provided fields are changed."""
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Convert UUIDs to strings for SQL
    for key in ("load_port_id", "discharge_port_id"):
        if key in updates and updates[key] is not None:
            updates[key] = str(updates[key])

    set_parts = [f"{k} = %s" for k in updates]
    set_clause = ", ".join(set_parts)
    values = list(updates.values()) + [str(deal_id)]

    async with get_conn() as conn:
        query = f"""
            UPDATE deals
            SET {set_clause}, updated_at = NOW()
            WHERE id = %s
            RETURNING *
        """
        cursor = await conn.execute(query, values)
        row = await cursor.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Deal {deal_id} not found")

    logger.info("Updated deal {} fields: {}", deal_id, list(updates.keys()))
    return DealResponse(
        id=row["id"],
        contract_id=row["contract_id"],
        commodity=row["commodity"],
        buyer=row["buyer"],
        seller=row["seller"],
        quantity_tons=float(row["quantity_tons"]),
        price_per_ton=float(row["price_per_ton"]),
        contract_value=float(row["contract_value"]) if row["contract_value"] else None,
        incoterms=row["incoterms"],
        load_port_id=row["load_port_id"],
        discharge_port_id=row["discharge_port_id"],
        status=row["status"],
        notes=row["notes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.delete("/{deal_id}", status_code=204)
async def delete_deal(deal_id: UUID) -> None:
    """Delete a deal. Fails if the deal has associated shipments."""
    async with get_conn() as conn:
        # Check for associated shipments
        cursor = await conn.execute(
            "SELECT COUNT(*) AS cnt FROM shipments WHERE deal_id = %s",
            [str(deal_id)],
        )
        row = await cursor.fetchone()
        if row and row["cnt"] > 0:
            raise HTTPException(
                status_code=409,
                detail="Cannot delete deal with associated shipments. Cancel the deal instead.",
            )

        cursor = await conn.execute(
            "DELETE FROM deals WHERE id = %s RETURNING id",
            [str(deal_id)],
        )
        deleted = await cursor.fetchone()
        if deleted is None:
            raise HTTPException(status_code=404, detail=f"Deal {deal_id} not found")

    logger.info("Deleted deal {}", deal_id)
