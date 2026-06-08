"""Add feedback entries.

Revision ID: 20260319_000009
Revises: 20260319_000008
Create Date: 2026-03-19 00:00:09
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260319_000009"
down_revision: str | None = "20260319_000008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "feedback_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("feedback_type", sa.String(length=20), nullable=False),
        sa.Column("clarity", sa.Integer(), nullable=False),
        sa.Column("usefulness", sa.Integer(), nullable=False),
        sa.Column("personalization_fit", sa.Integer(), nullable=False),
        sa.Column("communication_quality", sa.Integer(), nullable=False),
        sa.Column("satisfaction", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_feedback_entries_id", "feedback_entries", ["id"])
    op.create_index("ix_feedback_entries_session_id", "feedback_entries", ["session_id"])
    op.create_index("ix_feedback_entries_feedback_type", "feedback_entries", ["feedback_type"])


def downgrade() -> None:
    op.drop_index("ix_feedback_entries_feedback_type", table_name="feedback_entries")
    op.drop_index("ix_feedback_entries_session_id", table_name="feedback_entries")
    op.drop_index("ix_feedback_entries_id", table_name="feedback_entries")
    op.drop_table("feedback_entries")
