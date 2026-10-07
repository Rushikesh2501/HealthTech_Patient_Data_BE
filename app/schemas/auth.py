"""Pydantic schemas for Authentication requests and responses."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1)
    remember_me: bool = Field(default=False, alias="rememberMe")


class RefreshTokenRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    refresh_token: str = Field(min_length=10, alias="refreshToken")


class TokenResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    access_token: str
    token_type: str = "bearer"
    token: str  # Direct alias for frontend ease
    refresh_token: Optional[str] = None
    refreshToken: Optional[str] = None
    expires_in: int
    user: UserResponse


class LogoutResponse(BaseModel):
    message: str = "Logged out successfully"


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    old_password: str = Field(min_length=1, alias="oldPassword")
    new_password: str = Field(min_length=8, max_length=128, alias="newPassword")


class ChangePasswordResponse(BaseModel):
    message: str = "Password updated successfully. Please log in again."
