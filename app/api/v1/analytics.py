"""Healthcare Analytics API Endpoints."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.constants import Permission
from app.dependencies.database import get_db
from app.dependencies.permissions import require_permission
from app.schemas.analytics import (
    AnalyticsFilterParams,
    AnalyticsOverviewResponse,
    AnalyticsTrendsResponse,
)
from app.schemas.common import StandardErrorResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/overview",
    response_model=AnalyticsOverviewResponse,
    summary="Get Analytics Overview",
    description="Comprehensive aggregated clinical overview with KPIs, top diagnoses, and demographic distributions.",
    dependencies=[Depends(require_permission(Permission.ANALYTICS_READ))],
    responses={
        401: {"model": StandardErrorResponse, "description": "Unauthorized"},
        403: {"model": StandardErrorResponse, "description": "Forbidden - requires analytics.read"},
    },
)
def get_analytics_overview(
    date_from: Optional[date] = Query(
        None, alias="from_date", description="Start date (YYYY-MM-DD)"
    ),
    date_to: Optional[date] = Query(None, alias="to_date", description="End date (YYYY-MM-DD)"),
    range_preset: Optional[str] = Query(
        None, alias="rangePreset", description="today, 7d, 30d, 90d, custom"
    ),
    db: Session = Depends(get_db),
) -> AnalyticsOverviewResponse:
    filters = AnalyticsFilterParams(
        from_date=date_from,
        to_date=date_to,
        range_preset=range_preset,
    )
    service = AnalyticsService(db)
    return service.get_overview(filters)


@router.get(
    "/trends",
    response_model=AnalyticsTrendsResponse,
    summary="Get Analytics Trends",
    description="Returns time-series encounter volumes alongside seasonal epidemiological breakdowns.",
    dependencies=[Depends(require_permission(Permission.ANALYTICS_READ))],
    responses={
        401: {"model": StandardErrorResponse, "description": "Unauthorized"},
        403: {"model": StandardErrorResponse, "description": "Forbidden - requires analytics.read"},
    },
)
def get_analytics_trends(
    date_from: Optional[date] = Query(None, alias="from_date"),
    date_to: Optional[date] = Query(None, alias="to_date"),
    range_preset: Optional[str] = Query(None, alias="rangePreset"),
    db: Session = Depends(get_db),
) -> AnalyticsTrendsResponse:
    filters = AnalyticsFilterParams(
        from_date=date_from,
        to_date=date_to,
        range_preset=range_preset,
    )
    service = AnalyticsService(db)
    return service.get_trends(filters)
