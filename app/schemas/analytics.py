"""Pydantic schemas for Healthcare Analytics and aggregated reporting."""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.dashboard import (
    AgeDistributionPoint,
    DashboardSummary,
    DiagnosisDistributionPoint,
    EncounterTrendPoint,
    SeasonalTrendPoint,
)


class AnalyticsFilterParams(BaseModel):
    date_from: Optional[date] = Field(default=None, alias="from_date")
    date_to: Optional[date] = Field(default=None, alias="to_date")
    range_preset: Optional[str] = Field(default=None, description="today, 7d, 30d, 90d, custom")


class AnalyticsOverviewResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    summary: DashboardSummary
    top_diagnoses: List[DiagnosisDistributionPoint]
    age_demographics: List[AgeDistributionPoint]
    time_window: str


class AnalyticsTrendsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    encounter_trends: List[EncounterTrendPoint]
    seasonal_trends: List[SeasonalTrendPoint]
    time_window: str
