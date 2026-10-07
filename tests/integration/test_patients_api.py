"""Integration tests for Anonymized Patients API endpoints."""

from fastapi.testclient import TestClient

from app.models.patient import Patient


def test_list_patients_paginated(client: TestClient, clinician_token: str, sample_patient: Patient):
    response = client.get(
        "/api/v1/patients?page=1&pageSize=10",
        headers={"Authorization": f"Bearer {clinician_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "pagination" in data
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["total"] >= 1


def test_create_patient(client: TestClient, clinician_token: str):
    payload = {
        "age": 28,
        "gender": "Female",
        "status": "active",
    }
    response = client.post(
        "/api/v1/patients",
        json=payload,
        headers={"Authorization": f"Bearer {clinician_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["patientId"].startswith("PT-")
    assert data["age"] == 28
    assert data["gender"] == "Female"


def test_get_patient_by_id(client: TestClient, clinician_token: str, sample_patient: Patient):
    response = client.get(
        f"/api/v1/patients/{sample_patient.id}",
        headers={"Authorization": f"Bearer {clinician_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["patientId"] == sample_patient.patient_code


def test_update_patient(client: TestClient, clinician_token: str, sample_patient: Patient):
    response = client.patch(
        f"/api/v1/patients/{sample_patient.id}",
        json={"age": 36, "status": "inactive"},
        headers={"Authorization": f"Bearer {clinician_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["age"] == 36
    assert data["status"] == "inactive"


def test_delete_patient_admin(client: TestClient, admin_token: str, sample_patient: Patient):
    response = client.delete(
        f"/api/v1/patients/{sample_patient.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 204
