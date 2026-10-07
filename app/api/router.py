"""Root API Router for HealthTech Patient Data Dashboard."""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.api.v1 import v1_router
from app.api.v1.ai import router as ai_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.audit_logs import router as audit_router
from app.api.v1.auth import get_me, login, logout, refresh_token
from app.api.v1.auth import router as auth_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.encounters import router as encounters_router
from app.api.v1.patients import router as patients_router
from app.api.v1.users import router as users_router
from app.db.database import check_db_connection
from app.schemas.auth import LogoutResponse, TokenResponse
from app.schemas.user import UserResponse

api_router = APIRouter()

# 1. Mount versioned API routes under /v1 (Primary source of truth for documented API)
api_router.include_router(v1_router)

# 2. Mount fallback unversioned routes with include_in_schema=False (avoids duplicate Swagger entries)
api_router.include_router(auth_router, include_in_schema=False)
api_router.include_router(users_router, include_in_schema=False)
api_router.include_router(patients_router, include_in_schema=False)
api_router.include_router(encounters_router, include_in_schema=False)
api_router.include_router(dashboard_router, include_in_schema=False)
api_router.include_router(analytics_router, include_in_schema=False)
api_router.include_router(ai_router, include_in_schema=False)
api_router.include_router(audit_router, include_in_schema=False)

# 3. Direct aliases for frontends invoking /api/me, /api/login, etc. without /auth
api_router.add_api_route(
    "/me",
    get_me,
    methods=["GET"],
    response_model=UserResponse,
    include_in_schema=False,
)
api_router.add_api_route(
    "/login",
    login,
    methods=["POST"],
    response_model=TokenResponse,
    include_in_schema=False,
)
api_router.add_api_route(
    "/refresh",
    refresh_token,
    methods=["POST"],
    response_model=TokenResponse,
    include_in_schema=False,
)
api_router.add_api_route(
    "/logout",
    logout,
    methods=["POST"],
    response_model=LogoutResponse,
    include_in_schema=False,
)


@api_router.get("", include_in_schema=False)
@api_router.get("/", include_in_schema=False)
@api_router.get("/v1", include_in_schema=False)
@api_router.get("/v1/", include_in_schema=False)
def api_status_root():
    return {
        "status": "online",
        "service": "HealthTech Patient Data Management API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "docs": "/docs",
            "auth": "/api/v1/auth/login",
            "patients": "/api/v1/patients",
            "encounters": "/api/v1/encounters",
            "dashboard": "/api/v1/dashboard/summary",
            "analytics": "/api/v1/analytics/trends",
        },
    }


@api_router.get("/health", tags=["Health"], summary="Liveness Health Check", include_in_schema=False)
def health_check():
    """Liveness probe: verifies that the web service process is active."""
    return {"status": "healthy"}


@api_router.get("/ready", tags=["Health"], summary="Readiness Health Check", include_in_schema=False)
def readiness_check():
    """Readiness probe: validates database connectivity before accepting customer traffic."""
    db_ok = check_db_connection()
    if not db_ok:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "database": "disconnected"},
        )
    return {"status": "ready", "database": "connected"}
