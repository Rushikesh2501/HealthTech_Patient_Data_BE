"""Service for capturing compliance, access, and modification audit trails."""

from typing import Optional

from sqlalchemy.orm import Session

from app.core.constants import AuditAction, AuditStatus
from app.models.audit_log import AuditLog
from app.repositories.audit_repository import AuditRepository
from app.schemas.audit_log import AuditLogFilterParams, AuditLogResponse
from app.schemas.common import PaginatedResponse, PaginationMeta, PaginationParams


class AuditService:
    def __init__(self, db: Session):
        self.repository = AuditRepository(db)

    def log(
        self,
        action: AuditAction,
        status: AuditStatus = AuditStatus.SUCCESS,
        user_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[str] = None,
    ) -> AuditLog:
        """Create and persist an immutable audit trail entry."""
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            status=status,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            request_id=request_id,
            ip_address=ip_address,
            details=details,
        )
        return self.repository.create(audit_entry)

    def get_audit_logs(
        self, filters: AuditLogFilterParams, pagination: PaginationParams
    ) -> PaginatedResponse[AuditLogResponse]:
        offset = (pagination.page - 1) * pagination.page_size
        items, total = self.repository.get_all(filters, offset=offset, limit=pagination.page_size)

        total_pages = (total + pagination.page_size - 1) // pagination.page_size if total > 0 else 1

        formatted = []
        for item in items:
            formatted.append(
                AuditLogResponse(
                    id=item.id,
                    user_id=item.user_id,
                    user_email=item.user.email if item.user else None,
                    user_role=item.user.role.value if item.user else None,
                    action=AuditAction(item.action),
                    entity_type=item.entity_type,
                    entity_id=item.entity_id,
                    status=AuditStatus(item.status),
                    request_id=item.request_id,
                    ip_address=item.ip_address,
                    details=item.details,
                    created_at=item.created_at,
                )
            )

        return PaginatedResponse(
            data=formatted,
            pagination=PaginationMeta(
                page=pagination.page,
                pageSize=pagination.page_size,
                total=total,
                totalPages=total_pages,
            ),
        )
