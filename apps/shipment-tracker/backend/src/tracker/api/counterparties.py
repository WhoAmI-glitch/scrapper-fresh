"""CRUD endpoints for counterparties (trading partners)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from tracker.db import get_conn
from tracker.schemas.counterparties import (
    CounterpartyCreate,
    CounterpartyUpdate,
    CounterpartyResponse,
    CounterpartyListResponse,
)

router = APIRouter()


@router.get("", response_model=CounterpartyListResponse)
async def list_counterparties(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    type: str | None = Query(default=None),
) -> CounterpartyListResponse:
    """List counterparties with pagination and optional type filter."""
    async with get_conn() as conn:
        conditions: list[str] = []
        params: list[object] = []

        if type is not None:
            conditions.append("c.type = %s")
            params.append(type)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        count_query = f"SELECT COUNT(*) AS total FROM counterparties c {where_clause}"
        cursor = await conn.execute(count_query, params)
        count_row = await cursor.fetchone()
        total = count_row["total"] if count_row else 0

        offset = (page - 1) * page_size
        data_query = f"""
            SELECT
                c.*,
                COALESCE(dc.cnt, 0) AS deal_count
            FROM counterparties c
            LEFT JOIN (
                SELECT unnest(ARRAY[buyer_id, seller_id, broker_id]) AS cp_id,
                       COUNT(*) AS cnt
                FROM deals
                GROUP BY cp_id
            ) dc ON dc.cp_id = c.id
            {where_clause}
            ORDER BY c.name ASC
            LIMIT %s OFFSET %s
        """
        cursor = await conn.execute(data_query, params + [page_size, offset])
        rows = await cursor.fetchall()

    items = [
        CounterpartyResponse(
            id=row["id"],
            name=row["name"],
            short_name=row["short_name"],
            type=row["type"],
            country=row["country"],
            tax_id=row["tax_id"],
            primary_contact_name=row["primary_contact_name"],
            primary_contact_email=row["primary_contact_email"],
            primary_contact_phone=row["primary_contact_phone"],
            notes=row["notes"],
            deal_count=row["deal_count"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        for row in rows
    ]

    return CounterpartyListResponse(
        items=items, total=total, page=page, page_size=page_size
    )


@router.get("/{cp_id}", response_model=CounterpartyResponse)
async def get_counterparty(cp_id: UUID) -> CounterpartyResponse:
    """Get a single counterparty by ID."""
    async with get_conn() as conn:
        query = """
            SELECT c.*,
                   (SELECT COUNT(*) FROM deals
                    WHERE buyer_id = c.id OR seller_id = c.id OR broker_id = c.id
                   ) AS deal_count
            FROM counterparties c
            WHERE c.id = %s
        """
        cursor = await conn.execute(query, [str(cp_id)])
        row = await cursor.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Counterparty {cp_id} not found")

    return CounterpartyResponse(
        id=row["id"],
        name=row["name"],
        short_name=row["short_name"],
        type=row["type"],
        country=row["country"],
        tax_id=row["tax_id"],
        primary_contact_name=row["primary_contact_name"],
        primary_contact_email=row["primary_contact_email"],
        primary_contact_phone=row["primary_contact_phone"],
        notes=row["notes"],
        deal_count=row["deal_count"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.post("", response_model=CounterpartyResponse, status_code=201)
async def create_counterparty(body: CounterpartyCreate) -> CounterpartyResponse:
    """Create a new counterparty."""
    async with get_conn() as conn:
        query = """
            INSERT INTO counterparties (
                name, short_name, type, country, tax_id,
                primary_contact_name, primary_contact_email, primary_contact_phone, notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        cursor = await conn.execute(
            query,
            [
                body.name,
                body.short_name,
                body.type,
                body.country,
                body.tax_id,
                body.primary_contact_name,
                body.primary_contact_email,
                body.primary_contact_phone,
                body.notes,
            ],
        )
        row = await cursor.fetchone()

        # Log audit
        await conn.execute(
            """INSERT INTO audit_log (entity_type, entity_id, action, actor, source)
               VALUES ('counterparty', %s, 'create', 'system', 'api')""",
            [str(row["id"])],
        )

    logger.info("Created counterparty {} ({})", row["id"], row["name"])
    return CounterpartyResponse(
        id=row["id"],
        name=row["name"],
        short_name=row["short_name"],
        type=row["type"],
        country=row["country"],
        tax_id=row["tax_id"],
        primary_contact_name=row["primary_contact_name"],
        primary_contact_email=row["primary_contact_email"],
        primary_contact_phone=row["primary_contact_phone"],
        notes=row["notes"],
        deal_count=0,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.put("/{cp_id}", response_model=CounterpartyResponse)
async def update_counterparty(cp_id: UUID, body: CounterpartyUpdate) -> CounterpartyResponse:
    """Update an existing counterparty."""
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    set_parts = [f"{k} = %s" for k in updates]
    set_clause = ", ".join(set_parts)
    values = list(updates.values()) + [str(cp_id)]

    async with get_conn() as conn:
        # Fetch old values for audit
        cursor = await conn.execute(
            "SELECT * FROM counterparties WHERE id = %s", [str(cp_id)]
        )
        old_row = await cursor.fetchone()
        if old_row is None:
            raise HTTPException(status_code=404, detail=f"Counterparty {cp_id} not found")

        query = f"""
            UPDATE counterparties
            SET {set_clause}, updated_at = NOW()
            WHERE id = %s
            RETURNING *
        """
        cursor = await conn.execute(query, values)
        row = await cursor.fetchone()

        # Audit log for each changed field
        for field, new_val in updates.items():
            old_val = old_row.get(field)
            if str(old_val) != str(new_val):
                await conn.execute(
                    """INSERT INTO audit_log
                       (entity_type, entity_id, action, field_name, old_value, new_value, actor, source)
                       VALUES ('counterparty', %s, 'update', %s, %s, %s, 'system', 'api')""",
                    [str(cp_id), field, str(old_val) if old_val else None, str(new_val)],
                )

    logger.info("Updated counterparty {} fields: {}", cp_id, list(updates.keys()))

    # Re-fetch with deal count
    return await get_counterparty(cp_id)


@router.delete("/{cp_id}", status_code=204)
async def delete_counterparty(cp_id: UUID) -> None:
    """Delete a counterparty. Fails if linked to deals."""
    async with get_conn() as conn:
        cursor = await conn.execute(
            "SELECT COUNT(*) AS cnt FROM deals WHERE buyer_id=%s OR seller_id=%s OR broker_id=%s",
            [str(cp_id), str(cp_id), str(cp_id)],
        )
        row = await cursor.fetchone()
        if row and row["cnt"] > 0:
            raise HTTPException(
                status_code=409,
                detail="Cannot delete counterparty linked to deals.",
            )

        cursor = await conn.execute(
            "DELETE FROM counterparties WHERE id = %s RETURNING id", [str(cp_id)]
        )
        deleted = await cursor.fetchone()
        if deleted is None:
            raise HTTPException(status_code=404, detail=f"Counterparty {cp_id} not found")

        await conn.execute(
            """INSERT INTO audit_log (entity_type, entity_id, action, actor, source)
               VALUES ('counterparty', %s, 'delete', 'system', 'api')""",
            [str(cp_id)],
        )

    logger.info("Deleted counterparty {}", cp_id)
