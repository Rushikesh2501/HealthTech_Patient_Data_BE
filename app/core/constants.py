"""System constants, role definitions, and permission specifications."""

from enum import Enum


class UserRole(str, Enum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    CLINICIAN = "clinician"
    NURSE = "nurse"


class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class EncounterStatus(str, Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"
    PENDING = "pending"
    FAILED = "failed"


class PatientStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class AuditAction(str, Enum):
    LOGIN = "LOGIN"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    PATIENT_CREATED = "PATIENT_CREATED"
    PATIENT_UPDATED = "PATIENT_UPDATED"
    PATIENT_DELETED = "PATIENT_DELETED"
    ENCOUNTER_CREATED = "ENCOUNTER_CREATED"
    ENCOUNTER_UPDATED = "ENCOUNTER_UPDATED"
    ENCOUNTER_DELETED = "ENCOUNTER_DELETED"
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"
    AI_ANALYTICS_REQUEST = "AI_ANALYTICS_REQUEST"


class AuditStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    DENIED = "DENIED"


# Centralized permission constants
class Permission(str, Enum):
    PATIENTS_READ = "patients.read"
    PATIENTS_CREATE = "patients.create"
    PATIENTS_UPDATE = "patients.update"
    PATIENTS_DELETE = "patients.delete"

    ENCOUNTERS_READ = "encounters.read"
    ENCOUNTERS_CREATE = "encounters.create"
    ENCOUNTERS_UPDATE = "encounters.update"
    ENCOUNTERS_DELETE = "encounters.delete"

    ANALYTICS_READ = "analytics.read"
    ANALYTICS_AI_READ = "analytics.ai.read"

    AUDIT_READ = "audit.read"

    USERS_READ = "users.read"
    USERS_CREATE = "users.create"
    USERS_UPDATE = "users.update"
    USERS_DELETE = "users.delete"

    SETTINGS_MANAGE = "settings.manage"


# Mapping from UserRole to set of Permissions
ROLE_PERMISSIONS: dict[UserRole, set[Permission]] = {
    UserRole.SUPERADMIN: set(Permission),
    UserRole.ADMIN: {
        Permission.PATIENTS_READ,
        Permission.PATIENTS_CREATE,
        Permission.PATIENTS_UPDATE,
        Permission.PATIENTS_DELETE,
        Permission.ENCOUNTERS_READ,
        Permission.ENCOUNTERS_CREATE,
        Permission.ENCOUNTERS_UPDATE,
        Permission.ENCOUNTERS_DELETE,
        Permission.ANALYTICS_READ,
        Permission.ANALYTICS_AI_READ,
        Permission.AUDIT_READ,
        Permission.USERS_READ,
        Permission.USERS_CREATE,
        Permission.USERS_UPDATE,
        Permission.USERS_DELETE,
        Permission.SETTINGS_MANAGE,
    },
    UserRole.CLINICIAN: {
        Permission.PATIENTS_READ,
        Permission.PATIENTS_CREATE,
        Permission.PATIENTS_UPDATE,
        Permission.ENCOUNTERS_READ,
        Permission.ENCOUNTERS_CREATE,
        Permission.ENCOUNTERS_UPDATE,
        Permission.ANALYTICS_READ,
        Permission.ANALYTICS_AI_READ,
    },
    UserRole.NURSE: {
        Permission.PATIENTS_READ,
        Permission.ENCOUNTERS_READ,
        Permission.ENCOUNTERS_CREATE,
        Permission.ENCOUNTERS_UPDATE,
    },
}
