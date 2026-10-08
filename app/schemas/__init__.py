"""Pydantic Schemas package."""

from app.schemas.ai import AITrendAnalysisRequest, AITrendAnalysisResponse
from app.schemas.analytics import (
    AnalyticsFilterParams,
    AnalyticsOverviewResponse,
    AnalyticsTrendsResponse,
)
from app.schemas.audit_log import AuditLogFilterParams, AuditLogResponse
from app.schemas.auth import LoginRequest, LogoutResponse, RefreshTokenRequest, TokenResponse
from app.schemas.chat import ChatMessage, MedicalChatRequest, MedicalChatResponse
from app.schemas.common import (
    ApiResponse,
    ErrorDetail,
    PaginatedResponse,
    PaginationMeta,
    PaginationParams,
    StandardErrorResponse,
)
from app.schemas.dashboard import (
    AgeDistributionPoint,
    DashboardSummary,
    DiagnosisDistributionPoint,
    EncounterTrendPoint,
    SeasonalTrendPoint,
)
from app.schemas.encounter import (
    EncounterBase,
    EncounterCreate,
    EncounterFilterParams,
    EncounterResponse,
    EncounterUpdate,
)
from app.schemas.patient import (
    PatientBase,
    PatientCreate,
    PatientFilterParams,
    PatientResponse,
    PatientUpdate,
)
from app.schemas.user import UserBase, UserCreate, UserResponse, UserUpdate

__all__ = [
    "AITrendAnalysisRequest",
    "AITrendAnalysisResponse",
    "AnalyticsFilterParams",
    "AnalyticsOverviewResponse",
    "AnalyticsTrendsResponse",
    "AuditLogFilterParams",
    "AuditLogResponse",
    "LoginRequest",
    "LogoutResponse",
    "RefreshTokenRequest",
    "TokenResponse",
    "ApiResponse",
    "ErrorDetail",
    "PaginatedResponse",
    "PaginationMeta",
    "PaginationParams",
    "StandardErrorResponse",
    "AgeDistributionPoint",
    "DashboardSummary",
    "DiagnosisDistributionPoint",
    "EncounterTrendPoint",
    "SeasonalTrendPoint",
    "EncounterBase",
    "EncounterCreate",
    "EncounterFilterParams",
    "EncounterResponse",
    "EncounterUpdate",
    "PatientBase",
    "PatientCreate",
    "PatientFilterParams",
    "PatientResponse",
    "PatientUpdate",
    "UserBase",
    "UserCreate",
    "UserResponse",
    "UserUpdate",
    "ChatMessage",
    "MedicalChatRequest",
    "MedicalChatResponse",
]
