"""Main API router that aggregates all sub-routers."""

from fastapi import APIRouter

from tracker.api.deals import router as deals_router
from tracker.api.vessels import router as vessels_router
from tracker.api.shipments import router as shipments_router
from tracker.api.dashboard import router as dashboard_router
from tracker.api.alerts import router as alerts_router

api_router = APIRouter()

api_router.include_router(deals_router, prefix="/deals", tags=["deals"])
api_router.include_router(vessels_router, prefix="/vessels", tags=["vessels"])
api_router.include_router(shipments_router, prefix="/shipments", tags=["shipments"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(alerts_router, prefix="/alerts", tags=["alerts"])
