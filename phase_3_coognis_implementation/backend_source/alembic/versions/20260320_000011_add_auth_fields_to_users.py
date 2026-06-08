"""Add auth and privacy fields to users.

Revision ID: 20260320_000011
Revises: 20260319_000010
Create Date: 2026-03-20 00:00:11
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260320_000011"
down_revision: str | None = "20260319_000010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("first_name", sa.String(length=255), nullable=False, server_default=""))
    op.add_column("users", sa.Column("last_name", sa.String(length=255), nullable=False, server_default=""))
    op.add_column("users", sa.Column("password_hash", sa.String(length=512), nullable=True))
    op.add_column(
        "users",
        sa.Column("registration_status", sa.String(length=50), nullable=False, server_default="approved"),
    )
    op.add_column(
        "users",
        sa.Column("two_factor_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "users",
        sa.Column("ai_profiling_consent", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "users",
        sa.Column("gdpr_consent", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "users",
        sa.Column("profiling_opt_out_requested", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "users",
        sa.Column("account_deletion_requested", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "users",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.execute("UPDATE users SET first_name = name WHERE first_name = ''")


def downgrade() -> None:
    op.drop_column("users", "updated_at")
    op.drop_column("users", "account_deletion_requested")
    op.drop_column("users", "profiling_opt_out_requested")
    op.drop_column("users", "gdpr_consent")
    op.drop_column("users", "ai_profiling_consent")
    op.drop_column("users", "two_factor_enabled")
    op.drop_column("users", "registration_status")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
