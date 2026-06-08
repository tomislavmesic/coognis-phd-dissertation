"""Add chat messages and session state fields.

Revision ID: 20260319_000007
Revises: 20260319_000006
Create Date: 2026-03-19 00:00:07
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260319_000007"
down_revision: str | None = "20260319_000006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "chat_sessions",
        sa.Column("mode", sa.String(length=20), nullable=False, server_default="system"),
    )
    op.add_column(
        "chat_sessions",
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
    )
    op.add_column(
        "chat_sessions",
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_chat_sessions_mode", "chat_sessions", ["mode"])
    op.create_index("ix_chat_sessions_status", "chat_sessions", ["status"])
    op.alter_column("chat_sessions", "mode", server_default=None)
    op.alter_column("chat_sessions", "status", server_default=None)

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_chat_messages_id", "chat_messages", ["id"])
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"])
    op.create_index("ix_chat_messages_mode", "chat_messages", ["mode"])


def downgrade() -> None:
    op.drop_index("ix_chat_messages_mode", table_name="chat_messages")
    op.drop_index("ix_chat_messages_session_id", table_name="chat_messages")
    op.drop_index("ix_chat_messages_id", table_name="chat_messages")
    op.drop_table("chat_messages")

    op.drop_index("ix_chat_sessions_status", table_name="chat_sessions")
    op.drop_index("ix_chat_sessions_mode", table_name="chat_sessions")
    op.drop_column("chat_sessions", "closed_at")
    op.drop_column("chat_sessions", "status")
    op.drop_column("chat_sessions", "mode")
