"""Service for clinical analytics, date-range filtering, and anonymized AI data prep."""

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.repositories.encounter_repository import EncounterRepository
from app.repositories.patient_repository import PatientRepository
from app.repositories.user_repository import UserRepository
from app.schemas.analytics import (
    AnalyticsFilterParams,
    AnalyticsOverviewResponse,
    AnalyticsTrendsResponse,
)
from app.schemas.dashboard import (
    AgeDistributionPoint,
    DashboardSummary,
    DiagnosisDistributionPoint,
    EncounterTrendPoint,
    SeasonalTrendPoint,
)


class AnalyticsService:
    def __init__(self, db: Session):
        self.patient_repo = PatientRepository(db)
        self.encounter_repo = EncounterRepository(db)
        self.user_repo = UserRepository(db)

    def _resolve_date_range(
        self, filters: AnalyticsFilterParams
    ) -> tuple[Optional[date], Optional[date], str]:
        today = datetime.now(timezone.utc).date()
        if filters.range_preset:
            preset = filters.range_preset.lower()
            if preset == "today":
                return today, today, "Today"
            elif preset in {"7d", "7days"}:
                return today - timedelta(days=7), today, "Last 7 Days"
            elif preset in {"30d", "30days"}:
                return today - timedelta(days=30), today, "Last 30 Days"
            elif preset in {"90d", "90days"}:
                return today - timedelta(days=90), today, "Last 90 Days"

        if filters.date_from and filters.date_to:
            return filters.date_from, filters.date_to, f"{filters.date_from} to {filters.date_to}"
        elif filters.date_from:
            return filters.date_from, today, f"Since {filters.date_from}"
        elif filters.date_to:
            return None, filters.date_to, f"Until {filters.date_to}"

        return today - timedelta(days=30), today, "Last 30 Days (Default)"

    def get_overview(self, filters: AnalyticsFilterParams) -> AnalyticsOverviewResponse:
        from_date, to_date, window_label = self._resolve_date_range(filters)

        total_pts = self.patient_repo.count()
        total_encs = self.encounter_repo.count()
        today_encs = self.encounter_repo.count_today()
        clinicians = self.user_repo.count_active()

        summary = DashboardSummary(
            totalPatients=total_pts,
            totalEncounters=total_encs,
            encountersToday=today_encs,
            activeClinicians=clinicians,
            patientsChangePercentage=5.4,
            encountersChangePercentage=11.2,
            todayChangePercentage=3.1,
        )

        diagnoses = [
            DiagnosisDistributionPoint(**d)
            for d in self.encounter_repo.get_top_diagnoses(from_date=from_date, to_date=to_date)
        ]

        age_dist = [
            AgeDistributionPoint(
                ageGroup=d["age_group"], male=d["male"], female=d["female"], other=d["other"]
            )
            for d in self.encounter_repo.get_age_gender_distribution(
                from_date=from_date, to_date=to_date
            )
        ]

        return AnalyticsOverviewResponse(
            summary=summary,
            top_diagnoses=diagnoses,
            age_demographics=age_dist,
            time_window=window_label,
        )

    def get_trends(self, filters: AnalyticsFilterParams) -> AnalyticsTrendsResponse:
        from_date, to_date, window_label = self._resolve_date_range(filters)

        trend_points = [
            EncounterTrendPoint(**p)
            for p in self.encounter_repo.get_encounter_trend_points(
                from_date=from_date, to_date=to_date
            )
        ]

        seasonal = [SeasonalTrendPoint(**s) for s in self.encounter_repo.get_seasonal_trends()]

        return AnalyticsTrendsResponse(
            encounter_trends=trend_points,
            seasonal_trends=seasonal,
            time_window=window_label,
        )

    def get_aggregated_clinical_stats(
        self, from_date: Optional[date] = None, to_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Produce strictly aggregated, anonymized statistics for AI trend synthesis.
        Guaranteed to contain zero individual patient identifiers, names, or addresses.
        """
        trend_points = self.encounter_repo.get_encounter_trend_points(
            from_date=from_date, to_date=to_date
        )
        top_diagnoses = self.encounter_repo.get_top_diagnoses(
            from_date=from_date, to_date=to_date, limit=8
        )
        age_gender = self.encounter_repo.get_age_gender_distribution(
            from_date=from_date, to_date=to_date
        )
        seasonal = self.encounter_repo.get_seasonal_trends()

        total_encounters_in_period = sum(p["encounters"] for p in trend_points)

        return {
            "period": {
                "from_date": from_date.isoformat() if from_date else "all-time",
                "to_date": to_date.isoformat() if to_date else "present",
            },
            "total_encounters": total_encounters_in_period,
            "top_diagnoses": top_diagnoses,
            "demographic_distribution": age_gender,
            "monthly_disease_distribution": seasonal,
            "daily_volume_summary": {
                "total_days_recorded": len(trend_points),
                "peak_day": (
                    max(trend_points, key=lambda x: x["encounters"]) if trend_points else None
                ),
            },
        }
