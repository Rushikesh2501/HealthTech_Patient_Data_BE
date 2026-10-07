"""Pydantic schemas for Gemini AI Trend Analysis."""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AITrendAnalysisRequest(BaseModel):
    question: str = Field(
        min_length=5, max_length=500, description="Analytical query regarding clinical trends"
    )
    from_date: Optional[date] = Field(
        default=None, description="Start date for trend aggregation (inclusive)"
    )
    to_date: Optional[date] = Field(
        default=None, description="End date for trend aggregation (inclusive)"
    )


class AITrendAnalysisResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    summary: str
    observations: List[str]
    limitations: List[str]
    data_points_analyzed: int = 0
    generated_at: datetime
