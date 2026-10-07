"""SQLAlchemy Clinical Encounter model."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import EncounterStatus
from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.patient import Patient
    from app.models.user import User


class Encounter(Base, TimestampMixin):
    __tablename__ = "encounters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    encounter_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        comment="Unique encounter identifier e.g. ENC-0001",
    )
    patient_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("patients.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    clinician_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    encounter_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    symptoms: Mapped[str] = mapped_column(Text, nullable=False)
    diagnosis: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    treatment: Mapped[str] = mapped_column(Text, nullable=False)
    temperature: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    blood_pressure: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(
            EncounterStatus,
            native_enum=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        default=EncounterStatus.COMPLETED,
        nullable=False,
        index=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", back_populates="encounters")
    clinician: Mapped[Optional["User"]] = relationship("User", back_populates="encounters")

    def __repr__(self) -> str:
        return f"<Encounter id={self.id} code={self.encounter_code} diag={self.diagnosis}>"
