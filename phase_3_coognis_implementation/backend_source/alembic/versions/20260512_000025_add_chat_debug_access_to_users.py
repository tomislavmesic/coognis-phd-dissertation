"""Add per-user chat debug panel access flag.

Revision ID: 20260512_000025
Revises: 20260504_000024
Create Date: 2026-05-12 00:00:25
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260512_000025"
down_revision: str | None = "20260504_000024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("can_access_chat_debug_panels", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("users", "can_access_chat_debug_panels", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "can_access_chat_debug_panels")
