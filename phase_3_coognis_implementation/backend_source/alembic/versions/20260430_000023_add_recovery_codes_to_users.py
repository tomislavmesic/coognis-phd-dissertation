"""Add recovery codes storage to users.

Revision ID: 20260430_000023
Revises: 20260430_000022
Create Date: 2026-04-30 00:00:23
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260430_000023"
down_revision: str | None = "20260430_000022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("recovery_codes_hashes", sa.String(length=4096), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "recovery_codes_hashes")
