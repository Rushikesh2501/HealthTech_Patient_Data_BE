"""Initial production schema: users, patients, encounters, audit_logs.

Revision ID: 20261007_0001
Revises:
Create Date: 2026-10-07 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "20261007_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "role",
            sa.Enum("superadmin", "admin", "clinician", "nurse", name="user_role_enum"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)

    # 2. Anonymized Patients table
    op.create_table(
        "patients",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "patient_code",
            sa.String(length=50),
            nullable=False,
            comment="Anonymized ID format e.g. PT-0001",
        ),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column(
            "gender",
            sa.Enum("Male", "Female", "Other", name="patient_gender_enum"),
            nullable=False,
        ),
        sa.Column("registration_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("active", "inactive", name="patient_status_enum"),
            nullable=False,
            server_default="active",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_patients_id"), "patients", ["id"], unique=False)
    op.create_index(op.f("ix_patients_patient_code"), "patients", ["patient_code"], unique=True)
    op.create_index(
        op.f("ix_patients_registration_date"), "patients", ["registration_date"], unique=False
    )
    op.create_index(op.f("ix_patients_status"), "patients", ["status"], unique=False)

    # 3. Clinical Encounters table
    op.create_table(
        "encounters",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "encounter_code",
            sa.String(length=50),
            nullable=False,
            comment="Unique encounter identifier e.g. ENC-0001",
        ),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("clinician_id", sa.Integer(), nullable=True),
        sa.Column("encounter_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("symptoms", sa.Text(), nullable=False),
        sa.Column("diagnosis", sa.String(length=255), nullable=False),
        sa.Column("treatment", sa.Text(), nullable=False),
        sa.Column("temperature", sa.String(length=50), nullable=True),
        sa.Column("blood_pressure", sa.String(length=50), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "scheduled",
                "completed",
                "active",
                "inactive",
                "cancelled",
                "pending",
                "failed",
                name="encounter_status_enum",
            ),
            nullable=False,
            server_default="completed",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["clinician_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_encounters_id"), "encounters", ["id"], unique=False)
    op.create_index(
        op.f("ix_encounters_encounter_code"), "encounters", ["encounter_code"], unique=True
    )
    op.create_index(op.f("ix_encounters_patient_id"), "encounters", ["patient_id"], unique=False)
    op.create_index(
        op.f("ix_encounters_clinician_id"), "encounters", ["clinician_id"], unique=False
    )
    op.create_index(
        op.f("ix_encounters_encounter_date"), "encounters", ["encounter_date"], unique=False
    )
    op.create_index(op.f("ix_encounters_diagnosis"), "encounters", ["diagnosis"], unique=False)
    op.create_index(op.f("ix_encounters_status"), "encounters", ["status"], unique=False)

    # 4. Audit Logs table
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column(
            "action",
            sa.Enum(
                "LOGIN",
                "LOGIN_FAILED",
                "LOGOUT",
                "PATIENT_CREATED",
                "PATIENT_UPDATED",
                "PATIENT_DELETED",
                "ENCOUNTER_CREATED",
                "ENCOUNTER_UPDATED",
                "ENCOUNTER_DELETED",
                "UNAUTHORIZED_ACCESS",
                "AI_ANALYTICS_REQUEST",
                name="audit_action_enum",
            ),
            nullable=False,
        ),
        sa.Column("entity_type", sa.String(length=50), nullable=True),
        sa.Column("entity_id", sa.String(length=50), nullable=True),
        sa.Column(
            "status",
            sa.Enum("SUCCESS", "FAILED", "DENIED", name="audit_status_enum"),
            nullable=False,
            server_default="SUCCESS",
        ),
        sa.Column("request_id", sa.String(length=100), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_id"), "audit_logs", ["id"], unique=False)
    op.create_index(op.f("ix_audit_logs_user_id"), "audit_logs", ["user_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_type"), "audit_logs", ["entity_type"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_id"), "audit_logs", ["entity_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_request_id"), "audit_logs", ["request_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_created_at"), "audit_logs", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("encounters")
    op.drop_table("patients")
    op.drop_table("users")

    # Drop Enums
    sa.Enum(name="audit_status_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="audit_action_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="encounter_status_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="patient_status_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="patient_gender_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="user_role_enum").drop(op.get_bind(), checkfirst=True)
