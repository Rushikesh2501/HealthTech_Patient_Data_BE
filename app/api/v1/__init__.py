"""API v1 Endpoints Router aggregation."""

from fastapi import APIRouter

from app.api.v1.ai import router as ai_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.audit_logs import router as audit_router
from app.api.v1.auth import router as auth_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.encounters import router as encounters_router
from app.api.v1.patients import router as patients_router
from app.api.v1.users import router as users_router

v1_router = APIRouter(prefix="/v1")

v1_router.include_router(auth_router)
v1_router.include_router(users_router)
v1_router.include_router(patients_router)
v1_router.include_router(encounters_router)
v1_router.include_router(dashboard_router)
v1_router.include_router(analytics_router)
v1_router.include_router(ai_router)
v1_router.include_router(audit_router)

__all__ = ["v1_router"]
