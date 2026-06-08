"""Add TOTP fields to users.

Revision ID: 20260430_000021
Revises: 20260326_000020
Create Date: 2026-04-30 00:00:21
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260430_000021"
down_revision: str | None = "20260326_000020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("two_factor_method", sa.String(length=32), nullable=True))
    op.add_column("users", sa.Column("totp_secret_encrypted", sa.String(length=1024), nullable=True))
    op.add_column("users", sa.Column("two_factor_confirmed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "two_factor_confirmed_at")
    op.drop_column("users", "totp_secret_encrypted")
    op.drop_column("users", "two_factor_method")
