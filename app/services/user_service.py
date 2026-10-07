"""Service for managing system users, clinician accounts, and administrative tasks."""

from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginatedResponse, PaginationMeta, PaginationParams
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.audit_service import AuditService


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = UserRepository(db)
        self.audit_service = AuditService(db)

    def get_users(self, pagination: PaginationParams) -> PaginatedResponse[UserResponse]:
        offset = (pagination.page - 1) * pagination.page_size
        users, total = self.repo.get_all(offset=offset, limit=pagination.page_size)
        total_pages = (total + pagination.page_size - 1) // pagination.page_size if total > 0 else 1

        return PaginatedResponse(
            data=[UserResponse.model_validate(u) for u in users],
            pagination=PaginationMeta(
                page=pagination.page,
                pageSize=pagination.page_size,
                total=total,
                totalPages=total_pages,
            ),
        )

    def get_user_by_id(self, user_id: int) -> UserResponse:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found", code="USER_NOT_FOUND")
        return UserResponse.model_validate(user)

    def create_user(
        self,
        data: UserCreate,
        actor: Optional[User] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> UserResponse:
        existing = self.repo.get_by_email(data.email)
        if existing:
            raise ConflictError(
                f"Email '{data.email}' is already registered", code="EMAIL_ALREADY_EXISTS"
            )

        password_hash = hash_password(data.password)
        new_user = User(
            email=data.email,
            password_hash=password_hash,
            name=data.name,
            role=data.role,
            is_active=True,
        )
        created = self.repo.create(new_user)

        try:
            self.audit_service.log(
                action="USER_CREATED",  # type: ignore
                status="SUCCESS",  # type: ignore
                user_id=actor.id if actor else None,
                entity_type="USER",
                entity_id=str(created.id),
                request_id=request_id,
                ip_address=ip_address,
                details=f"User {created.email} created with role {created.role.value}",
            )
        except Exception:
            pass
        return UserResponse.model_validate(created)

    def update_user(
        self,
        user_id: int,
        data: UserUpdate,
        actor: Optional[User] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> UserResponse:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found", code="USER_NOT_FOUND")

        if data.name is not None:
            user.name = data.name
        if data.role is not None:
            user.role = data.role
        if data.is_active is not None:
            user.is_active = data.is_active
        if data.password is not None:
            user.password_hash = hash_password(data.password)

        updated = self.repo.update(user)
        try:
            self.audit_service.log(
                action="USER_UPDATED",  # type: ignore
                status="SUCCESS",  # type: ignore
                user_id=actor.id if actor else None,
                entity_type="USER",
                entity_id=str(updated.id),
                request_id=request_id,
                ip_address=ip_address,
                details=f"User {updated.id} updated by {actor.email if actor else 'system'}",
            )
        except Exception:
            pass
        return UserResponse.model_validate(updated)

    def delete_user(
        self,
        user_id: int,
        actor: Optional[User] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> None:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found", code="USER_NOT_FOUND")

        if actor and actor.id == user_id:
            raise ConflictError(
                "You cannot delete your own account", code="SELF_DELETION_FORBIDDEN"
            )

        self.repo.delete(user)
        try:
            self.audit_service.log(
                action="USER_DELETED",  # type: ignore
                status="SUCCESS",  # type: ignore
                user_id=actor.id if actor else None,
                entity_type="USER",
                entity_id=str(user_id),
                request_id=request_id,
                ip_address=ip_address,
                details=f"User {user.email} permanently deleted",
            )
        except Exception:
            pass
