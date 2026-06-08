"""add chat unread tracking

Revision ID: 20260325_000017
Revises: 20260325_000016
Create Date: 2026-03-25 00:00:17
"""

from alembic import op
import sqlalchemy as sa


revision = "20260325_000017"
down_revision = "20260325_000016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("chat_sessions", sa.Column("user_last_seen_message_id", sa.Integer(), nullable=True))
    op.add_column("chat_sessions", sa.Column("expert_last_seen_message_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("chat_sessions", "expert_last_seen_message_id")
    op.drop_column("chat_sessions", "user_last_seen_message_id")
