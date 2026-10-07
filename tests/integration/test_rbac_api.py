"""Integration tests proving backend RBAC enforcement across roles.
Verifies that the backend enforces authorization regardless of client requests.
"""

from fastapi.testclient import TestClient

from app.models.patient import Patient


def test_nurse_cannot_delete_patient(client: TestClient, nurse_token: str, sample_patient: Patient):
    response = client.delete(
        f"/api/v1/patients/{sample_patient.id}",
        headers={"Authorization": f"Bearer {nurse_token}"},
    )
    assert response.status_code == 403
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "FORBIDDEN_PERMISSION"


def test_clinician_cannot_delete_patient(
    client: TestClient, clinician_token: str, sample_patient: Patient
):
    response = client.delete(
        f"/api/v1/patients/{sample_patient.id}",
        headers={"Authorization": f"Bearer {clinician_token}"},
    )
    assert response.status_code == 403
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "FORBIDDEN_PERMISSION"


def test_nurse_cannot_access_audit_logs(client: TestClient, nurse_token: str):
    response = client.get(
        "/api/v1/audit-logs",
        headers={"Authorization": f"Bearer {nurse_token}"},
    )
    assert response.status_code == 403


def test_admin_can_access_audit_logs(client: TestClient, admin_token: str):
    response = client.get(
        "/api/v1/audit-logs",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200


def test_nurse_cannot_use_ai_analytics(client: TestClient, nurse_token: str):
    response = client.post(
        "/api/v1/ai/trends",
        json={"question": "Analyze spikes in fever cases"},
        headers={"Authorization": f"Bearer {nurse_token}"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN_PERMISSION"


def test_clinician_can_use_ai_analytics(client: TestClient, clinician_token: str):
    response = client.post(
        "/api/v1/ai/trends",
        json={"question": "Analyze spikes in fever cases"},
        headers={"Authorization": f"Bearer {clinician_token}"},
    )
    # Allowed by RBAC (200 OK with synthesized analysis)
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "observations" in data
    assert "limitations" in data


def test_unauthenticated_requests_fail_401(client: TestClient):
    response = client.get("/api/v1/patients")
    assert response.status_code == 401
    assert response.json()["success"] is False
