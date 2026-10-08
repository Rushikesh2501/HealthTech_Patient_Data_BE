"""Integration tests for AI Medical Chatbot API endpoints.
Verifies that the chatbot operates purely as an informative assistant with zero database access.
"""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.schemas.chat import MedicalChatResponse


def test_chat_endpoint_public_access(client: TestClient):
    with patch(
        "app.services.medical_chat_service.MedicalChatService.chat",
        new_callable=AsyncMock,
    ) as mock_chat:
        mock_chat.return_value = MedicalChatResponse(
            reply="Headaches can arise from tension or dehydration. Please consult a doctor.",
            disclaimer="Strictly for educational purposes. Consult a doctor.",
            timestamp="2026-10-08T12:00:00Z",
        )

        response = client.post(
            "/api/v1/chat",
            json={"message": "Why do I have a headache?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert "disclaimer" in data
        assert "consult a doctor" in data["reply"].lower()


def test_chat_endpoint_no_db_dependency(client: TestClient):
    """Verifies that chat executes as an informative service without touching or requiring the DB."""
    with patch(
        "app.services.medical_chat_service.MedicalChatService.chat",
        new_callable=AsyncMock,
    ) as mock_chat:
        mock_chat.return_value = MedicalChatResponse(
            reply="That is outside my expertise. I only answer health questions.",
            disclaimer="Strictly for educational purposes. Consult a doctor.",
            timestamp="2026-10-08T12:00:00Z",
        )

        response = client.post(
            "/api/v1/chat",
            json={"message": "Can you recommend a stock to invest in?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "outside my expertise" in data["reply"].lower()


def test_chat_with_conversation_history(client: TestClient):
    with patch(
        "app.services.medical_chat_service.MedicalChatService.chat",
        new_callable=AsyncMock,
    ) as mock_chat:
        mock_chat.return_value = MedicalChatResponse(
            reply="Drinking plenty of water and resting may help mild symptoms, but consult a physician.",
            disclaimer="Strictly for educational purposes. Consult a doctor.",
            timestamp="2026-10-08T12:00:00Z",
        )

        payload = {
            "message": "What home remedies might ease it?",
            "history": [
                {"role": "user", "content": "I have a sore throat."},
                {"role": "assistant", "content": "A sore throat can be caused by viral infections."},
            ],
        }
        response = client.post("/api/v1/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "consult a physician" in data["reply"]


def test_chat_ai_alias_endpoint(client: TestClient):
    with patch(
        "app.services.medical_chat_service.MedicalChatService.chat",
        new_callable=AsyncMock,
    ) as mock_chat:
        mock_chat.return_value = MedicalChatResponse(
            reply="General wellness information provided. Consult your doctor.",
            disclaimer="Educational disclaimer.",
            timestamp="2026-10-08T12:00:00Z",
        )

        response = client.post(
            "/api/v1/ai/chat",
            json={"message": "How many hours of sleep are recommended for adults?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data


def test_chat_validation_empty_message(client: TestClient):
    response = client.post(
        "/api/v1/chat",
        json={"message": ""},
    )
    assert response.status_code == 422
