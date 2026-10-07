"""Dashboard Metrics and Aggregations API Endpoints."""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.constants import Permission
from app.dependencies.database import get_db
from app.dependencies.permissions import require_permission
from app.schemas.common import StandardErrorResponse
from app.schemas.dashboard import (
    AgeDistributionPoint,
    DashboardSummary,
    DiagnosisDistributionPoint,
    EncounterTrendPoint,
)
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/summary",
    response_model=DashboardSummary,
    summary="Get Dashboard Summary Metrics",
    description="Returns aggregate counts: total patients, total encounters, visits today, and active staff.",
    dependencies=[Depends(require_permission(Permission.ANALYTICS_READ))],
    responses={
        401: {"model": StandardErrorResponse, "description": "Unauthorized"},
        403: {"model": StandardErrorResponse, "description": "Forbidden - requires analytics.read"},
    },
)
def get_dashboard_summary(
    db: Session = Depends(get_db),
) -> DashboardSummary:
    service = DashboardService(db)
    return service.get_summary()


@router.get(
    "/trends",
    response_model=List[EncounterTrendPoint],
    summary="Get Encounter Volume Trends",
    description="Time-series count of patient encounters and follow-ups grouped by date.",
    dependencies=[Depends(require_permission(Permission.ANALYTICS_READ))],
    responses={
        401: {"model": StandardErrorResponse, "description": "Unauthorized"},
        403: {"model": StandardErrorResponse, "description": "Forbidden"},
    },
)
def get_encounter_trends(
    from_date: Optional[date] = Query(
        None, alias="fromDate", description="Start date for trend data"
    ),
    to_date: Optional[date] = Query(None, alias="toDate", description="End date for trend data"),
    db: Session = Depends(get_db),
) -> List[EncounterTrendPoint]:
    service = DashboardService(db)
    return service.get_trends(from_date=from_date, to_date=to_date)


@router.get(
    "/diagnoses",
    response_model=List[DiagnosisDistributionPoint],
    summary="Get Diagnosis Breakdown",
    description="Frequency distribution and percentages of leading diagnoses in the selected window.",
    dependencies=[Depends(require_permission(Permission.ANALYTICS_READ))],
    responses={
        401: {"model": StandardErrorResponse, "description": "Unauthorized"},
        403: {"model": StandardErrorResponse, "description": "Forbidden"},
    },
)
def get_diagnoses_breakdown(
    from_date: Optional[date] = Query(None, alias="fromDate"),
    to_date: Optional[date] = Query(None, alias="toDate"),
    db: Session = Depends(get_db),
) -> List[DiagnosisDistributionPoint]:
    service = DashboardService(db)
    return service.get_diagnoses(from_date=from_date, to_date=to_date)


@router.get(
    "/age-distribution",
    response_model=List[AgeDistributionPoint],
    summary="Get Age and Gender Demographics",
    description="Aggregated count of patients across standard clinical age brackets and gender classifications.",
    dependencies=[Depends(require_permission(Permission.ANALYTICS_READ))],
    responses={
        401: {"model": StandardErrorResponse, "description": "Unauthorized"},
        403: {"model": StandardErrorResponse, "description": "Forbidden"},
    },
)
def get_age_distribution(
    from_date: Optional[date] = Query(None, alias="fromDate"),
    to_date: Optional[date] = Query(None, alias="toDate"),
    db: Session = Depends(get_db),
) -> List[AgeDistributionPoint]:
    service = DashboardService(db)
    return service.get_age_distribution(from_date=from_date, to_date=to_date)
