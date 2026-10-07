"""Datetime and timezone helpers (strictly UTC)."""

from datetime import date, datetime, timezone
from typing import Optional


def utc_now() -> datetime:
    """Return the current time in UTC with timezone awareness."""
    return datetime.now(timezone.utc)


def utc_today() -> date:
    """Return the current date in UTC."""
    return datetime.now(timezone.utc).date()


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure a datetime object is timezone-aware and set to UTC."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
