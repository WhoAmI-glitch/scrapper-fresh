"""Deal management service -- P&L, margins, and commission calculations.

Owns deal-level financial calculations. All monetary values in USD.
"""

from __future__ import annotations

from uuid import UUID

import psycopg
from loguru import logger


async def calculate_deal_pnl(conn: psycopg.AsyncConnection, deal_id: UUID) -> dict:
    """Calculate full P&L for a single deal.

    Returns a dict with: revenue, actual_costs, estimated_costs, total_costs,
    gross_margin, margin_pct, total_commission, net_margin, cost_breakdown.
    """
    # Fetch the deal
    cursor = await conn.execute(
        "SELECT id, contract_id, contract_value, quantity_tons FROM deals WHERE id = %s",
        [str(deal_id)],
    )
    deal = await cursor.fetchone()
    if deal is None:
        return {}

    revenue = float(deal["contract_value"] or 0)
    quantity = float(deal["quantity_tons"] or 0)

    # Fetch costs grouped by type
    cursor = await conn.execute(
        """
        SELECT cost_type,
               SUM(amount) AS total,
               SUM(amount) FILTER (WHERE is_estimated) AS estimated,
               SUM(amount) FILTER (WHERE NOT is_estimated) AS actual
        FROM deal_costs
        WHERE deal_id = %s
        GROUP BY cost_type
        ORDER BY cost_type
        """,
        [str(deal_id)],
    )
    cost_rows = await cursor.fetchall()

    cost_breakdown = []
    total_costs = 0.0
    actual_costs = 0.0
    estimated_costs = 0.0

    for row in cost_rows:
        amt = float(row["total"] or 0)
        act = float(row["actual"] or 0)
        est = float(row["estimated"] or 0)
        total_costs += amt
        actual_costs += act
        estimated_costs += est
        cost_breakdown.append({
            "cost_type": row["cost_type"],
            "total": amt,
            "actual": act,
            "estimated": est,
        })

    gross_margin = revenue - total_costs
    margin_pct = (gross_margin / revenue * 100) if revenue > 0 else 0.0

    # Commissions
    total_commission = await calculate_commission(conn, deal_id)

    net_margin = gross_margin - total_commission

    return {
        "deal_id": str(deal_id),
        "contract_id": deal["contract_id"],
        "revenue": revenue,
        "quantity_tons": quantity,
        "actual_costs": actual_costs,
        "estimated_costs": estimated_costs,
        "total_costs": total_costs,
        "gross_margin": gross_margin,
        "margin_pct": round(margin_pct, 2),
        "total_commission": total_commission,
        "net_margin": net_margin,
        "cost_breakdown": cost_breakdown,
    }


async def calculate_commission(conn: psycopg.AsyncConnection, deal_id: UUID) -> float:
    """Calculate total commission for a deal.

    Supports three commission types:
    - flat: rate is the absolute USD amount
    - per_ton: rate * quantity_tons
    - percentage: rate * contract_value (rate is decimal, e.g. 0.025 = 2.5%)
    """
    cursor = await conn.execute(
        "SELECT contract_value, quantity_tons FROM deals WHERE id = %s",
        [str(deal_id)],
    )
    deal = await cursor.fetchone()
    if deal is None:
        return 0.0

    contract_value = float(deal["contract_value"] or 0)
    quantity_tons = float(deal["quantity_tons"] or 0)

    cursor = await conn.execute(
        "SELECT commission_type, rate FROM deal_commissions WHERE deal_id = %s",
        [str(deal_id)],
    )
    rows = await cursor.fetchall()

    total = 0.0
    for row in rows:
        rate = float(row["rate"])
        match row["commission_type"]:
            case "flat":
                total += rate
            case "per_ton":
                total += rate * quantity_tons
            case "percentage":
                total += rate * contract_value
            case _:
                logger.warning(
                    "Unknown commission type '{}' for deal {}",
                    row["commission_type"],
                    deal_id,
                )
    return round(total, 2)


async def get_all_deal_pnl(conn: psycopg.AsyncConnection) -> list[dict]:
    """Calculate P&L for all active deals."""
    cursor = await conn.execute(
        "SELECT id FROM deals WHERE status NOT IN ('cancelled') ORDER BY created_at DESC"
    )
    rows = await cursor.fetchall()
    results = []
    for row in rows:
        pnl = await calculate_deal_pnl(conn, row["id"])
        if pnl:
            results.append(pnl)
    return results


async def add_deal_cost(
    conn: psycopg.AsyncConnection,
    deal_id: UUID,
    *,
    cost_type: str,
    description: str,
    amount: float,
    currency: str = "USD",
    is_estimated: bool = True,
    invoice_ref: str | None = None,
) -> dict:
    """Add a cost line item to a deal."""
    cursor = await conn.execute(
        """
        INSERT INTO deal_costs (deal_id, cost_type, description, amount, currency, is_estimated, invoice_ref)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING *
        """,
        [str(deal_id), cost_type, description, amount, currency, is_estimated, invoice_ref],
    )
    row = await cursor.fetchone()
    logger.info("Added {} cost ${} to deal {}", cost_type, amount, deal_id)
    return row


async def add_deal_commission(
    conn: psycopg.AsyncConnection,
    deal_id: UUID,
    *,
    recipient: str,
    commission_type: str,
    rate: float,
) -> dict:
    """Add a commission entry to a deal."""
    cursor = await conn.execute(
        """
        INSERT INTO deal_commissions (deal_id, recipient, commission_type, rate)
        VALUES (%s, %s, %s, %s)
        RETURNING *
        """,
        [str(deal_id), recipient, commission_type, rate],
    )
    row = await cursor.fetchone()
    logger.info("Added {} commission for {} on deal {}", commission_type, recipient, deal_id)
    return row
