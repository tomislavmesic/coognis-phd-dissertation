"""Create MIND sessions and logs tables.

Revision ID: 20260319_000006
Revises: 20260319_000005
Create Date: 2026-03-19 00:00:06
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260319_000006"
down_revision: str | None = "20260319_000005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_chat_sessions_id", "chat_sessions", ["id"])
    op.create_index("ix_chat_sessions_user_id", "chat_sessions", ["user_id"])

    op.create_table(
        "mind_chat_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("final_response", sa.Text(), nullable=False),
        sa.Column("modules_used", sa.JSON(), nullable=False),
        sa.Column("expert_suggestion", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_mind_chat_logs_id", "mind_chat_logs", ["id"])
    op.create_index("ix_mind_chat_logs_session_id", "mind_chat_logs", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_mind_chat_logs_session_id", table_name="mind_chat_logs")
    op.drop_index("ix_mind_chat_logs_id", table_name="mind_chat_logs")
    op.drop_table("mind_chat_logs")

    op.drop_index("ix_chat_sessions_user_id", table_name="chat_sessions")
    op.drop_index("ix_chat_sessions_id", table_name="chat_sessions")
    op.drop_table("chat_sessions")
