"""Database session context manager and generator."""

from typing import Generator

from sqlalchemy.orm import Session

from app.db.database import SessionLocal


def get_db_session() -> Generator[Session, None, None]:
    """Yield a database session and safely commit or rollback on exception."""
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
