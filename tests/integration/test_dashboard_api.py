"""Integration tests for Dashboard visualization and summary metrics."""

from fastapi.testclient import TestClient


def test_dashboard_summary(client: TestClient, clinician_token: str):
    response = client.get(
        "/api/v1/dashboard/summary",
        headers={"Authorization": f"Bearer {clinician_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "totalPatients" in data
    assert "totalEncounters" in data
    assert "encountersToday" in data
    assert "activeClinicians" in data


def test_dashboard_trends(client: TestClient, clinician_token: str):
    response = client.get(
        "/api/v1/dashboard/trends",
        headers={"Authorization": f"Bearer {clinician_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_dashboard_diagnoses(client: TestClient, clinician_token: str):
    response = client.get(
        "/api/v1/dashboard/diagnoses",
        headers={"Authorization": f"Bearer {clinician_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_dashboard_age_distribution(client: TestClient, clinician_token: str):
    response = client.get(
        "/api/v1/dashboard/age-distribution",
        headers={"Authorization": f"Bearer {clinician_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
