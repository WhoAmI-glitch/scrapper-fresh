"""FastAPI application entry point for the Shipment Tracker platform.

Configures middleware, lifespan events, routers, and the health-check
endpoint. Run with: uvicorn tracker.main:app --reload
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from tracker.config import get_settings
from tracker.db import init_pool, close_pool, get_conn, run_migrations
from tracker.api.router import api_router
from tracker.api.ws import ws_router
from tracker.workers.ais_poller import start_ais_poller, stop_ais_poller
from tracker.workers.email_poller import start_email_poller, stop_email_poller
from tracker.workers.alert_checker import start_alert_checker, stop_alert_checker
from tracker.workers.calendar_sync import start_calendar_sync, stop_calendar_sync
from tracker.workers.report_scheduler import start_report_scheduler, stop_report_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown lifecycle.

    - Opens the database connection pool
    - Starts background worker tasks
    - Cleans up all resources on shutdown
    """
    settings = get_settings()
    logger.info("Starting {} v0.1.0", settings.app_name)

    # Database
    await init_pool()

    # Run pending migrations
    async with get_conn() as conn:
        await run_migrations(conn)

    # Background workers
    worker_tasks: list[asyncio.Task] = []
    worker_tasks.append(await start_ais_poller())
    worker_tasks.append(await start_email_poller())
    worker_tasks.append(await start_alert_checker())
    worker_tasks.append(await start_calendar_sync())
    worker_tasks.append(await start_report_scheduler())

    logger.info("All background workers started")

    yield

    # Shutdown
    logger.info("Shutting down...")
    await stop_ais_poller()
    await stop_email_poller()
    await stop_alert_checker()
    await stop_calendar_sync()
    await stop_report_scheduler()

    # Cancel any remaining worker tasks
    for task in worker_tasks:
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    await close_pool()
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    """Factory function that builds the configured FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="Charcoal shipment intelligence and tracking platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes
    app.include_router(api_router, prefix="/api")

    # WebSocket routes (no /api prefix)
    app.include_router(ws_router)

    @app.get("/health", tags=["system"])
    async def health_check() -> dict:
        """Basic health check endpoint."""
        return {"status": "ok", "service": settings.app_name, "version": "0.1.0"}

    return app


app = create_app()
