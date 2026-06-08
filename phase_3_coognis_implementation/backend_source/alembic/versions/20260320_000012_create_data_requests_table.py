"""create data requests table

Revision ID: 20260320_000012
Revises: 20260320_000011
Create Date: 2026-03-20 20:05:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260320_000012"
down_revision: str | None = "20260320_000011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "data_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("request_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_data_requests_user_id", "data_requests", ["user_id"], unique=False)
    op.create_index("ix_data_requests_request_type", "data_requests", ["request_type"], unique=False)
    op.create_index("ix_data_requests_status", "data_requests", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_data_requests_status", table_name="data_requests")
    op.drop_index("ix_data_requests_request_type", table_name="data_requests")
    op.drop_index("ix_data_requests_user_id", table_name="data_requests")
    op.drop_table("data_requests")
