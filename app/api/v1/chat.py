"""Medical AI Chatbot Endpoints.
Purely informative medical assistant with ZERO database access.
Provides general health concepts and symptom education, prohibits direct medical diagnosis/orders,
and strictly refuses non-health inquiries.
"""

from fastapi import APIRouter

from app.schemas.chat import MedicalChatRequest, MedicalChatResponse
from app.schemas.common import StandardErrorResponse
from app.services.medical_chat_service import MedicalChatService

router = APIRouter(prefix="/chat", tags=["AI Medical Chatbot"])


@router.post(
    "",
    response_model=MedicalChatResponse,
    summary="Interactive Medical AI Chatbot",
    description=(
        "Purely informative AI Medical Expert assistant with zero database access. "
        "Provides general health, anatomical, symptom, and wellness guidance. "
        "Strictly prohibits direct personal diagnosis and prescriptive orders (advises consulting a physician). "
        "Strictly refuses questions outside of the health and medical domain."
    ),
    responses={
        500: {"model": StandardErrorResponse, "description": "Internal server or AI processing error"},
    },
)
@router.post(
    "/message",
    response_model=MedicalChatResponse,
    include_in_schema=False,
)
async def chat_with_medical_expert(
    payload: MedicalChatRequest,
) -> MedicalChatResponse:
    """Stateless informative medical chat - executes without any database connection."""
    chat_service = MedicalChatService()
    return await chat_service.chat(
        message=payload.message,
        history=payload.history,
    )
