"""SQLAlchemy Anonymized Patient model.
Contains strictly anonymized clinical identifiers and demographics.
"""

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Date, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import Gender, PatientStatus
from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.encounter import Encounter


class Patient(Base, TimestampMixin):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        comment="Anonymized ID format e.g. PT-0001",
    )
    name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str] = mapped_column(
        Enum(
            Gender, name="patient_gender_enum", values_callable=lambda obj: [e.value for e in obj]
        ),
        nullable=False,
    )
    registration_date: Mapped[date] = mapped_column(
        Date,
        default=lambda: datetime.now(timezone.utc).date(),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        Enum(
            PatientStatus,
            name="patient_status_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        default=PatientStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    # Relationships
    encounters: Mapped[List["Encounter"]] = relationship(
        "Encounter",
        back_populates="patient",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Patient id={self.id} code={self.patient_code}>"
