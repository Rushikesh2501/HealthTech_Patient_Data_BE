"""Pydantic schemas for Patient Encounters."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.constants import EncounterStatus


class EncounterBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    symptoms: str = Field(min_length=2, max_length=2000)
    diagnosis: str = Field(min_length=2, max_length=255)
    treatment: str = Field(min_length=2, max_length=2000)
    temperature: Optional[str] = Field(default=None, max_length=50)
    blood_pressure: Optional[str] = Field(default=None, alias="bloodPressure", max_length=50)
    status: EncounterStatus = EncounterStatus.COMPLETED
    notes: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("blood_pressure")
    @classmethod
    def validate_blood_pressure(cls, v: Optional[str]) -> Optional[str]:
        if v:
            cleaned = v.strip()
            return cleaned
        return v


class EncounterCreate(EncounterBase):
    model_config = ConfigDict(populate_by_name=True)

    patient_id: int = Field(alias="patientId", description="Internal ID of the patient")
    clinician_id: Optional[int] = Field(default=None, alias="clinicianId")
    encounter_code: Optional[str] = Field(default=None, alias="encounterId")
    encounter_date: Optional[datetime] = Field(default=None, alias="encounterDate")


class EncounterUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    symptoms: Optional[str] = Field(default=None, min_length=2, max_length=2000)
    diagnosis: Optional[str] = Field(default=None, min_length=2, max_length=255)
    treatment: Optional[str] = Field(default=None, min_length=2, max_length=2000)
    temperature: Optional[str] = None
    blood_pressure: Optional[str] = Field(default=None, alias="bloodPressure")
    status: Optional[EncounterStatus] = None
    notes: Optional[str] = None
    encounter_date: Optional[datetime] = Field(default=None, alias="encounterDate")


class EncounterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    encounter_code: str = Field(alias="encounterId")
    patient_id: int = Field(alias="patientId")
    patient_display_code: Optional[str] = Field(default=None, alias="patientDisplayId")
    clinician_id: Optional[int] = Field(default=None, alias="clinicianId")
    clinician_name: Optional[str] = Field(default=None, alias="clinician")
    encounter_date: datetime = Field(alias="date")
    symptoms: str
    diagnosis: str
    treatment: str
    temperature: Optional[str] = None
    blood_pressure: Optional[str] = Field(default=None, alias="bloodPressure")
    status: EncounterStatus
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @property
    def encounterId(self) -> str:
        return self.encounter_code

    @property
    def patientId(self) -> int:
        return self.patient_id

    @property
    def date(self) -> datetime:
        return self.encounter_date


class EncounterFilterParams(BaseModel):
    search: Optional[str] = None
    patient_id: Optional[int] = None
    clinician_id: Optional[int] = None
    diagnosis: Optional[str] = None
    status: Optional[EncounterStatus] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
