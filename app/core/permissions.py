"""RBAC permission enforcement engine."""

from typing import Set

from app.core.constants import ROLE_PERMISSIONS, Permission, UserRole
from app.core.exceptions import ForbiddenError


def get_permissions_for_role(role: UserRole | str) -> Set[Permission]:
    """Retrieve all authorized permissions for a given user role."""
    try:
        user_role = UserRole(role) if isinstance(role, str) else role
    except ValueError:
        return set()
    return ROLE_PERMISSIONS.get(user_role, set())


def has_permission(role: UserRole | str, permission: Permission | str) -> bool:
    """Check if a specific role possesses the required permission."""
    try:
        perm = Permission(permission) if isinstance(permission, str) else permission
    except ValueError:
        return False

    allowed_permissions = get_permissions_for_role(role)
    return perm in allowed_permissions


def check_permission(role: UserRole | str, permission: Permission | str) -> None:
    """Verify that a role has the required permission; raises ForbiddenError otherwise."""
    perm_str = permission.value if isinstance(permission, Permission) else str(permission)
    if not has_permission(role, permission):
        raise ForbiddenError(
            message=f"Access denied. Missing required permission: '{perm_str}'.",
            code="FORBIDDEN_PERMISSION",
            details={"required_permission": perm_str, "user_role": str(role)},
        )
