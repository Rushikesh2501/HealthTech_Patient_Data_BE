"""Unit tests for EncounterService."""

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.patient import Patient
from app.models.user import User
from app.schemas.encounter import EncounterCreate, EncounterUpdate
from app.services.encounter_service import EncounterService


def test_create_encounter_valid(db_session: Session, clinician_user: User, sample_patient: Patient):
    service = EncounterService(db_session)
    data = EncounterCreate(
        patientId=sample_patient.id,
        symptoms="Fever and severe cough",
        diagnosis="Acute Bronchitis",
        treatment="Rest, fluids, and bronchodilator",
        temperature="100.4 °F",
        bloodPressure="120/80 mmHg",
    )

    created = service.create_encounter(data, actor=clinician_user)
    assert created.id is not None
    assert created.encounterId.startswith("ENC-")
    assert created.patientId == sample_patient.id
    assert created.diagnosis == "Acute Bronchitis"


def test_create_encounter_invalid_patient(db_session: Session, clinician_user: User):
    service = EncounterService(db_session)
    data = EncounterCreate(
        patientId=999999,
        symptoms="Headache",
        diagnosis="Tension Headache",
        treatment="Hydration",
    )

    with pytest.raises(NotFoundError):
        service.create_encounter(data, actor=clinician_user)


def test_update_encounter(db_session: Session, clinician_user: User, sample_patient: Patient):
    service = EncounterService(db_session)
    created = service.create_encounter(
        EncounterCreate(
            patientId=sample_patient.id,
            symptoms="Mild rash",
            diagnosis="Contact Dermatitis",
            treatment="Topical hydrocortisone",
        ),
        actor=clinician_user,
    )

    updated = service.update_encounter(
        created.id,
        EncounterUpdate(diagnosis="Atopic Dermatitis", treatment="Emollient cream"),
        actor=clinician_user,
    )
    assert updated.diagnosis == "Atopic Dermatitis"
    assert updated.treatment == "Emollient cream"
