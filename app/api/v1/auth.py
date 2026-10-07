"""Authentication API Endpoints."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest, ChangePasswordResponse, LoginRequest, LogoutResponse, RefreshTokenRequest, TokenResponse
from app.schemas.common import StandardErrorResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate User and Obtain JWT Tokens",
    description="Validates credentials, updates last login timestamp, records an audit log, and issues JWT access and refresh tokens.",
    responses={
        401: {
            "model": StandardErrorResponse,
            "description": "Invalid credentials or deactivated account",
        },
        422: {"model": StandardErrorResponse, "description": "Request validation error"},
    },
)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    ip_addr = request.client.host if request.client else None
    req_id = getattr(request.state, "request_id", None)
    service = AuthService(db)
    return service.login(payload, ip_address=ip_addr, request_id=req_id)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotate JWT Access and Refresh Tokens",
    description="Validates a long-lived refresh token and issues a new pair of access and refresh tokens.",
    responses={
        401: {"model": StandardErrorResponse, "description": "Invalid or expired refresh token"},
    },
)
def refresh_token(
    payload: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    ip_addr = request.client.host if request.client else None
    req_id = getattr(request.state, "request_id", None)
    service = AuthService(db)
    return service.refresh(payload.refresh_token, ip_address=ip_addr, request_id=req_id)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="User Logout",
    description="Audits the user logout event and invalidates the client session.",
    responses={
        401: {
            "model": StandardErrorResponse,
            "description": "Missing or invalid authentication token",
        },
    },
)
def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LogoutResponse:
    ip_addr = request.client.host if request.client else None
    req_id = getattr(request.state, "request_id", None)
    service = AuthService(db)
    service.logout(current_user, ip_address=ip_addr, request_id=req_id)
    return LogoutResponse(message="Logged out successfully")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Retrieve Authenticated User Profile",
    description="Returns identity, role, and details of the currently authenticated user.",
    responses={
        401: {"model": StandardErrorResponse, "description": "Unauthorized access"},
    },
)
def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post(
    "/change-password",
    response_model=ChangePasswordResponse,
    summary="Change User Password",
    description="Validates old password, updates password hash, and records audit trail.",
    responses={
        400: {"model": StandardErrorResponse, "description": "Validation error or password reuse"},
        401: {"model": StandardErrorResponse, "description": "Incorrect current password"},
    },
)
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChangePasswordResponse:
    ip_addr = request.client.host if request.client else None
    req_id = getattr(request.state, "request_id", None)
    service = AuthService(db)
    return service.change_password(current_user, payload, ip_address=ip_addr, request_id=req_id)
