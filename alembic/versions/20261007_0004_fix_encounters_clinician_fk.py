"""Fix encounters clinician_id nullable and fk ondelete set null.

Revision ID: 20261007_0004
Revises: 20261007_0003
Create Date: 2026-10-07 23:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261007_0004"
down_revision: Union[str, None] = "20261007_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("encounters", "clinician_id", nullable=True)
    op.drop_constraint("fk_encounters_clinician", "encounters", type_="foreignkey")
    op.create_foreign_key(
        "fk_encounters_clinician",
        "encounters",
        "users",
        ["clinician_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_encounters_clinician", "encounters", type_="foreignkey")
    op.create_foreign_key(
        "fk_encounters_clinician",
        "encounters",
        "users",
        ["clinician_id"],
        ["id"],
    )
    op.alter_column("encounters", "clinician_id", nullable=False)
