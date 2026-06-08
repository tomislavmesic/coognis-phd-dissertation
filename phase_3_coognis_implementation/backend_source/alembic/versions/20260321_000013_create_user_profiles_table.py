"""create user profiles table

Revision ID: 20260321_000013
Revises: 20260320_000012
Create Date: 2026-03-21 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260321_000013"
down_revision: str | None = "20260320_000012"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_profiles",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("manual_mbti", sa.String(length=4), nullable=True),
        sa.Column("inferred_mbti", sa.String(length=4), nullable=True),
        sa.Column("effective_mbti", sa.String(length=4), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("accumulated_chat_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("interaction_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_inference_interaction_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_inference_text_length", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_inferred_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_user_profiles_id"), "user_profiles", ["id"], unique=False)
    op.create_index(op.f("ix_user_profiles_user_id"), "user_profiles", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_profiles_user_id"), table_name="user_profiles")
    op.drop_index(op.f("ix_user_profiles_id"), table_name="user_profiles")
    op.drop_table("user_profiles")
