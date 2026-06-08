"""Add status to knowledge items.

Revision ID: 20260319_000004
Revises: 20260319_000003
Create Date: 2026-03-19 00:00:04
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260319_000004"
down_revision: str | None = "20260319_000003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "knowledge_items",
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
    )
    op.create_index("ix_knowledge_items_status", "knowledge_items", ["status"])
    op.alter_column("knowledge_items", "status", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_knowledge_items_status", table_name="knowledge_items")
    op.drop_column("knowledge_items", "status")
