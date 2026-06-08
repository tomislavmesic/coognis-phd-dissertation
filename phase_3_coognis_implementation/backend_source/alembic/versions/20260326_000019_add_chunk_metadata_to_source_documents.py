"""add chunk metadata to source documents

Revision ID: 20260326_000019
Revises: 20260326_000018
Create Date: 2026-03-26 16:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260326_000019"
down_revision: str | None = "20260326_000018"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "source_documents",
        sa.Column("chunk_index", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "source_documents",
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_index(
        op.f("ix_source_documents_chunk_index"),
        "source_documents",
        ["chunk_index"],
        unique=False,
    )
    op.alter_column("source_documents", "chunk_index", server_default=None)
    op.alter_column("source_documents", "chunk_count", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_source_documents_chunk_index"), table_name="source_documents")
    op.drop_column("source_documents", "chunk_count")
    op.drop_column("source_documents", "chunk_index")
