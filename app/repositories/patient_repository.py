"""Repository for Anonymized Patient database operations."""

from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.encounter import Encounter
from app.models.patient import Patient
from app.schemas.patient import PatientFilterParams


class PatientRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, patient_id: int) -> Optional[Patient]:
        return self.db.get(Patient, patient_id)

    def get_by_code(self, patient_code: str) -> Optional[Patient]:
        stmt = select(Patient).where(Patient.patient_code == patient_code)
        return self.db.scalars(stmt).first()

    def get_all(
        self, filters: PatientFilterParams, offset: int = 0, limit: int = 20
    ) -> Tuple[List[Patient], int]:
        stmt = select(Patient)

        if filters.search:
            search_pattern = f"%{filters.search.strip()}%"
            stmt = stmt.where(Patient.patient_code.ilike(search_pattern))

        if filters.gender:
            stmt = stmt.where(Patient.gender == filters.gender)

        if filters.status:
            stmt = stmt.where(Patient.status == filters.status)

        if filters.age_min is not None:
            stmt = stmt.where(Patient.age >= filters.age_min)

        if filters.age_max is not None:
            stmt = stmt.where(Patient.age <= filters.age_max)

        if filters.registration_date_from is not None:
            stmt = stmt.where(Patient.registration_date >= filters.registration_date_from)

        if filters.registration_date_to is not None:
            stmt = stmt.where(Patient.registration_date <= filters.registration_date_to)

        # Count total matching records efficiently
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt) or 0

        # Query paginated records ordered by id descending (most recent first)
        paginated_stmt = stmt.order_by(Patient.id.desc()).offset(offset).limit(limit)
        patients = list(self.db.scalars(paginated_stmt).all())

        return patients, total

    def get_encounter_stats(
        self, patient_ids: List[int]
    ) -> Dict[int, Tuple[int, Optional[datetime]]]:
        """Bulk query encounter count and last encounter date for a batch of patient IDs.
        Avoids N+1 query overhead.
        """
        if not patient_ids:
            return {}

        stmt = (
            select(
                Encounter.patient_id,
                func.count(Encounter.id).label("total_encounters"),
                func.max(Encounter.encounter_date).label("last_encounter_date"),
            )
            .where(Encounter.patient_id.in_(patient_ids))
            .group_by(Encounter.patient_id)
        )

        results = self.db.execute(stmt).all()
        stats: Dict[int, Tuple[int, Optional[datetime]]] = {}
        for row in results:
            stats[row.patient_id] = (row.total_encounters, row.last_encounter_date)
        return stats

    def create(self, patient: Patient) -> Patient:
        self.db.add(patient)
        self.db.commit()
        self.db.refresh(patient)
        return patient

    def update(self, patient: Patient) -> Patient:
        self.db.commit()
        self.db.refresh(patient)
        return patient

    def delete(self, patient: Patient) -> None:
        self.db.delete(patient)
        self.db.commit()

    def generate_next_patient_code(self) -> str:
        """Atomically generate the next sequential anonymized patient code (e.g. PT-0001)."""
        stmt = select(func.max(Patient.id))
        max_id = self.db.scalar(stmt) or 0
        next_id = max_id + 1
        return f"PT-{next_id:04d}"

    def count(self) -> int:
        stmt = select(func.count(Patient.id))
        return self.db.scalar(stmt) or 0
