"""Unit tests for AuthService: login, invalid credentials, inactive accounts, token refresh."""

from datetime import timedelta

import pytest
from sqlalchemy.orm import Session

from app.core.constants import UserRole
from app.core.exceptions import AuthenticationError
from app.core.security import create_access_token, decode_token, hash_password
from app.models.user import User
from app.schemas.auth import LoginRequest
from app.services.auth_service import AuthService


def test_login_successful(db_session: Session, clinician_user: User):
    service = AuthService(db_session)
    req = LoginRequest(email=clinician_user.email, password="Password123!")

    res = service.login(req)
    assert res.access_token is not None
    assert res.refresh_token is not None
    assert res.user.email == clinician_user.email
    assert res.user.role == UserRole.CLINICIAN


def test_login_invalid_password(db_session: Session, clinician_user: User):
    service = AuthService(db_session)
    req = LoginRequest(email=clinician_user.email, password="WrongPassword999!")

    with pytest.raises(AuthenticationError) as exc_info:
        service.login(req)
    assert "Invalid email or password" in str(exc_info.value.message)


def test_login_inactive_user(db_session: Session):
    inactive = User(
        email="inactive@test.local",
        name="Inactive User",
        password_hash=hash_password("Pass123!"),
        role=UserRole.CLINICIAN,
        is_active=False,
    )
    db_session.add(inactive)
    db_session.commit()

    service = AuthService(db_session)
    req = LoginRequest(email=inactive.email, password="Pass123!")

    with pytest.raises(AuthenticationError) as exc_info:
        service.login(req)
    assert "inactive" in str(exc_info.value.message).lower()


def test_refresh_token_successful(db_session: Session, clinician_user: User):
    service = AuthService(db_session)
    login_req = LoginRequest(email=clinician_user.email, password="Password123!")
    login_res = service.login(login_req)

    refreshed = service.refresh(login_res.refresh_token)
    assert refreshed.access_token is not None
    assert refreshed.refresh_token is not None
    assert refreshed.user.email == clinician_user.email


def test_expired_token():
    expired_token = create_access_token(
        subject="1", role="clinician", expires_delta=timedelta(seconds=-10)
    )
    with pytest.raises(AuthenticationError) as exc:
        decode_token(expired_token)
    assert "expired" in str(exc.value.message).lower()
