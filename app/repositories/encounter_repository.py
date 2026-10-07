"""Repository for Clinical Encounter database operations and PostgreSQL aggregations."""

from datetime import date, datetime, time, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import Date, case, cast, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.encounter import Encounter
from app.models.patient import Patient
from app.schemas.encounter import EncounterFilterParams


class EncounterRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, encounter_id: int) -> Optional[Encounter]:
        stmt = (
            select(Encounter)
            .options(joinedload(Encounter.patient), joinedload(Encounter.clinician))
            .where(Encounter.id == encounter_id)
        )
        return self.db.scalars(stmt).first()

    def get_by_code(self, encounter_code: str) -> Optional[Encounter]:
        stmt = (
            select(Encounter)
            .options(joinedload(Encounter.patient), joinedload(Encounter.clinician))
            .where(Encounter.encounter_code == encounter_code)
        )
        return self.db.scalars(stmt).first()

    def get_all(
        self, filters: EncounterFilterParams, offset: int = 0, limit: int = 20
    ) -> Tuple[List[Encounter], int]:
        stmt = (
            select(Encounter)
            .join(Patient, Encounter.patient_id == Patient.id)
            .options(joinedload(Encounter.patient), joinedload(Encounter.clinician))
        )

        if filters.search:
            search_pat = f"%{filters.search.strip()}%"
            stmt = stmt.where(
                or_(
                    Encounter.encounter_code.ilike(search_pat),
                    Encounter.diagnosis.ilike(search_pat),
                    Encounter.symptoms.ilike(search_pat),
                    Patient.patient_code.ilike(search_pat),
                )
            )

        if filters.patient_id is not None:
            stmt = stmt.where(Encounter.patient_id == filters.patient_id)

        if filters.clinician_id is not None:
            stmt = stmt.where(Encounter.clinician_id == filters.clinician_id)

        if filters.diagnosis:
            stmt = stmt.where(Encounter.diagnosis.ilike(f"%{filters.diagnosis.strip()}%"))

        if filters.status:
            stmt = stmt.where(Encounter.status == filters.status)

        if filters.date_from:
            stmt = stmt.where(Encounter.encounter_date >= filters.date_from)

        if filters.date_to:
            stmt = stmt.where(Encounter.encounter_date <= filters.date_to)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt) or 0

        paginated_stmt = stmt.order_by(Encounter.encounter_date.desc()).offset(offset).limit(limit)
        encounters = list(self.db.scalars(paginated_stmt).all())

        return encounters, total

    def create(self, encounter: Encounter) -> Encounter:
        self.db.add(encounter)
        self.db.commit()
        self.db.refresh(encounter)
        return encounter

    def update(self, encounter: Encounter) -> Encounter:
        self.db.commit()
        self.db.refresh(encounter)
        return encounter

    def delete(self, encounter: Encounter) -> None:
        self.db.delete(encounter)
        self.db.commit()

    def generate_next_encounter_code(self) -> str:
        stmt = select(func.max(Encounter.id))
        max_id = self.db.scalar(stmt) or 0
        next_id = max_id + 1
        return f"ENC-{next_id:04d}"

    def count(self) -> int:
        stmt = select(func.count(Encounter.id))
        return self.db.scalar(stmt) or 0

    def count_today(self) -> int:
        today_start = datetime.combine(datetime.now(timezone.utc).date(), time.min).replace(
            tzinfo=timezone.utc
        )
        stmt = select(func.count(Encounter.id)).where(Encounter.encounter_date >= today_start)
        return self.db.scalar(stmt) or 0

    # PostgreSQL aggregations for analytics
    def get_encounter_trend_points(
        self, from_date: Optional[date] = None, to_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """Aggregate encounter volume and follow-ups grouped by date."""
        date_col = cast(Encounter.encounter_date, Date)
        stmt = (
            select(
                date_col.label("day"),
                func.count(Encounter.id).label("encounters"),
                func.sum(case((Encounter.notes.ilike("%follow%"), 1), else_=0)).label("follow_ups"),
            )
            .group_by(date_col)
            .order_by(date_col.asc())
        )

        if from_date:
            stmt = stmt.where(date_col >= from_date)
        if to_date:
            stmt = stmt.where(date_col <= to_date)

        rows = self.db.execute(stmt).all()
        return [
            {
                "date": row.day.isoformat(),
                "encounters": int(row.encounters),
                "follow_ups": int(row.follow_ups or 0),
            }
            for row in rows
        ]

    def get_top_diagnoses(
        self, from_date: Optional[date] = None, to_date: Optional[date] = None, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Aggregate diagnosis frequency and percentages in PostgreSQL."""
        stmt = (
            select(
                Encounter.diagnosis,
                func.count(Encounter.id).label("count"),
            )
            .group_by(Encounter.diagnosis)
            .order_by(func.count(Encounter.id).desc())
            .limit(limit)
        )

        if from_date:
            stmt = stmt.where(cast(Encounter.encounter_date, Date) >= from_date)
        if to_date:
            stmt = stmt.where(cast(Encounter.encounter_date, Date) <= to_date)

        rows = self.db.execute(stmt).all()
        total_stmt = select(func.count(Encounter.id))
        if from_date:
            total_stmt = total_stmt.where(cast(Encounter.encounter_date, Date) >= from_date)
        if to_date:
            total_stmt = total_stmt.where(cast(Encounter.encounter_date, Date) <= to_date)
        total_count = self.db.scalar(total_stmt) or 1

        palette = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899"]
        diagnoses = []
        for idx, row in enumerate(rows):
            pct = round((row.count / total_count) * 100, 1)
            color = palette[idx % len(palette)]
            diagnoses.append(
                {
                    "name": row.diagnosis,
                    "count": row.count,
                    "percentage": pct,
                    "color": color,
                }
            )
        return diagnoses

    def get_age_gender_distribution(
        self, from_date: Optional[date] = None, to_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """Aggregate patient age brackets and gender counts via joined aggregation."""
        # Age brackets: 0-18, 19-35, 36-50, 51-65, 65+
        age_group_case = case(
            (Patient.age <= 18, "0-18"),
            (Patient.age <= 35, "19-35"),
            (Patient.age <= 50, "36-50"),
            (Patient.age <= 65, "51-65"),
            else_="65+",
        ).label("age_group")

        stmt = (
            select(
                age_group_case,
                func.sum(case((Patient.gender == "Male", 1), else_=0)).label("male"),
                func.sum(case((Patient.gender == "Female", 1), else_=0)).label("female"),
                func.sum(case((Patient.gender == "Other", 1), else_=0)).label("other"),
            )
            .select_from(Encounter)
            .join(Patient, Encounter.patient_id == Patient.id)
            .group_by(age_group_case)
        )

        if from_date:
            stmt = stmt.where(cast(Encounter.encounter_date, Date) >= from_date)
        if to_date:
            stmt = stmt.where(cast(Encounter.encounter_date, Date) <= to_date)

        rows = self.db.execute(stmt).all()
        # Sort predictably
        order = {"0-18": 0, "19-35": 1, "36-50": 2, "51-65": 3, "65+": 4}
        results = [
            {
                "age_group": row[0],
                "male": int(row[1] or 0),
                "female": int(row[2] or 0),
                "other": int(row[3] or 0),
            }
            for row in rows
        ]
        results.sort(key=lambda x: order.get(x["age_group"], 99))
        return results

    def get_seasonal_trends(self) -> List[Dict[str, Any]]:
        """Aggregate monthly breakdown for key rural healthcare disease categories."""
        month_names = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]

        # Check dialect: PostgreSQL uses to_char, SQLite uses strftime
        dialect_name = self.db.bind.dialect.name if self.db.bind else "postgresql"
        if dialect_name == "sqlite":
            month_str = func.strftime("%m", Encounter.encounter_date)
            stmt = (
                select(
                    month_str.label("month_num"),
                    func.sum(case((Encounter.diagnosis.ilike("%respiratory%"), 1), else_=0)).label(
                        "respiratory"
                    ),
                    func.sum(case((Encounter.diagnosis.ilike("%diabetes%"), 1), else_=0)).label(
                        "diabetes"
                    ),
                    func.sum(
                        case(
                            (
                                Encounter.diagnosis.ilike("%malaria%")
                                | Encounter.diagnosis.ilike("%dengue%"),
                                1,
                            ),
                            else_=0,
                        )
                    ).label("vector"),
                    func.sum(
                        case(
                            (
                                Encounter.diagnosis.ilike("%gastro%")
                                | Encounter.diagnosis.ilike("%diarrhea%"),
                                1,
                            ),
                            else_=0,
                        )
                    ).label("gastro"),
                )
                .group_by(month_str)
                .order_by(month_str.asc())
            )
            rows = self.db.execute(stmt).all()
            return [
                {
                    "month": (
                        month_names[int(row.month_num) - 1]
                        if row.month_num and int(row.month_num) <= 12
                        else "Jan"
                    ),
                    "viral_respiratory": int(row.respiratory or 0),
                    "diabetes_related": int(row.diabetes or 0),
                    "vector_borne": int(row.vector or 0),
                    "gastrointestinal": int(row.gastro or 0),
                }
                for row in rows
            ]
        else:
            month_col = func.to_char(Encounter.encounter_date, "Mon").label("month_name")
            month_num = func.extract("month", Encounter.encounter_date).label("month_num")

            stmt = (
                select(
                    month_col,
                    month_num,
                    func.sum(case((Encounter.diagnosis.ilike("%respiratory%"), 1), else_=0)).label(
                        "respiratory"
                    ),
                    func.sum(case((Encounter.diagnosis.ilike("%diabetes%"), 1), else_=0)).label(
                        "diabetes"
                    ),
                    func.sum(
                        case(
                            (
                                Encounter.diagnosis.ilike("%malaria%")
                                | Encounter.diagnosis.ilike("%dengue%"),
                                1,
                            ),
                            else_=0,
                        )
                    ).label("vector"),
                    func.sum(
                        case(
                            (
                                Encounter.diagnosis.ilike("%gastro%")
                                | Encounter.diagnosis.ilike("%diarrhea%"),
                                1,
                            ),
                            else_=0,
                        )
                    ).label("gastro"),
                )
                .group_by(month_col, month_num)
                .order_by(month_num.asc())
            )

            rows = self.db.execute(stmt).all()
            return [
                {
                    "month": row.month_name,
                    "viral_respiratory": int(row.respiratory or 0),
                    "diabetes_related": int(row.diabetes or 0),
                    "vector_borne": int(row.vector or 0),
                    "gastrointestinal": int(row.gastro or 0),
                }
                for row in rows
            ]
