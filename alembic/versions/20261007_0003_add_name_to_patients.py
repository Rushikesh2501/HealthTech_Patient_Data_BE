"""Add name column to patients table.

Revision ID: 20261007_0003
Revises: 20261007_0002
Create Date: 2026-10-07 14:05:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "20261007_0003"
down_revision: Union[str, None] = "20261007_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("patients", sa.Column("name", sa.String(length=150), nullable=True))


def downgrade() -> None:
    op.drop_column("patients", "name")
