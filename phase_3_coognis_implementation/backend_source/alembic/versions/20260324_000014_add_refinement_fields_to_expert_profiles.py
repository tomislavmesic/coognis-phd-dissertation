"""add refinement fields to expert profiles

Revision ID: 20260324_000014
Revises: 20260321_000013
Create Date: 2026-03-24 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260324_000014"
down_revision: str | None = "20260321_000013"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "expert_profiles",
        sa.Column("accumulated_interaction_text", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "expert_profiles",
        sa.Column("interaction_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "expert_profiles",
        sa.Column("last_inference_interaction_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "expert_profiles",
        sa.Column("last_inference_text_length", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "expert_profiles",
        sa.Column("last_inferred_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("expert_profiles", "last_inferred_at")
    op.drop_column("expert_profiles", "last_inference_text_length")
    op.drop_column("expert_profiles", "last_inference_interaction_count")
    op.drop_column("expert_profiles", "interaction_count")
    op.drop_column("expert_profiles", "accumulated_interaction_text")
