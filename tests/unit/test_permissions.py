"""Unit tests for RBAC permission mapping and enforcement."""

import pytest

from app.core.constants import Permission, UserRole
from app.core.exceptions import ForbiddenError
from app.core.permissions import check_permission, has_permission


def test_superadmin_has_all_permissions():
    for perm in Permission:
        assert has_permission(UserRole.SUPERADMIN, perm) is True


def test_admin_has_all_permissions():
    for perm in Permission:
        assert has_permission(UserRole.ADMIN, perm) is True


def test_clinician_permissions():
    assert has_permission(UserRole.CLINICIAN, Permission.PATIENTS_READ) is True
    assert has_permission(UserRole.CLINICIAN, Permission.PATIENTS_CREATE) is True
    assert has_permission(UserRole.CLINICIAN, Permission.PATIENTS_UPDATE) is True
    assert has_permission(UserRole.CLINICIAN, Permission.PATIENTS_DELETE) is False

    assert has_permission(UserRole.CLINICIAN, Permission.ENCOUNTERS_READ) is True
    assert has_permission(UserRole.CLINICIAN, Permission.ENCOUNTERS_CREATE) is True
    assert has_permission(UserRole.CLINICIAN, Permission.ENCOUNTERS_DELETE) is False

    assert has_permission(UserRole.CLINICIAN, Permission.ANALYTICS_READ) is True
    assert has_permission(UserRole.CLINICIAN, Permission.ANALYTICS_AI_READ) is True

    assert has_permission(UserRole.CLINICIAN, Permission.USERS_READ) is False
    assert has_permission(UserRole.CLINICIAN, Permission.AUDIT_READ) is False


def test_nurse_permissions():
    assert has_permission(UserRole.NURSE, Permission.PATIENTS_READ) is True
    assert has_permission(UserRole.NURSE, Permission.PATIENTS_CREATE) is False
    assert has_permission(UserRole.NURSE, Permission.PATIENTS_DELETE) is False

    assert has_permission(UserRole.NURSE, Permission.ENCOUNTERS_READ) is True
    assert has_permission(UserRole.NURSE, Permission.ENCOUNTERS_CREATE) is True
    assert has_permission(UserRole.NURSE, Permission.ENCOUNTERS_UPDATE) is True
    assert has_permission(UserRole.NURSE, Permission.ENCOUNTERS_DELETE) is False

    assert has_permission(UserRole.NURSE, Permission.ANALYTICS_READ) is False
    assert has_permission(UserRole.NURSE, Permission.ANALYTICS_AI_READ) is False
    assert has_permission(UserRole.NURSE, Permission.AUDIT_READ) is False


def test_check_permission_raises_forbidden():
    # Nurse trying to delete patient
    with pytest.raises(ForbiddenError) as exc_info:
        check_permission(UserRole.NURSE, Permission.PATIENTS_DELETE)
    assert "Missing required permission" in str(exc_info.value.message)
