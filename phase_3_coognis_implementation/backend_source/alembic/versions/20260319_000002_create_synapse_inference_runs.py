"""Create synapse inference runs table.

Revision ID: 20260319_000002
Revises: 20260319_000001
Create Date: 2026-03-19 00:00:02
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260319_000002"
down_revision: str | None = "20260319_000001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "synapse_inference_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("subject_type", sa.String(length=20), nullable=True),
        sa.Column("subject_id", sa.Integer(), nullable=True),
        sa.Column("mode", sa.String(length=50), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("mbti_type", sa.String(length=4), nullable=False),
        sa.Column("dimensions", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("model_version", sa.String(length=255), nullable=False),
        sa.Column("profile_status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_synapse_inference_runs_id", "synapse_inference_runs", ["id"])
    op.create_index(
        "ix_synapse_inference_runs_subject_id",
        "synapse_inference_runs",
        ["subject_id"],
    )
    op.create_index(
        "ix_synapse_inference_runs_subject_type",
        "synapse_inference_runs",
        ["subject_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_synapse_inference_runs_subject_type", table_name="synapse_inference_runs")
    op.drop_index("ix_synapse_inference_runs_subject_id", table_name="synapse_inference_runs")
    op.drop_index("ix_synapse_inference_runs_id", table_name="synapse_inference_runs")
    op.drop_table("synapse_inference_runs")
