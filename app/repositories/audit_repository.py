"""Repository for Compliance and Security Audit Log operations."""

from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogFilterParams


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, log: AuditLog) -> AuditLog:
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_by_id(self, log_id: int) -> Optional[AuditLog]:
        stmt = select(AuditLog).options(joinedload(AuditLog.user)).where(AuditLog.id == log_id)
        return self.db.scalars(stmt).first()

    def get_all(
        self, filters: AuditLogFilterParams, offset: int = 0, limit: int = 20
    ) -> Tuple[List[AuditLog], int]:
        stmt = select(AuditLog).options(joinedload(AuditLog.user))

        if filters.action:
            stmt = stmt.where(AuditLog.action == filters.action)

        if filters.user_id:
            stmt = stmt.where(AuditLog.user_id == filters.user_id)

        if filters.status:
            stmt = stmt.where(AuditLog.status == filters.status)

        if filters.date_from:
            stmt = stmt.where(AuditLog.created_at >= filters.date_from)

        if filters.date_to:
            stmt = stmt.where(AuditLog.created_at <= filters.date_to)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt) or 0

        paginated_stmt = stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
        logs = list(self.db.scalars(paginated_stmt).all())

        return logs, total
