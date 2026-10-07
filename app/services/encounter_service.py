"""Service for managing clinical encounters, vitals, diagnoses, and treatments."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.constants import AuditAction, AuditStatus
from app.core.exceptions import ConflictError, NotFoundError
from app.models.encounter import Encounter
from app.models.user import User
from app.repositories.encounter_repository import EncounterRepository
from app.repositories.patient_repository import PatientRepository
from app.schemas.common import PaginatedResponse, PaginationMeta, PaginationParams
from app.schemas.encounter import (
    EncounterCreate,
    EncounterFilterParams,
    EncounterResponse,
    EncounterUpdate,
)
from app.services.audit_service import AuditService


class EncounterService:
    def __init__(self, db: Session):
        self.db = db
        self.encounter_repo = EncounterRepository(db)
        self.patient_repo = PatientRepository(db)
        self.audit_service = AuditService(db)

    def _to_response(self, encounter: Encounter) -> EncounterResponse:
        return EncounterResponse(
            id=encounter.id,
            encounterId=encounter.encounter_code,
            patientId=encounter.patient_id,
            patientDisplayId=(
                encounter.patient.patient_code
                if encounter.patient
                else f"PT-{encounter.patient_id}"
            ),
            clinicianId=encounter.clinician_id,
            clinician=encounter.clinician.name if encounter.clinician else "Attending Clinician",
            date=encounter.encounter_date,
            symptoms=encounter.symptoms,
            diagnosis=encounter.diagnosis,
            treatment=encounter.treatment,
            temperature=encounter.temperature,
            bloodPressure=encounter.blood_pressure,
            status=encounter.status,  # type: ignore
            notes=encounter.notes,
            created_at=encounter.created_at,
            updated_at=encounter.updated_at,
        )

    def create_encounter(
        self,
        data: EncounterCreate,
        actor: Optional[User] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> EncounterResponse:
        # Validate that the patient actually exists
        patient = self.patient_repo.get_by_id(data.patient_id)
        if not patient:
            raise NotFoundError(
                f"Patient with ID {data.patient_id} does not exist",
                code="PATIENT_NOT_FOUND",
            )

        code = data.encounter_code
        if not code:
            code = self.encounter_repo.generate_next_encounter_code()

        existing = self.encounter_repo.get_by_code(code)
        if existing:
            raise ConflictError(
                f"Encounter code '{code}' already exists", code="DUPLICATE_ENCOUNTER_CODE"
            )

        clinician_id = data.clinician_id or (actor.id if actor else None)
        enc_date = data.encounter_date or datetime.now(timezone.utc)

        encounter = Encounter(
            encounter_code=code,
            patient_id=data.patient_id,
            clinician_id=clinician_id,
            encounter_date=enc_date,
            symptoms=data.symptoms,
            diagnosis=data.diagnosis,
            treatment=data.treatment,
            temperature=data.temperature,
            blood_pressure=data.blood_pressure,
            status=data.status.value,
            notes=data.notes,
        )
        created = self.encounter_repo.create(encounter)

        # Re-fetch with joined relations
        fresh = self.encounter_repo.get_by_id(created.id) or created

        self.audit_service.log(
            action=AuditAction.ENCOUNTER_CREATED,
            status=AuditStatus.SUCCESS,
            user_id=actor.id if actor else None,
            entity_type="ENCOUNTER",
            entity_id=str(created.id),
            request_id=request_id,
            ip_address=ip_address,
            details=f"Encounter {fresh.encounter_code} logged for patient {patient.patient_code}",
        )

        return self._to_response(fresh)

    def get_encounters(
        self, filters: EncounterFilterParams, pagination: PaginationParams
    ) -> PaginatedResponse[EncounterResponse]:
        offset = (pagination.page - 1) * pagination.page_size
        items, total = self.encounter_repo.get_all(
            filters, offset=offset, limit=pagination.page_size
        )

        total_pages = (total + pagination.page_size - 1) // pagination.page_size if total > 0 else 1

        return PaginatedResponse(
            data=[self._to_response(e) for e in items],
            pagination=PaginationMeta(
                page=pagination.page,
                pageSize=pagination.page_size,
                total=total,
                totalPages=total_pages,
            ),
        )

    def get_encounter_by_id(self, encounter_id: int) -> EncounterResponse:
        encounter = self.encounter_repo.get_by_id(encounter_id)
        if not encounter:
            raise NotFoundError(
                f"Encounter with ID {encounter_id} not found", code="ENCOUNTER_NOT_FOUND"
            )
        return self._to_response(encounter)

    def update_encounter(
        self,
        encounter_id: int,
        data: EncounterUpdate,
        actor: Optional[User] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> EncounterResponse:
        encounter = self.encounter_repo.get_by_id(encounter_id)
        if not encounter:
            raise NotFoundError(
                f"Encounter with ID {encounter_id} not found", code="ENCOUNTER_NOT_FOUND"
            )

        if data.symptoms is not None:
            encounter.symptoms = data.symptoms
        if data.diagnosis is not None:
            encounter.diagnosis = data.diagnosis
        if data.treatment is not None:
            encounter.treatment = data.treatment
        if data.temperature is not None:
            encounter.temperature = data.temperature
        if data.blood_pressure is not None:
            encounter.blood_pressure = data.blood_pressure
        if data.status is not None:
            encounter.status = data.status.value
        if data.notes is not None:
            encounter.notes = data.notes
        if data.encounter_date is not None:
            encounter.encounter_date = data.encounter_date

        updated = self.encounter_repo.update(encounter)
        fresh = self.encounter_repo.get_by_id(updated.id) or updated

        self.audit_service.log(
            action=AuditAction.ENCOUNTER_UPDATED,
            status=AuditStatus.SUCCESS,
            user_id=actor.id if actor else None,
            entity_type="ENCOUNTER",
            entity_id=str(fresh.id),
            request_id=request_id,
            ip_address=ip_address,
            details=f"Encounter {fresh.encounter_code} updated",
        )

        return self._to_response(fresh)

    def delete_encounter(
        self,
        encounter_id: int,
        actor: Optional[User] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> None:
        encounter = self.encounter_repo.get_by_id(encounter_id)
        if not encounter:
            raise NotFoundError(
                f"Encounter with ID {encounter_id} not found", code="ENCOUNTER_NOT_FOUND"
            )

        code = encounter.encounter_code
        self.encounter_repo.delete(encounter)

        self.audit_service.log(
            action=AuditAction.ENCOUNTER_DELETED,
            status=AuditStatus.SUCCESS,
            user_id=actor.id if actor else None,
            entity_type="ENCOUNTER",
            entity_id=str(encounter_id),
            request_id=request_id,
            ip_address=ip_address,
            details=f"Encounter {code} permanently removed",
        )
