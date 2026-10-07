"""Pydantic schemas for Dashboard metrics and data visualizer graphs."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DashboardSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total_patients: int = Field(alias="totalPatients")
    total_encounters: int = Field(alias="totalEncounters")
    encounters_today: int = Field(alias="encountersToday")
    active_clinicians: int = Field(alias="activeClinicians")
    patients_change_percentage: Optional[float] = Field(
        default=0.0, alias="patientsChangePercentage"
    )
    encounters_change_percentage: Optional[float] = Field(
        default=0.0, alias="encountersChangePercentage"
    )
    today_change_percentage: Optional[float] = Field(default=0.0, alias="todayChangePercentage")


class EncounterTrendPoint(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    date: str
    encounters: int
    follow_ups: int = Field(default=0, alias="followUps")


class DiagnosisDistributionPoint(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    count: int
    percentage: float
    color: Optional[str] = None


class AgeDistributionPoint(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    age_group: str = Field(alias="ageGroup")
    male: int = 0
    female: int = 0
    other: int = 0


class SeasonalTrendPoint(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    month: str
    viral_respiratory: int = Field(default=0, alias="viralRespiratory")
    diabetes_related: int = Field(default=0, alias="diabetesRelated")
    vector_borne: int = Field(default=0, alias="vectorBorne")
    gastrointestinal: int = 0
