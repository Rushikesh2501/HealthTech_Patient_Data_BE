"""Unit tests for MedicalChatService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.chat import ChatMessage
from app.services.medical_chat_service import (
    DEFAULT_DISCLAIMER,
    MedicalChatService,
)


def test_build_gemini_contents_empty_history():
    service = MedicalChatService()
    contents = service._build_gemini_contents("What causes high blood pressure?")
    assert len(contents) == 1
    assert contents[0]["role"] == "user"
    assert contents[0]["parts"][0]["text"] == "What causes high blood pressure?"


def test_build_gemini_contents_with_history():
    service = MedicalChatService()
    history = [
        ChatMessage(role="user", content="I feel dizzy"),
        ChatMessage(role="assistant", content="Dizziness can stem from dehydration or inner ear issues."),
    ]
    contents = service._build_gemini_contents("What should I do?", history=history)
    assert len(contents) == 3
    assert contents[0]["role"] == "user"
    assert contents[0]["parts"][0]["text"] == "I feel dizzy"
    assert contents[1]["role"] == "model"
    assert "inner ear issues" in contents[1]["parts"][0]["text"]
    assert contents[2]["role"] == "user"
    assert contents[2]["parts"][0]["text"] == "What should I do?"


def test_fallback_refuses_non_health_query():
    service = MedicalChatService()
    service.api_key = ""  # Force fallback
    res = service._generate_fallback_response("Write python code for a binary search tree")
    assert "outside my expertise" in res.reply.lower()
    assert res.disclaimer == DEFAULT_DISCLAIMER


def test_fallback_answers_health_query_with_doctor_advisory():
    service = MedicalChatService()
    service.api_key = ""  # Force fallback
    res = service._generate_fallback_response("I have a high fever and headache")
    assert "consult a qualified physician" in res.reply.lower()
    assert "cannot provide a direct diagnosis" in res.reply.lower()
    assert res.disclaimer == DEFAULT_DISCLAIMER


@pytest.mark.asyncio
async def test_chat_successful_gemini_response():
    service = MedicalChatService()
    service.api_key = "test-api-key"

    fake_response = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": (
                                "Hypertension or high blood pressure is typically influenced by genetics, "
                                "dietary sodium, stress, and vascular resistance. I cannot diagnose your "
                                "specific condition, so please consult a qualified physician for clinical evaluation."
                            )
                        }
                    ]
                }
            }
        ]
    }

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = fake_response
    mock_client.post.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client

    with patch("httpx.AsyncClient", return_value=mock_client):
        res = await service.chat("What causes high blood pressure?")

    assert "Hypertension" in res.reply
    assert "consult a qualified physician" in res.reply
    assert res.disclaimer == DEFAULT_DISCLAIMER


@pytest.mark.asyncio
async def test_chat_non_medical_refusal_via_gemini():
    service = MedicalChatService()
    service.api_key = "test-api-key"

    fake_response = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": (
                                "That is outside my expertise. As a medical health assistant, "
                                "I can only assist with health, wellness, and medical questions."
                            )
                        }
                    ]
                }
            }
        ]
    }

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = fake_response
    mock_client.post.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client

    with patch("httpx.AsyncClient", return_value=mock_client):
        res = await service.chat("Who won the 2022 World Cup?")

    assert "outside my expertise" in res.reply.lower()


@pytest.mark.asyncio
async def test_chat_graceful_fallback_on_network_error():
    service = MedicalChatService()
    service.api_key = "test-api-key"

    mock_client = AsyncMock()
    mock_client.post.side_effect = Exception("Connection timed out")
    mock_client.__aenter__.return_value = mock_client

    with patch("httpx.AsyncClient", return_value=mock_client):
        res = await service.chat("I have a persistent cough")

    # Should not raise exception, but return safe fallback
    assert "consult a qualified physician" in res.reply.lower()
    assert res.disclaimer is not None


def test_service_has_no_database_dependencies():
    service = MedicalChatService()
    # Confirm service has no database or session attributes
    assert not hasattr(service, "db")
    assert not hasattr(service, "session")
    assert not hasattr(service, "repository")
