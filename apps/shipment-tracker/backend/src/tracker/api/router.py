"""Main API router that aggregates all sub-routers."""

from fastapi import APIRouter

from tracker.api.deals import router as deals_router
from tracker.api.vessels import router as vessels_router
from tracker.api.shipments import router as shipments_router
from tracker.api.dashboard import router as dashboard_router
from tracker.api.alerts import router as alerts_router
from tracker.api.counterparties import router as counterparties_router
from tracker.api.reports import router as reports_router
from tracker.api.meetings import router as meetings_router
from tracker.api.ai import router as ai_router
from tracker.api.auth import router as auth_router
from tracker.api.analytics import router as analytics_router

api_router = APIRouter()

api_router.include_router(deals_router, prefix="/deals", tags=["deals"])
api_router.include_router(vessels_router, prefix="/vessels", tags=["vessels"])
api_router.include_router(shipments_router, prefix="/shipments", tags=["shipments"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(alerts_router, prefix="/alerts", tags=["alerts"])
api_router.include_router(counterparties_router, prefix="/counterparties", tags=["counterparties"])
api_router.include_router(reports_router, prefix="/reports", tags=["reports"])
api_router.include_router(meetings_router, prefix="/meetings", tags=["meetings"])
api_router.include_router(ai_router, prefix="/ai", tags=["ai"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
