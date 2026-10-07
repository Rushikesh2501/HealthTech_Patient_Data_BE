"""Audit Logs API Endpoints (Admin RBAC Protected)."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.constants import AuditAction, AuditStatus, Permission
from app.dependencies.database import get_db
from app.dependencies.permissions import require_permission
from app.schemas.audit_log import AuditLogFilterParams, AuditLogResponse
from app.schemas.common import PaginatedResponse, PaginationParams, StandardErrorResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get(
    "",
    response_model=PaginatedResponse[AuditLogResponse],
    summary="List System Audit Logs",
    description="Retrieve system security, compliance, access, and modification logs. Restricted to administrators.",
    dependencies=[Depends(require_permission(Permission.AUDIT_READ))],
    responses={
        401: {"model": StandardErrorResponse, "description": "Unauthorized"},
        403: {"model": StandardErrorResponse, "description": "Forbidden - requires audit.read"},
    },
)
def list_audit_logs(
    action: Optional[AuditAction] = Query(None, description="Filter by audit action"),
    user_id: Optional[int] = Query(None, alias="userId", description="Filter by user ID"),
    status: Optional[AuditStatus] = Query(
        None, description="Filter by status (SUCCESS, FAILED, DENIED)"
    ),
    date_from: Optional[datetime] = Query(None, alias="dateFrom"),
    date_to: Optional[datetime] = Query(None, alias="dateTo"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize", description="Items per page"),
    db: Session = Depends(get_db),
) -> PaginatedResponse[AuditLogResponse]:
    filters = AuditLogFilterParams(
        action=action,
        user_id=user_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
    )
    pagination = PaginationParams(page=page, page_size=page_size)
    service = AuditService(db)
    return service.get_audit_logs(filters, pagination)
