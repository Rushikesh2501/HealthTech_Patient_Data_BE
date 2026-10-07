"""Service for user authentication, JWT generation, and token refresh."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import AuditAction, AuditStatus
from app.core.exceptions import AuthenticationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserResponse
from app.services.audit_service import AuditService


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.audit_service = AuditService(db)

    def authenticate_user(self, email: str, plain_password: str) -> Optional[User]:
        user = self.user_repo.get_by_email(email)
        if not user:
            return None
        if not verify_password(plain_password, user.password_hash):
            return None
        return user

    def login(
        self,
        request: LoginRequest,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> TokenResponse:
        user = self.user_repo.get_by_email(request.email)

        # Constant-time mitigation against user enumeration
        if not user or not verify_password(request.password, user.password_hash):
            self.audit_service.log(
                action=AuditAction.LOGIN_FAILED,
                status=AuditStatus.FAILED,
                user_id=user.id if user else None,
                entity_type="USER",
                entity_id=str(user.id) if user else request.email,
                request_id=request_id,
                ip_address=ip_address,
                details=f"Failed login attempt for {request.email}",
            )
            raise AuthenticationError("Invalid email or password", code="INVALID_CREDENTIALS")

        if not user.is_active:
            self.audit_service.log(
                action=AuditAction.LOGIN_FAILED,
                status=AuditStatus.DENIED,
                user_id=user.id,
                entity_type="USER",
                entity_id=str(user.id),
                request_id=request_id,
                ip_address=ip_address,
                details="Attempted login on deactivated account",
            )
            raise AuthenticationError(
                "User account is inactive. Please contact support.", code="ACCOUNT_INACTIVE"
            )

        # Update last login timestamp
        user.last_login_at = datetime.now(timezone.utc)
        self.user_repo.update(user)

        # Generate tokens
        access_token = create_access_token(subject=user.id, role=user.role.value)
        refresh_token = create_refresh_token(subject=user.id)

        # Audit successful login
        self.audit_service.log(
            action=AuditAction.LOGIN,
            status=AuditStatus.SUCCESS,
            user_id=user.id,
            entity_type="USER",
            entity_id=str(user.id),
            request_id=request_id,
            ip_address=ip_address,
            details=f"Successful login for role {user.role.value}",
        )

        user_response = UserResponse.model_validate(user)
        return TokenResponse(
            access_token=access_token,
            token=access_token,
            refresh_token=refresh_token,
            refreshToken=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_response,
        )

    def refresh(
        self, refresh_token: str, ip_address: Optional[str] = None, request_id: Optional[str] = None
    ) -> TokenResponse:
        payload = decode_token(refresh_token, expected_type="refresh")
        user_id_raw = payload.get("sub")
        if not user_id_raw:
            raise AuthenticationError("Invalid refresh token payload", code="INVALID_TOKEN")

        try:
            user_id = int(user_id_raw)
        except ValueError:
            raise AuthenticationError("Malformed user ID in token", code="INVALID_TOKEN")

        user = self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise AuthenticationError("User no longer exists or is inactive", code="USER_INACTIVE")

        new_access_token = create_access_token(subject=user.id, role=user.role.value)
        new_refresh_token = create_refresh_token(subject=user.id)

        user_response = UserResponse.model_validate(user)
        return TokenResponse(
            access_token=new_access_token,
            token=new_access_token,
            refresh_token=new_refresh_token,
            refreshToken=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_response,
        )

    def logout(
        self, user: User, ip_address: Optional[str] = None, request_id: Optional[str] = None
    ) -> None:
        self.audit_service.log(
            action=AuditAction.LOGOUT,
            status=AuditStatus.SUCCESS,
            user_id=user.id,
            entity_type="USER",
            entity_id=str(user.id),
            request_id=request_id,
            ip_address=ip_address,
            details=f"User {user.email} logged out",
        )
