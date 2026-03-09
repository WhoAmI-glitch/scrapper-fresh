"""Dashboard endpoints for aggregated metrics and exposure analysis."""

from __future__ import annotations

from fastapi import APIRouter

from tracker.db import get_conn
from tracker.schemas.shipments import DashboardMetrics, ExposureByRegion
from tracker.services.shipment_state import calculate_exposure, get_exposure_by_region

router = APIRouter()


@router.get("/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics() -> DashboardMetrics:
    """Get high-level dashboard metrics from the dashboard_metrics view.

    Returns counts and aggregates for active shipments, total tonnage
    at sea, total contract value at sea, vessels in risk zones, and
    count of active vessels.
    """
    async with get_conn() as conn:
        row = await calculate_exposure(conn)

    return DashboardMetrics(
        active_shipments=row["active_shipments"],
        total_tons_at_sea=float(row["total_tons_at_sea"]),
        total_value_at_sea=float(row["total_value_at_sea"]),
        vessels_in_risk_zones=row["vessels_in_risk_zones"],
        active_vessels=row["active_vessels"],
    )


@router.get("/exposure-by-region", response_model=list[ExposureByRegion])
async def get_exposure_by_region_endpoint() -> list[ExposureByRegion]:
    """Get cargo exposure aggregated by discharge port country.

    Useful for understanding geographic concentration of risk
    and contract value distribution.
    """
    async with get_conn() as conn:
        rows = await get_exposure_by_region(conn)

    return [
        ExposureByRegion(
            region=r["region"],
            total_tons=float(r["total_tons"]),
            total_value=float(r["total_value"]),
            shipment_count=r["shipment_count"],
        )
        for r in rows
    ]
