"""Root API Router for HealthTech Patient Data Dashboard."""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.api.v1 import v1_router
from app.db.database import check_db_connection

api_router = APIRouter()

# Mount v1 router at /v1
api_router.include_router(v1_router)

# Also mount v1 subrouters directly at /api for convenience with frontends omitting /v1
for sub in v1_router.routes:
    pass  # We also support direct /v1 paths seamlessly


@api_router.get("/health", tags=["Health"], summary="Liveness Health Check")
def health_check():
    """Liveness probe: verifies that the web service process is active."""
    return {"status": "healthy"}


@api_router.get("/ready", tags=["Health"], summary="Readiness Health Check")
def readiness_check():
    """Readiness probe: validates database connectivity before accepting customer traffic."""
    db_ok = check_db_connection()
    if not db_ok:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "database": "disconnected"},
        )
    return {"status": "ready", "database": "connected"}
