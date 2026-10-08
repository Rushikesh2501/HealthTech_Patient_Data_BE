"""Pydantic schemas for the AI Medical Chatbot."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ChatMessage(BaseModel):
    """Single message in a conversational thread."""

    model_config = ConfigDict(populate_by_name=True)

    role: str = Field(
        ...,
        description="Author role: 'user' for human query, 'assistant' or 'model' for AI response",
        examples=["user", "assistant"],
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Text content of the message",
    )


class MedicalChatRequest(BaseModel):
    """Payload for conversational medical AI assistant."""

    model_config = ConfigDict(populate_by_name=True)

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's question or statement",
        examples=["What are some common lifestyle habits to maintain healthy blood pressure?"],
    )
    history: Optional[List[ChatMessage]] = Field(
        default_factory=list,
        description="Optional list of previous messages in this conversation for context",
    )


class MedicalChatResponse(BaseModel):
    """Response returned by the medical AI chatbot."""

    model_config = ConfigDict(populate_by_name=True)

    reply: str = Field(
        ...,
        description="AI assistant's response adhering to medical expert safety constraints",
    )
    disclaimer: str = Field(
        default=(
            "This information is strictly for educational purposes and is not a substitute for "
            "professional medical advice, diagnosis, or treatment. Always consult a qualified "
            "physician or healthcare provider with any medical questions or emergencies."
        ),
        description="Clinical advisory disclaimer",
    )
    timestamp: datetime = Field(
        ...,
        description="UTC timestamp when the response was generated",
    )
