"""Permission dependency factory for role-based access control.
Enforces that backend RBAC is the definitive security boundary.
"""

from typing import Callable

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.constants import AuditAction, AuditStatus, Permission
from app.core.exceptions import ForbiddenError
from app.core.permissions import has_permission
from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.user import User
from app.services.audit_service import AuditService


def require_permission(permission: Permission | str) -> Callable[[User, Request, Session], User]:
    """Dependency factory that validates whether the authenticated user holds the required permission.
    Raises 403 ForbiddenError if unauthorized, and records an UNAUTHORIZED_ACCESS audit log.
    """
    perm_val = permission.value if isinstance(permission, Permission) else str(permission)

    def dependency(
        current_user: User = Depends(get_current_user),
        request: Request = None,  # type: ignore
        db: Session = Depends(get_db),
    ) -> User:
        if not has_permission(current_user.role, perm_val):
            # Capture unauthorized attempt for security monitoring
            req_id = (
                getattr(request.state, "request_id", None)
                if request and hasattr(request, "state")
                else None
            )
            client_ip = request.client.host if request and request.client else None

            audit_service = AuditService(db)
            audit_service.log(
                action=AuditAction.UNAUTHORIZED_ACCESS,
                status=AuditStatus.DENIED,
                user_id=current_user.id,
                entity_type="PERMISSION",
                entity_id=perm_val,
                request_id=req_id,
                ip_address=client_ip,
                details=f"User {current_user.email} (role: {current_user.role}) denied permission '{perm_val}' for path {request.url.path if request else 'unknown'}",
            )

            raise ForbiddenError(
                message=f"Access denied. You do not have permission '{perm_val}'.",
                code="FORBIDDEN_PERMISSION",
                details={
                    "required_permission": perm_val,
                    "user_role": (
                        current_user.role.value
                        if hasattr(current_user.role, "value")
                        else str(current_user.role)
                    ),
                },
            )
        return current_user

    return dependency
