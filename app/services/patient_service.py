"""Service for anonymized patient management and HIPAA/GDPR-compliant record handling."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.constants import AuditAction, AuditStatus
from app.core.exceptions import ConflictError, NotFoundError
from app.models.patient import Patient
from app.models.user import User
from app.repositories.patient_repository import PatientRepository
from app.schemas.common import PaginatedResponse, PaginationMeta, PaginationParams
from app.schemas.patient import (
    PatientCreate,
    PatientFilterParams,
    PatientResponse,
    PatientUpdate,
)
from app.services.audit_service import AuditService


class PatientService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PatientRepository(db)
        self.audit_service = AuditService(db)

    def create_patient(
        self,
        data: PatientCreate,
        actor: Optional[User] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> PatientResponse:
        code = data.patient_code
        if not code:
            code = self.repo.generate_next_patient_code()

        existing = self.repo.get_by_code(code)
        if existing:
            raise ConflictError(
                f"Patient code '{code}' already exists", code="DUPLICATE_PATIENT_CODE"
            )

        reg_date = data.registration_date or datetime.now(timezone.utc).date()

        patient = Patient(
            patient_code=code,
            age=data.age,
            gender=data.gender.value,
            registration_date=reg_date,
            status=data.status.value,
        )
        created = self.repo.create(patient)

        # Audit log creation
        self.audit_service.log(
            action=AuditAction.PATIENT_CREATED,
            status=AuditStatus.SUCCESS,
            user_id=actor.id if actor else None,
            entity_type="PATIENT",
            entity_id=str(created.id),
            request_id=request_id,
            ip_address=ip_address,
            details=f"Anonymized patient created with code {created.patient_code}",
        )

        return PatientResponse(
            id=created.id,
            patientId=created.patient_code,
            age=created.age,
            gender=created.gender,  # type: ignore
            registrationDate=created.registration_date,
            status=created.status,  # type: ignore
            created_at=created.created_at,
            updated_at=created.updated_at,
            totalEncounters=0,
            lastEncounterDate=None,
        )

    def get_patients(
        self, filters: PatientFilterParams, pagination: PaginationParams
    ) -> PaginatedResponse[PatientResponse]:
        offset = (pagination.page - 1) * pagination.page_size
        patients, total = self.repo.get_all(filters, offset=offset, limit=pagination.page_size)

        # Bulk fetch encounter statistics for these patients to eliminate N+1 queries
        patient_ids = [p.id for p in patients]
        stats = self.repo.get_encounter_stats(patient_ids)

        data = []
        for p in patients:
            enc_count, last_date = stats.get(p.id, (0, None))
            data.append(
                PatientResponse(
                    id=p.id,
                    patientId=p.patient_code,
                    age=p.age,
                    gender=p.gender,  # type: ignore
                    registrationDate=p.registration_date,
                    status=p.status,  # type: ignore
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                    totalEncounters=enc_count,
                    lastEncounterDate=last_date,
                )
            )

        total_pages = (total + pagination.page_size - 1) // pagination.page_size if total > 0 else 1

        return PaginatedResponse(
            data=data,
            pagination=PaginationMeta(
                page=pagination.page,
                pageSize=pagination.page_size,
                total=total,
                totalPages=total_pages,
            ),
        )

    def get_patient_by_id(self, patient_id: int) -> PatientResponse:
        patient = self.repo.get_by_id(patient_id)
        if not patient:
            raise NotFoundError(f"Patient with ID {patient_id} not found", code="PATIENT_NOT_FOUND")

        stats = self.repo.get_encounter_stats([patient.id])
        enc_count, last_date = stats.get(patient.id, (0, None))

        return PatientResponse(
            id=patient.id,
            patientId=patient.patient_code,
            age=patient.age,
            gender=patient.gender,  # type: ignore
            registrationDate=patient.registration_date,
            status=patient.status,  # type: ignore
            created_at=patient.created_at,
            updated_at=patient.updated_at,
            totalEncounters=enc_count,
            lastEncounterDate=last_date,
        )

    def update_patient(
        self,
        patient_id: int,
        data: PatientUpdate,
        actor: Optional[User] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> PatientResponse:
        patient = self.repo.get_by_id(patient_id)
        if not patient:
            raise NotFoundError(f"Patient with ID {patient_id} not found", code="PATIENT_NOT_FOUND")

        if data.age is not None:
            patient.age = data.age
        if data.gender is not None:
            patient.gender = data.gender.value
        if data.status is not None:
            patient.status = data.status.value

        updated = self.repo.update(patient)

        self.audit_service.log(
            action=AuditAction.PATIENT_UPDATED,
            status=AuditStatus.SUCCESS,
            user_id=actor.id if actor else None,
            entity_type="PATIENT",
            entity_id=str(updated.id),
            request_id=request_id,
            ip_address=ip_address,
            details=f"Patient {updated.patient_code} demographics updated",
        )

        stats = self.repo.get_encounter_stats([updated.id])
        enc_count, last_date = stats.get(updated.id, (0, None))

        return PatientResponse(
            id=updated.id,
            patientId=updated.patient_code,
            age=updated.age,
            gender=updated.gender,  # type: ignore
            registrationDate=updated.registration_date,
            status=updated.status,  # type: ignore
            created_at=updated.created_at,
            updated_at=updated.updated_at,
            totalEncounters=enc_count,
            lastEncounterDate=last_date,
        )

    def delete_patient(
        self,
        patient_id: int,
        actor: Optional[User] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> None:
        patient = self.repo.get_by_id(patient_id)
        if not patient:
            raise NotFoundError(f"Patient with ID {patient_id} not found", code="PATIENT_NOT_FOUND")

        patient_code = patient.patient_code
        self.repo.delete(patient)

        self.audit_service.log(
            action=AuditAction.PATIENT_DELETED,
            status=AuditStatus.SUCCESS,
            user_id=actor.id if actor else None,
            entity_type="PATIENT",
            entity_id=str(patient_id),
            request_id=request_id,
            ip_address=ip_address,
            details=f"Patient record {patient_code} permanently deleted",
        )
