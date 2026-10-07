"""FastAPI database dependency."""

from typing import Generator

from sqlalchemy.orm import Session

from app.db.session import get_db_session


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides an active SQLAlchemy database session per request."""
    yield from get_db_session()
