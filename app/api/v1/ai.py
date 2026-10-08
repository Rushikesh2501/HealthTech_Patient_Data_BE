"""Gemini AI Clinical Analytics API Endpoints.
Guarantees strict privacy: Never sends individual patient records or PII to Gemini.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.constants import AuditAction, AuditStatus, Permission
from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.dependencies.permissions import require_permission
from app.models.user import User
from app.schemas.ai import AITrendAnalysisRequest, AITrendAnalysisResponse
from app.schemas.chat import MedicalChatRequest, MedicalChatResponse
from app.schemas.common import StandardErrorResponse
from app.services.analytics_service import AnalyticsService
from app.services.audit_service import AuditService
from app.services.gemini_service import GeminiService
from app.services.medical_chat_service import MedicalChatService

router = APIRouter(prefix="/ai", tags=["AI Analytics"])


@router.post(
    "/trends",
    response_model=AITrendAnalysisResponse,
    summary="AI-Powered Clinical Trend Analysis",
    description="Utilizes Gemini to interpret aggregated, anonymized clinical statistics. Individual patient data is NEVER transmitted.",
    dependencies=[Depends(require_permission(Permission.ANALYTICS_AI_READ))],
    responses={
        401: {"model": StandardErrorResponse, "description": "Unauthorized"},
        403: {
            "model": StandardErrorResponse,
            "description": "Forbidden - requires analytics.ai.read (Nurse denied)",
        },
        502: {"model": StandardErrorResponse, "description": "AI processing error"},
    },
)
async def analyze_clinical_trends(
    payload: AITrendAnalysisRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AITrendAnalysisResponse:
    ip_addr = request.client.host if request.client else None
    req_id = getattr(request.state, "request_id", None)

    # 1. Aggregate statistics across the specified time frame via PostgreSQL
    analytics_service = AnalyticsService(db)
    aggregated_stats = analytics_service.get_aggregated_clinical_stats(
        from_date=payload.from_date, to_date=payload.to_date
    )

    # 2. Invoke Gemini Service with strictly aggregated data
    gemini_service = GeminiService()
    result = await gemini_service.analyze_trends(payload.question, aggregated_stats)

    # 3. Record audit trail
    audit_service = AuditService(db)
    audit_service.log(
        action=AuditAction.AI_ANALYTICS_REQUEST,
        status=AuditStatus.SUCCESS,
        user_id=current_user.id,
        entity_type="AI_ANALYTICS",
        entity_id=None,
        request_id=req_id,
        ip_address=ip_addr,
        details=f"AI query '{payload.question[:60]}...' analyzed {result.data_points_analyzed} aggregated encounters",
    )

    return result


@router.post(
    "/chat",
    response_model=MedicalChatResponse,
    summary="Interactive Medical AI Chatbot",
    description="Conversational medical expert assistant with strict safety guardrails and zero database access.",
    responses={
        500: {"model": StandardErrorResponse, "description": "Internal server or AI processing error"},
    },
)
async def chat_with_medical_expert(
    payload: MedicalChatRequest,
) -> MedicalChatResponse:
    chat_service = MedicalChatService()
    return await chat_service.chat(
        message=payload.message,
        history=payload.history,
    )
