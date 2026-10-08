"""Authentication dependencies for FastAPI route handlers."""

from typing import Optional

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError
from app.core.security import decode_token
from app.dependencies.database import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

# Support standard Bearer tokens via HTTPBearer with auto_error=False
security = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Extract and validate the JWT Bearer token, returning the authenticated User.
    Raises 401 AuthenticationError on missing or invalid tokens.
    """
    token: Optional[str] = None
    if credentials:
        token = credentials.credentials
    else:
        # Fallback to Authorization header manually if needed
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]

    if not token:
        raise AuthenticationError(
            "Authorization header is missing or malformed", code="MISSING_TOKEN"
        )

    payload = decode_token(token, expected_type="access")
    user_id_raw = payload.get("sub")
    if not user_id_raw:
        raise AuthenticationError("Invalid token subject", code="INVALID_TOKEN")

    try:
        user_id = int(user_id_raw)
    except ValueError:
        raise AuthenticationError("Malformed user ID in token", code="INVALID_TOKEN")

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if not user:
        raise AuthenticationError(
            "User associated with token no longer exists", code="USER_NOT_FOUND"
        )

    if not user.is_active:
        raise AuthenticationError("User account is inactive", code="ACCOUNT_INACTIVE")

    # Attach current user to request state for middleware or audit loggers
    request.state.current_user = user
    request.state.user_id = user.id
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Convenience alias guaranteeing active status."""
    return current_user


def get_optional_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Gracefully extracts the authenticated User if valid credentials are provided,
    otherwise returns None without raising an authentication exception.
    """
    token: Optional[str] = None
    if credentials:
        token = credentials.credentials
    else:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]

    if not token:
        return None

    try:
        payload = decode_token(token, expected_type="access")
        user_id_raw = payload.get("sub")
        if not user_id_raw:
            return None
        user_id = int(user_id_raw)
        user_repo = UserRepository(db)
        user = user_repo.get_by_id(user_id)
        if user and user.is_active:
            request.state.current_user = user
            request.state.user_id = user.id
            return user
    except Exception:
        return None

    return None
