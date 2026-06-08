"""add chat typing state

Revision ID: 20260325_000015
Revises: 20260324_000014
Create Date: 2026-03-25 00:00:15
"""

from alembic import op
import sqlalchemy as sa


revision = "20260325_000015"
down_revision = "20260324_000014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("chat_sessions", sa.Column("typing_actor_role", sa.String(length=20), nullable=True))
    op.add_column("chat_sessions", sa.Column("typing_updated_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("chat_sessions", "typing_updated_at")
    op.drop_column("chat_sessions", "typing_actor_role")
