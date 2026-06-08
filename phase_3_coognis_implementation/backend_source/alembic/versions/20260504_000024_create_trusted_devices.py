"""Create trusted devices table.

Revision ID: 20260504_000024
Revises: 20260430_000023
Create Date: 2026-05-04 00:00:24
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260504_000024"
down_revision: str | None = "20260430_000023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "trusted_devices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("user_agent_hash", sa.String(length=128), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_trusted_devices_id"), "trusted_devices", ["id"], unique=False)
    op.create_index(op.f("ix_trusted_devices_user_id"), "trusted_devices", ["user_id"], unique=False)
    op.create_index(op.f("ix_trusted_devices_token_hash"), "trusted_devices", ["token_hash"], unique=True)
    op.create_index(op.f("ix_trusted_devices_expires_at"), "trusted_devices", ["expires_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_trusted_devices_expires_at"), table_name="trusted_devices")
    op.drop_index(op.f("ix_trusted_devices_token_hash"), table_name="trusted_devices")
    op.drop_index(op.f("ix_trusted_devices_user_id"), table_name="trusted_devices")
    op.drop_index(op.f("ix_trusted_devices_id"), table_name="trusted_devices")
    op.drop_table("trusted_devices")
