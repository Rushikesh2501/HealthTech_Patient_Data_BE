"""SQLAlchemy AuditLog model for compliance, security tracking, and AI monitoring."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import AuditAction, AuditStatus
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    action: Mapped[str] = mapped_column(
        Enum(
            AuditAction,
            name="audit_action_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        index=True,
        nullable=False,
    )
    entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    status: Mapped[str] = mapped_column(
        Enum(
            AuditStatus,
            name="audit_status_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        default=AuditStatus.SUCCESS,
        nullable=False,
    )
    request_id: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} action={self.action} status={self.status}>"
