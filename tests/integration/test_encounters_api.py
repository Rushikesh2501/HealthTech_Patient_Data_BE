"""Integration tests for Clinical Encounters API endpoints."""

from fastapi.testclient import TestClient

from app.models.patient import Patient


def test_create_and_get_encounter(
    client: TestClient, clinician_token: str, sample_patient: Patient
):
    payload = {
        "patientId": sample_patient.id,
        "symptoms": "High fever, chills, persistent coughing",
        "diagnosis": "Viral Pneumonia",
        "treatment": "Supportive care, hydration, monitoring O2 saturation",
        "temperature": "101.5 °F",
        "bloodPressure": "118/76 mmHg",
        "status": "completed",
    }
    create_resp = client.post(
        "/api/v1/encounters",
        json=payload,
        headers={"Authorization": f"Bearer {clinician_token}"},
    )
    assert create_resp.status_code == 201
    enc_data = create_resp.json()
    assert enc_data["encounterId"].startswith("ENC-")
    assert enc_data["diagnosis"] == "Viral Pneumonia"

    get_resp = client.get(
        f"/api/v1/encounters/{enc_data['id']}",
        headers={"Authorization": f"Bearer {clinician_token}"},
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["encounterId"] == enc_data["encounterId"]


def test_list_encounters_filtering(
    client: TestClient, clinician_token: str, sample_patient: Patient
):
    # Create encounter first
    client.post(
        "/api/v1/encounters",
        json={
            "patientId": sample_patient.id,
            "symptoms": "Throat pain",
            "diagnosis": "Pharyngitis",
            "treatment": "Lozenges",
        },
        headers={"Authorization": f"Bearer {clinician_token}"},
    )

    response = client.get(
        "/api/v1/encounters?diagnosis=Pharyngitis",
        headers={"Authorization": f"Bearer {clinician_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1
