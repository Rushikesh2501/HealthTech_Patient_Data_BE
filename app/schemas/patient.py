"""Pydantic schemas for Anonymized Patient records.
Strictly disallows personally identifiable information (PII).
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import Gender, PatientStatus


class PatientBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(default=None, max_length=150, description="Patient name")
    age: int = Field(ge=0, le=125, description="Patient age in years")
    gender: Gender
    status: PatientStatus = PatientStatus.ACTIVE


class PatientCreate(PatientBase):
    model_config = ConfigDict(populate_by_name=True)

    patient_code: Optional[str] = Field(
        default=None,
        alias="patientId",
        description="Optional manual code e.g. PT-0001; auto-generated if omitted",
    )
    registration_date: Optional[date] = Field(
        default=None,
        alias="registrationDate",
    )


class PatientUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = Field(default=None, max_length=150)
    age: Optional[int] = Field(default=None, ge=0, le=125)
    gender: Optional[Gender] = None
    status: Optional[PatientStatus] = None


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    patient_code: str = Field(alias="patientId")
    name: Optional[str] = None
    age: int
    gender: Gender
    registration_date: date = Field(alias="registrationDate")
    status: PatientStatus
    created_at: datetime
    updated_at: datetime

    # Summary fields calculated on retrieval
    total_encounters: int = Field(default=0, alias="totalEncounters")
    last_encounter_date: Optional[datetime] = Field(default=None, alias="lastEncounterDate")

    @property
    def patientId(self) -> str:
        return self.patient_code

    @property
    def registrationDate(self) -> date:
        return self.registration_date

    @property
    def totalEncounters(self) -> int:
        return self.total_encounters

    @property
    def lastEncounterDate(self) -> Optional[datetime]:
        return self.last_encounter_date


class PatientFilterParams(BaseModel):
    search: Optional[str] = None
    gender: Optional[Gender] = None
    age_min: Optional[int] = Field(default=None, ge=0)
    age_max: Optional[int] = Field(default=None, le=125)
    status: Optional[PatientStatus] = None
    registration_date_from: Optional[date] = None
    registration_date_to: Optional[date] = None
