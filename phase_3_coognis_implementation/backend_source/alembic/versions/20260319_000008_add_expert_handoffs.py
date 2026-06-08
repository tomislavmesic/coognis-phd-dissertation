"""Add expert handoffs and session expert assignment.

Revision ID: 20260319_000008
Revises: 20260319_000007
Create Date: 2026-03-19 00:00:08
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260319_000008"
down_revision: str | None = "20260319_000007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "chat_sessions",
        sa.Column("assigned_expert_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_chat_sessions_assigned_expert_id_experts",
        "chat_sessions",
        "experts",
        ["assigned_expert_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_chat_sessions_assigned_expert_id", "chat_sessions", ["assigned_expert_id"])

    op.create_table(
        "expert_handoffs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("expert_id", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("from_mode", sa.String(length=20), nullable=False),
        sa.Column("to_mode", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["expert_id"], ["experts.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_expert_handoffs_id", "expert_handoffs", ["id"])
    op.create_index("ix_expert_handoffs_session_id", "expert_handoffs", ["session_id"])
    op.create_index("ix_expert_handoffs_expert_id", "expert_handoffs", ["expert_id"])


def downgrade() -> None:
    op.drop_index("ix_expert_handoffs_expert_id", table_name="expert_handoffs")
    op.drop_index("ix_expert_handoffs_session_id", table_name="expert_handoffs")
    op.drop_index("ix_expert_handoffs_id", table_name="expert_handoffs")
    op.drop_table("expert_handoffs")

    op.drop_index("ix_chat_sessions_assigned_expert_id", table_name="chat_sessions")
    op.drop_constraint("fk_chat_sessions_assigned_expert_id_experts", "chat_sessions", type_="foreignkey")
    op.drop_column("chat_sessions", "assigned_expert_id")
