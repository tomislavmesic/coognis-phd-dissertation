"""add chat feedback tracking

Revision ID: 20260325_000016
Revises: 20260325_000015
Create Date: 2026-03-25 00:00:16
"""

from alembic import op
import sqlalchemy as sa


revision = "20260325_000016"
down_revision = "20260325_000015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("chat_sessions", sa.Column("closed_by_role", sa.String(length=20), nullable=True))
    op.add_column("chat_sessions", sa.Column("closed_by_name", sa.String(length=255), nullable=True))
    op.add_column(
        "feedback_entries",
        sa.Column("submitted_by_role", sa.String(length=20), nullable=False, server_default="user"),
    )
    op.alter_column("feedback_entries", "submitted_by_role", server_default=None)


def downgrade() -> None:
    op.drop_column("feedback_entries", "submitted_by_role")
    op.drop_column("chat_sessions", "closed_by_name")
    op.drop_column("chat_sessions", "closed_by_role")
