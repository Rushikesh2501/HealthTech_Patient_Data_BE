"""Repository for User database operations."""

from typing import Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(func.lower(User.email) == func.lower(email))
        return self.db.scalars(stmt).first()

    def get_all(self, offset: int = 0, limit: int = 20) -> Tuple[list[User], int]:
        total_stmt = select(func.count(User.id))
        total = self.db.scalar(total_stmt) or 0

        stmt = select(User).order_by(User.id.asc()).offset(offset).limit(limit)
        items = list(self.db.scalars(stmt).all())
        return items, total

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User) -> User:
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.commit()

    def count_active(self) -> int:
        stmt = select(func.count(User.id)).where(User.is_active.is_(True))
        return self.db.scalar(stmt) or 0
