"""Unit tests for PatientService."""

import pytest
from sqlalchemy.orm import Session

from app.core.constants import Gender, PatientStatus
from app.core.exceptions import ConflictError, NotFoundError
from app.models.user import User
from app.schemas.patient import PatientCreate, PatientUpdate
from app.services.patient_service import PatientService


def test_create_patient_auto_code(db_session: Session, clinician_user: User):
    service = PatientService(db_session)
    data = PatientCreate(age=42, gender=Gender.FEMALE)

    created = service.create_patient(data, actor=clinician_user)
    assert created.id is not None
    assert created.patientId.startswith("PT-")
    assert created.age == 42
    assert created.gender == Gender.FEMALE


def test_create_patient_duplicate_code(db_session: Session, clinician_user: User):
    service = PatientService(db_session)
    data1 = PatientCreate(patient_code="PT-0100", age=30, gender=Gender.MALE)
    service.create_patient(data1, actor=clinician_user)

    data2 = PatientCreate(patient_code="PT-0100", age=55, gender=Gender.FEMALE)
    with pytest.raises(ConflictError):
        service.create_patient(data2, actor=clinician_user)


def test_get_patient_not_found(db_session: Session):
    service = PatientService(db_session)
    with pytest.raises(NotFoundError):
        service.get_patient_by_id(999999)


def test_update_patient(db_session: Session, clinician_user: User):
    service = PatientService(db_session)
    created = service.create_patient(
        PatientCreate(age=25, gender=Gender.OTHER), actor=clinician_user
    )

    updated = service.update_patient(
        created.id,
        PatientUpdate(age=26, status=PatientStatus.INACTIVE),
        actor=clinician_user,
    )
    assert updated.age == 26
    assert updated.status == PatientStatus.INACTIVE
