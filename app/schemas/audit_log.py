"""Pydantic schemas for Audit Log entries."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import AuditAction, AuditStatus


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    user_id: Optional[int] = Field(default=None, alias="userId")
    user_email: Optional[str] = Field(default=None, alias="user")
    user_role: Optional[str] = Field(default=None, alias="role")
    action: AuditAction
    entity_type: Optional[str] = Field(default=None, alias="entity")
    entity_id: Optional[str] = Field(default=None, alias="entityId")
    status: AuditStatus
    request_id: Optional[str] = Field(default=None, alias="requestId")
    ip_address: Optional[str] = Field(default=None, alias="ipAddress")
    details: Optional[str] = None
    created_at: datetime = Field(alias="timestamp")


class AuditLogFilterParams(BaseModel):
    action: Optional[AuditAction] = None
    user_id: Optional[int] = None
    status: Optional[AuditStatus] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
