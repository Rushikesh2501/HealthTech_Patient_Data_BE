"""Add superadmin to user_role_enum.

Revision ID: 20261007_0002
Revises: 20261007_0001
Create Date: 2026-10-07 13:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "20261007_0002"
down_revision: Union[str, None] = "20261007_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Safely add 'superadmin' to PostgreSQL user_role_enum if not already present
    op.execute("ALTER TYPE user_role_enum ADD VALUE IF NOT EXISTS 'superadmin'")


def downgrade() -> None:
    # PostgreSQL does not support removing values from enums without recreating the type
    pass
