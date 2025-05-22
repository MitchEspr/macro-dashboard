# backend/app/api/api.py

from fastapi import APIRouter
from app.api.endpoints import indicators, new_indicators

router = APIRouter()

# Include the new unified indicators router (preferred)
router.include_router(
    new_indicators.router,
    prefix="/v2/indicators",
    tags=["indicators-v2"]
)

# Keep the old indicators router for backward compatibility
router.include_router(
    indicators.router,
    prefix="/indicators",
    tags=["indicators-legacy"]
)

@router.get("/")
async def root():
    return {
        "message": "Welcome to the Macro Dashboard API",
        "versions": {
            "v1": "/api/indicators (legacy endpoints)",
            "v2": "/api/v2/indicators (new unified endpoints)"
        },
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "indicators_v2": "/api/v2/indicators",
            "market_status": "/api/v2/indicators/market-status",
            "categories": "/api/v2/indicators/categories"
        }
    }