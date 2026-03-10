"""Report generation and export endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from loguru import logger

from tracker.db import get_conn
from tracker.services.report_generator import (
    generate_trading_book_report,
    generate_shipment_progress_report,
)
from tracker.services.deal_manager import calculate_deal_pnl, get_all_deal_pnl

router = APIRouter()


@router.post("/export/trading-book")
async def export_trading_book():
    """Generate and download the Trading Book Excel workbook."""
    async with get_conn() as conn:
        try:
            output = await generate_trading_book_report(conn)
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail=str(e))

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=trading_book.xlsx"},
    )


@router.post("/export/shipment-progress")
async def export_shipment_progress():
    """Generate and download the Shipment Progress Excel workbook."""
    async with get_conn() as conn:
        try:
            output = await generate_shipment_progress_report(conn)
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail=str(e))

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=shipment_progress.xlsx"},
    )


@router.get("/pnl")
async def get_deal_pnl_report():
    """Get P&L data for all active deals as JSON."""
    async with get_conn() as conn:
        results = await get_all_deal_pnl(conn)
    return {"items": results, "total": len(results)}


@router.get("/pnl/{deal_id}")
async def get_single_deal_pnl(deal_id: UUID):
    """Get P&L for a single deal."""
    async with get_conn() as conn:
        result = await calculate_deal_pnl(conn, deal_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Deal {deal_id} not found")
    return result
