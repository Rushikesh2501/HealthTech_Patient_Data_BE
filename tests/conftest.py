import os
import sys
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient

# Ensure root directory is on Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Force test environment variables before importing app
os.environ["APP_ENV"] = "test"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-32-chars-minimum-healthtech-secure"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.constants import UserRole
from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.dependencies.database import get_db
from app.main import app
from app.models.patient import Patient
from app.models.user import User

# In-memory test engine for fast unit and integration tests
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create all schema tables once for the test session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a fresh transactional session for each test that rolls back changes."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """TestClient with get_db dependency overridden to the test database session."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db_session: Session) -> User:
    user = User(
        email="admin@test.local",
        name="Admin Test User",
        password_hash=hash_password("Password123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def clinician_user(db_session: Session) -> User:
    user = User(
        email="clinician@test.local",
        name="Clinician Test User",
        password_hash=hash_password("Password123!"),
        role=UserRole.CLINICIAN,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def nurse_user(db_session: Session) -> User:
    user = User(
        email="nurse@test.local",
        name="Nurse Test User",
        password_hash=hash_password("Password123!"),
        role=UserRole.NURSE,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user: User) -> str:
    return create_access_token(subject=admin_user.id, role=admin_user.role.value)


@pytest.fixture
def clinician_token(clinician_user: User) -> str:
    return create_access_token(subject=clinician_user.id, role=clinician_user.role.value)


@pytest.fixture
def nurse_token(nurse_user: User) -> str:
    return create_access_token(subject=nurse_user.id, role=nurse_user.role.value)


@pytest.fixture
def sample_patient(db_session: Session) -> Patient:
    from datetime import date

    patient = Patient(
        patient_code="PT-9999",
        age=35,
        gender="Female",
        registration_date=date(2026, 1, 15),
        status="active",
    )
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)
    return patient
