"""Pydantic schemas for User entity operations and responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import UserRole


class UserBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    email: str = Field(min_length=3, max_length=255)
    name: str = Field(min_length=2, max_length=100)
    role: UserRole = UserRole.CLINICIAN


class UserCreate(UserBase):
    password: str = Field(
        min_length=8, max_length=128, description="Password must be at least 8 characters"
    )


class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    email: str
    name: str
    role: UserRole
    is_active: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
