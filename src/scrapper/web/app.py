"""FastAPI web application — dashboard, API, and export endpoints."""

from __future__ import annotations

import secrets
from datetime import datetime
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from loguru import logger

from scrapper.config import get_settings
from scrapper.db.connection import get_connection
from scrapper.logging_ import setup_logging

setup_logging()

app = FastAPI(title="Scrapper", version="0.1.0")
security = HTTPBasic()


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)) -> str:  # noqa: B008
    """Verify HTTP Basic Auth credentials."""
    settings = get_settings()
    correct_user = secrets.compare_digest(credentials.username, settings.app_username)
    correct_pass = secrets.compare_digest(credentials.password, settings.app_password)
    if not (correct_user and correct_pass):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return credentials.username


# ── Health (no auth) ─────────────────────────────────────────────


@app.get("/health")
def health() -> dict[str, str]:
    """Health check — no auth required."""
    try:
        with get_connection() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "degraded", "database": str(e)}


# ── Stats ────────────────────────────────────────────────────────


@app.get("/stats")
def stats(user: str = Depends(verify_credentials)) -> dict[str, Any]:
    """Pipeline statistics."""
    with get_connection() as conn:
        # Queue stats
        rows = conn.execute(
            "SELECT state, COUNT(*) as cnt FROM enrichment_tasks GROUP BY state"
        ).fetchall()
        queue: dict[str, Any] = {r["state"]: r["cnt"] for r in rows}  # type: ignore[call-overload]

        # Counts
        leads_row = conn.execute("SELECT COUNT(*) as cnt FROM leads").fetchone()
        cand_row = conn.execute("SELECT COUNT(*) as cnt FROM candidates").fetchone()

        # Contact fill rates
        fill_row = conn.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(inn) as has_inn,
                COUNT(phone) as has_phone,
                COUNT(email) as has_email,
                COUNT(website) as has_website,
                COUNT(ceo) as has_ceo,
                COUNT(revenue) as has_revenue
            FROM leads
        """).fetchone()

        # Leads by source (via candidates join)
        source_rows = conn.execute("""
            SELECT c.source, COUNT(l.id) as cnt
            FROM leads l
            JOIN enrichment_tasks et ON l.task_id = et.id
            JOIN candidates c ON et.candidate_id = c.id
            GROUP BY c.source
        """).fetchall()

    return {
        "candidates": cand_row["cnt"] if cand_row else 0,  # type: ignore[call-overload]
        "leads": leads_row["cnt"] if leads_row else 0,  # type: ignore[call-overload]
        "queue": queue,
        "fill_rates": dict(fill_row) if fill_row else {},
        "leads_by_source": {r["source"]: r["cnt"] for r in source_rows},  # type: ignore[call-overload]
    }


# ── Leads API ────────────────────────────────────────────────────


@app.get("/api/leads")
def api_leads(
    user: str = Depends(verify_credentials),
    limit: int = Query(500, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    search: str = Query(""),
    source: str = Query(""),
) -> list[dict[str, Any]]:
    """Return leads as JSON array for the dashboard."""
    with get_connection() as conn:
        query = """
            SELECT l.*, c.source as discovery_source
            FROM leads l
            LEFT JOIN enrichment_tasks et ON l.task_id = et.id
            LEFT JOIN candidates c ON et.candidate_id = c.id
        """
        conditions: list[str] = []
        params: list[Any] = []

        if search:
            conditions.append(
                "(l.company_name ILIKE %s OR l.inn LIKE %s OR l.address ILIKE %s)"
            )
            like = f"%{search}%"
            params.extend([like, f"%{search}%", like])

        if source:
            conditions.append("c.source = %s")
            params.append(source)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY l.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()

    # Serialize datetimes
    result = []
    for row in rows:
        d = dict(row)
        for k, v in d.items():
            if isinstance(v, datetime):
                d[k] = v.isoformat()
        result.append(d)
    return result


# ── Discovery trigger ────────────────────────────────────────────


@app.post("/runs/discover")
def trigger_discover(
    user: str = Depends(verify_credentials),
    source: str = Query("yandex_maps"),
    region: str = Query("moscow"),
) -> dict[str, Any]:
    """Trigger a discovery run."""
    from scrapper.db.queue import create_enrichment_task, save_candidate
    from scrapper.discovery.sources import SOURCES

    if source not in SOURCES:
        raise HTTPException(400, f"Unknown source: {source}")

    source_cls = SOURCES[source]
    kwargs: dict[str, Any] = {}
    if region and source in ("yandex_maps", "twogis", "zakupki"):
        kwargs["regions"] = [r.strip() for r in region.split(",") if r.strip()]

    try:
        src = source_cls(**kwargs)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    count = 0
    tasks_created = 0
    with get_connection() as conn:
        for hint in src.discover():
            cand_id = save_candidate(conn, hint)
            if cand_id is not None:
                count += 1
                create_enrichment_task(conn, cand_id)
                tasks_created += 1
        conn.commit()

    logger.info(f"Discovery via API: source={source}, region={region}, found={count}")
    return {"source": source, "region": region, "new_candidates": count, "tasks_created": tasks_created}


# ── Export ───────────────────────────────────────────────────────


@app.get("/export")
def export_leads(
    user: str = Depends(verify_credentials),
    fmt: str = Query("xlsx", alias="format"),
    limit: int = Query(default=0, ge=0),
) -> FileResponse:
    """Export leads as file download."""
    from scrapper.export.exporter import export_csv, export_json, export_xlsx

    lim = limit if limit > 0 else None
    if fmt == "csv":
        path = export_csv(limit=lim)
    elif fmt == "json":
        path = export_json(limit=lim)
    else:
        path = export_xlsx(limit=lim)

    media_types = {
        "csv": "text/csv",
        "json": "application/json",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    return FileResponse(
        path=str(path),
        filename=path.name,
        media_type=media_types.get(fmt, "application/octet-stream"),
    )


# ── Monitoring ───────────────────────────────────────────────────


@app.get("/monitoring")
def monitoring(user: str = Depends(verify_credentials)) -> dict[str, Any]:
    """Monitoring endpoint — check system health."""
    from scrapper.monitoring import get_monitoring_status
    return get_monitoring_status()


# ── Dashboard ────────────────────────────────────────────────────


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, user: str = Depends(verify_credentials)) -> HTMLResponse:
    """Serve the leads dashboard."""
    from scrapper.web.dashboard import DASHBOARD_HTML
    return HTMLResponse(content=DASHBOARD_HTML)


@app.get("/", response_class=HTMLResponse)
def root(request: Request) -> HTMLResponse:
    """Redirect to dashboard (or show health for unauthenticated)."""
    return HTMLResponse(
        content='<html><body><p>Scrapper API</p>'
        '<p><a href="/dashboard">Dashboard</a> | '
        '<a href="/health">Health</a></p></body></html>'
    )
