"""Excel report generation engine using XlsxWriter.

Generates structured trading workbooks with live formulas,
conditional formatting, and multiple sheets.
"""

from __future__ import annotations

import io
from datetime import datetime

import psycopg
from loguru import logger

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None  # type: ignore[assignment]
    logger.warning("xlsxwriter not installed. Excel reports will be unavailable.")


async def generate_trading_book_report(conn: psycopg.AsyncConnection) -> io.BytesIO:
    """Generate the Trading Book workbook with 5 sheets.

    Sheets: Summary, Deal Details, P&L, Commissions, Exposure
    Returns an in-memory BytesIO containing the .xlsx file.
    """
    if xlsxwriter is None:
        raise RuntimeError("xlsxwriter is required for Excel reports. pip install xlsxwriter")

    output = io.BytesIO()
    wb = xlsxwriter.Workbook(output, {"in_memory": True})

    # ── Formats ──
    header_fmt = wb.add_format({
        "bold": True, "bg_color": "#1e293b", "font_color": "#e2e8f0",
        "border": 1, "text_wrap": True, "valign": "vcenter",
    })
    money_fmt = wb.add_format({"num_format": "$#,##0.00", "border": 1})
    pct_fmt = wb.add_format({"num_format": "0.00%", "border": 1})
    num_fmt = wb.add_format({"num_format": "#,##0.00", "border": 1})
    text_fmt = wb.add_format({"border": 1, "text_wrap": True})
    date_fmt = wb.add_format({"num_format": "yyyy-mm-dd", "border": 1})
    title_fmt = wb.add_format({
        "bold": True, "font_size": 14, "font_color": "#1e293b",
    })
    kpi_label_fmt = wb.add_format({"bold": True, "font_size": 11})
    kpi_value_fmt = wb.add_format({"bold": True, "font_size": 12, "num_format": "$#,##0.00"})

    # Conditional format colors
    green_fill = wb.add_format({"bg_color": "#22c55e", "font_color": "#052e16", "border": 1})
    red_fill = wb.add_format({"bg_color": "#ef4444", "font_color": "#450a0a", "border": 1})
    yellow_fill = wb.add_format({"bg_color": "#eab308", "font_color": "#422006", "border": 1})
    blue_fill = wb.add_format({"bg_color": "#3b82f6", "font_color": "#1e3a5f", "border": 1})

    # ── Fetch Data ──
    cursor = await conn.execute("""
        SELECT
            d.contract_id, d.commodity, d.buyer, d.seller,
            d.quantity_tons, d.price_per_ton, d.contract_value,
            d.incoterms, d.status, d.payment_terms, d.risk_notes,
            lp.name AS load_port, dp.name AS discharge_port, dp.country AS discharge_country,
            s.eta, s.current_risk_level, s.status AS shipment_status,
            v.name AS vessel_name
        FROM deals d
        JOIN ports lp ON d.load_port_id = lp.id
        JOIN ports dp ON d.discharge_port_id = dp.id
        LEFT JOIN shipments s ON s.deal_id = d.id
        LEFT JOIN vessels v ON s.vessel_id = v.id
        WHERE d.status != 'cancelled'
        ORDER BY d.created_at DESC
    """)
    deals = await cursor.fetchall()

    # Fetch costs
    cursor = await conn.execute("""
        SELECT dc.deal_id, dc.cost_type, SUM(dc.amount) AS total,
               SUM(dc.amount) FILTER (WHERE dc.is_estimated) AS estimated,
               SUM(dc.amount) FILTER (WHERE NOT dc.is_estimated) AS actual
        FROM deal_costs dc
        JOIN deals d ON dc.deal_id = d.id
        WHERE d.status != 'cancelled'
        GROUP BY dc.deal_id, dc.cost_type
    """)
    cost_rows = await cursor.fetchall()
    costs_by_deal: dict[str, dict] = {}
    for row in cost_rows:
        did = str(row["deal_id"])
        if did not in costs_by_deal:
            costs_by_deal[did] = {"freight": 0, "insurance": 0, "port_charges": 0, "other": 0, "total": 0}
        amt = float(row["total"] or 0)
        ct = row["cost_type"]
        if ct in ("freight", "insurance", "port_charges"):
            costs_by_deal[did][ct] += amt
        else:
            costs_by_deal[did]["other"] += amt
        costs_by_deal[did]["total"] += amt

    # Fetch commissions
    cursor = await conn.execute("""
        SELECT dc.deal_id, dc.recipient, dc.commission_type, dc.rate, dc.paid,
               d.quantity_tons, d.contract_value
        FROM deal_commissions dc
        JOIN deals d ON dc.deal_id = d.id
        WHERE d.status != 'cancelled'
    """)
    comm_rows = await cursor.fetchall()

    # ══════════════════════════════════════════════════════════════════
    # SHEET 1: Summary
    # ══════════════════════════════════════════════════════════════════
    ws_summary = wb.add_worksheet("Summary")
    ws_summary.set_column("A:A", 25)
    ws_summary.set_column("B:B", 20)

    now = datetime.utcnow()
    ws_summary.write("A1", "Charcoal Trading Book", title_fmt)
    ws_summary.write("A2", f"Report Period: {now.strftime('%B %Y')}", kpi_label_fmt)
    ws_summary.write("A3", f"Generated: {now.strftime('%Y-%m-%d %H:%M UTC')}")

    ws_summary.write("A5", "Total Active Deals", kpi_label_fmt)
    ws_summary.write_formula("B5", f"=COUNTA('Deal Details'!A2:A{len(deals)+1})")
    ws_summary.write("A6", "Total Contract Value", kpi_label_fmt)
    ws_summary.write_formula("B6", f"=SUM('Deal Details'!G2:G{len(deals)+1})", kpi_value_fmt)
    ws_summary.write("A7", "Total Costs", kpi_label_fmt)
    ws_summary.write_formula("B7", f"=SUM('P&L'!G2:G{len(deals)+1})", kpi_value_fmt)
    ws_summary.write("A8", "Gross Margin", kpi_label_fmt)
    ws_summary.write_formula("B8", "=B6-B7", kpi_value_fmt)
    ws_summary.write("A9", "Margin %", kpi_label_fmt)
    ws_summary.write_formula("B9", "=IF(B6>0,B8/B6,0)", pct_fmt)
    ws_summary.write("A10", "Total Commission", kpi_label_fmt)
    ws_summary.write_formula("B10", f"=SUM(Commissions!E2:E{len(comm_rows)+1})", kpi_value_fmt)
    ws_summary.write("A11", "Net Margin", kpi_label_fmt)
    ws_summary.write_formula("B11", "=B8-B10", kpi_value_fmt)

    # ══════════════════════════════════════════════════════════════════
    # SHEET 2: Deal Details
    # ══════════════════════════════════════════════════════════════════
    ws_deals = wb.add_worksheet("Deal Details")
    deal_headers = [
        "Contract ID", "Commodity", "Buyer", "Seller", "Quantity (MT)",
        "Price ($/MT)", "Contract Value", "Incoterms", "Status",
        "Load Port", "Discharge Port", "ETA", "Days to ETA", "Risk Level",
    ]
    for col, h in enumerate(deal_headers):
        ws_deals.write(0, col, h, header_fmt)
        ws_deals.set_column(col, col, 16)

    for row_idx, deal in enumerate(deals, start=1):
        ws_deals.write(row_idx, 0, deal["contract_id"], text_fmt)
        ws_deals.write(row_idx, 1, deal["commodity"], text_fmt)
        ws_deals.write(row_idx, 2, deal["buyer"], text_fmt)
        ws_deals.write(row_idx, 3, deal["seller"], text_fmt)
        ws_deals.write(row_idx, 4, float(deal["quantity_tons"] or 0), num_fmt)
        ws_deals.write(row_idx, 5, float(deal["price_per_ton"] or 0), money_fmt)
        ws_deals.write_formula(row_idx, 6, f"=E{row_idx+1}*F{row_idx+1}", money_fmt)
        ws_deals.write(row_idx, 7, deal["incoterms"], text_fmt)
        ws_deals.write(row_idx, 8, deal["status"], text_fmt)
        ws_deals.write(row_idx, 9, deal["load_port"], text_fmt)
        ws_deals.write(row_idx, 10, deal["discharge_port"], text_fmt)

        eta = deal.get("eta")
        if eta:
            ws_deals.write_datetime(row_idx, 11, eta if isinstance(eta, datetime) else datetime.fromisoformat(str(eta)), date_fmt)
            ws_deals.write_formula(row_idx, 12, f'=IF(L{row_idx+1}="","",L{row_idx+1}-TODAY())', num_fmt)
        else:
            ws_deals.write(row_idx, 11, "", text_fmt)
            ws_deals.write(row_idx, 12, "", text_fmt)

        ws_deals.write(row_idx, 13, deal.get("current_risk_level", "low"), text_fmt)

    # ══════════════════════════════════════════════════════════════════
    # SHEET 3: P&L
    # ══════════════════════════════════════════════════════════════════
    ws_pnl = wb.add_worksheet("P&L")
    pnl_headers = [
        "Contract ID", "Revenue", "Freight", "Insurance", "Port Charges",
        "Other Costs", "Total Costs", "Gross Margin", "Margin %",
        "Commission", "Net Margin",
    ]
    for col, h in enumerate(pnl_headers):
        ws_pnl.write(0, col, h, header_fmt)
        ws_pnl.set_column(col, col, 16)

    for row_idx, deal in enumerate(deals, start=1):
        did = str(deal.get("id") if "id" in deal else "")
        costs = costs_by_deal.get(did, {"freight": 0, "insurance": 0, "port_charges": 0, "other": 0, "total": 0})

        ws_pnl.write(row_idx, 0, deal["contract_id"], text_fmt)
        ws_pnl.write_formula(row_idx, 1, f"='Deal Details'!G{row_idx+1}", money_fmt)
        ws_pnl.write(row_idx, 2, costs["freight"], money_fmt)
        ws_pnl.write(row_idx, 3, costs["insurance"], money_fmt)
        ws_pnl.write(row_idx, 4, costs["port_charges"], money_fmt)
        ws_pnl.write(row_idx, 5, costs["other"], money_fmt)
        ws_pnl.write_formula(row_idx, 6, f"=SUM(C{row_idx+1}:F{row_idx+1})", money_fmt)
        ws_pnl.write_formula(row_idx, 7, f"=B{row_idx+1}-G{row_idx+1}", money_fmt)
        ws_pnl.write_formula(row_idx, 8, f"=IF(B{row_idx+1}>0,H{row_idx+1}/B{row_idx+1},0)", pct_fmt)
        # Commission reference filled below
        ws_pnl.write(row_idx, 9, 0, money_fmt)
        ws_pnl.write_formula(row_idx, 10, f"=H{row_idx+1}-J{row_idx+1}", money_fmt)

    # ══════════════════════════════════════════════════════════════════
    # SHEET 4: Commissions
    # ══════════════════════════════════════════════════════════════════
    ws_comm = wb.add_worksheet("Commissions")
    comm_headers = ["Contract ID", "Broker/Recipient", "Type", "Rate", "Amount", "Paid", "Paid Date"]
    for col, h in enumerate(comm_headers):
        ws_comm.write(0, col, h, header_fmt)
        ws_comm.set_column(col, col, 18)

    for row_idx, comm in enumerate(comm_rows, start=1):
        # Find contract_id for this deal
        contract_id = ""
        for d in deals:
            if "id" in d and str(d.get("id")) == str(comm["deal_id"]):
                contract_id = d["contract_id"]
                break

        ws_comm.write(row_idx, 0, contract_id, text_fmt)
        ws_comm.write(row_idx, 1, comm["recipient"], text_fmt)
        ws_comm.write(row_idx, 2, comm["commission_type"], text_fmt)
        ws_comm.write(row_idx, 3, float(comm["rate"]), num_fmt)

        # Calculate amount
        rate = float(comm["rate"])
        qty = float(comm["quantity_tons"] or 0)
        cv = float(comm["contract_value"] or 0)
        match comm["commission_type"]:
            case "flat":
                amount = rate
            case "per_ton":
                amount = rate * qty
            case "percentage":
                amount = rate * cv
            case _:
                amount = 0
        ws_comm.write(row_idx, 4, amount, money_fmt)
        ws_comm.write(row_idx, 5, "Yes" if comm["paid"] else "No", text_fmt)
        ws_comm.write(row_idx, 6, "", text_fmt)

    # ══════════════════════════════════════════════════════════════════
    # SHEET 5: Exposure
    # ══════════════════════════════════════════════════════════════════
    ws_exp = wb.add_worksheet("Exposure")
    cursor = await conn.execute("""
        SELECT
            dp.country AS region,
            COUNT(*) AS active_deals,
            COALESCE(SUM(d.quantity_tons), 0) AS total_tons,
            COALESCE(SUM(d.contract_value), 0) AS total_value
        FROM deals d
        JOIN ports dp ON d.discharge_port_id = dp.id
        WHERE d.status NOT IN ('cancelled', 'completed')
        GROUP BY dp.country
        ORDER BY total_value DESC
    """)
    exposure_rows = await cursor.fetchall()

    exp_headers = ["Region", "Active Deals", "Total Tons", "Total Value", "% of Portfolio"]
    for col, h in enumerate(exp_headers):
        ws_exp.write(0, col, h, header_fmt)
        ws_exp.set_column(col, col, 18)

    for row_idx, exp in enumerate(exposure_rows, start=1):
        ws_exp.write(row_idx, 0, exp["region"], text_fmt)
        ws_exp.write(row_idx, 1, exp["active_deals"], num_fmt)
        ws_exp.write(row_idx, 2, float(exp["total_tons"]), num_fmt)
        ws_exp.write(row_idx, 3, float(exp["total_value"]), money_fmt)
        ws_exp.write_formula(
            row_idx, 4,
            f"=IF(SUM(D$2:D${len(exposure_rows)+1})>0,D{row_idx+1}/SUM(D$2:D${len(exposure_rows)+1}),0)",
            pct_fmt,
        )

    wb.close()
    output.seek(0)
    logger.info("Generated trading book report with {} deals", len(deals))
    return output


async def generate_shipment_progress_report(conn: psycopg.AsyncConnection) -> io.BytesIO:
    """Generate the Shipment Progress workbook.

    Single sheet with milestone tracking, progress bars, and delay analysis.
    """
    if xlsxwriter is None:
        raise RuntimeError("xlsxwriter is required for Excel reports. pip install xlsxwriter")

    output = io.BytesIO()
    wb = xlsxwriter.Workbook(output, {"in_memory": True})

    header_fmt = wb.add_format({
        "bold": True, "bg_color": "#1e293b", "font_color": "#e2e8f0",
        "border": 1, "text_wrap": True,
    })
    text_fmt = wb.add_format({"border": 1, "text_wrap": True})
    date_fmt = wb.add_format({"num_format": "yyyy-mm-dd", "border": 1})
    num_fmt = wb.add_format({"num_format": "#,##0", "border": 1})
    pct_fmt = wb.add_format({"num_format": "0%", "border": 1})

    ws = wb.add_worksheet("Shipment Progress")

    headers = [
        "Contract ID", "Vessel", "Route", "Load Date", "Departure",
        "ETA", "Actual Arrival", "Status", "Progress %", "Days in Transit",
        "Days Remaining", "On Time?",
    ]
    for col, h in enumerate(headers):
        ws.write(0, col, h, header_fmt)
        ws.set_column(col, col, 16)

    cursor = await conn.execute("""
        SELECT
            d.contract_id,
            v.name AS vessel_name,
            lp.name AS load_port, dp.name AS discharge_port,
            s.load_date, s.departure_date, s.eta, s.actual_arrival,
            s.status, s.current_risk_level
        FROM shipments s
        JOIN deals d ON s.deal_id = d.id
        LEFT JOIN vessels v ON s.vessel_id = v.id
        JOIN ports lp ON d.load_port_id = lp.id
        JOIN ports dp ON d.discharge_port_id = dp.id
        ORDER BY s.eta ASC NULLS LAST
    """)
    rows = await cursor.fetchall()

    status_progress = {
        "loading": 0.17, "departed": 0.33, "in_transit": 0.50,
        "arriving": 0.67, "arrived": 0.83, "discharged": 1.0,
    }

    for row_idx, row in enumerate(rows, start=1):
        ws.write(row_idx, 0, row["contract_id"], text_fmt)
        ws.write(row_idx, 1, row.get("vessel_name") or "TBN", text_fmt)
        ws.write(row_idx, 2, f"{row['load_port']} -> {row['discharge_port']}", text_fmt)

        for col, field in [(3, "load_date"), (4, "departure_date"), (5, "eta"), (6, "actual_arrival")]:
            val = row.get(field)
            if val:
                if isinstance(val, datetime):
                    ws.write_datetime(row_idx, col, val, date_fmt)
                else:
                    ws.write(row_idx, col, str(val), text_fmt)
            else:
                ws.write(row_idx, col, "", text_fmt)

        status = row["status"]
        ws.write(row_idx, 7, status, text_fmt)
        ws.write(row_idx, 8, status_progress.get(status, 0), pct_fmt)

        # Days in transit
        ws.write_formula(
            row_idx, 9,
            f'=IF(E{row_idx+1}="","",TODAY()-E{row_idx+1})',
            num_fmt,
        )
        # Days remaining
        ws.write_formula(
            row_idx, 10,
            f'=IF(F{row_idx+1}="","",F{row_idx+1}-TODAY())',
            num_fmt,
        )
        # On time?
        ws.write_formula(
            row_idx, 11,
            f'=IF(F{row_idx+1}="","N/A",IF(F{row_idx+1}>=TODAY(),"Yes","OVERDUE"))',
            text_fmt,
        )

    # Data bar for progress
    if rows:
        ws.conditional_format(1, 8, len(rows), 8, {
            "type": "data_bar",
            "bar_color": "#3b82f6",
        })

    wb.close()
    output.seek(0)
    logger.info("Generated shipment progress report with {} shipments", len(rows))
    return output
