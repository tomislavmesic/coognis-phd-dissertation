"""Create knowledge sources and source documents tables.

Revision ID: 20260319_000005
Revises: 20260319_000004
Create Date: 2026-03-19 00:00:05
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260319_000005"
down_revision: str | None = "20260319_000004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "knowledge_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("source_value", sa.String(length=2048), nullable=False),
        sa.Column("indexing_status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_knowledge_sources_id", "knowledge_sources", ["id"])
    op.create_index("ix_knowledge_sources_source_type", "knowledge_sources", ["source_type"])
    op.create_index("ix_knowledge_sources_indexing_status", "knowledge_sources", ["indexing_status"])

    op.create_table(
        "source_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("knowledge_source_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("url", sa.String(length=2048), nullable=True),
        sa.Column("indexing_status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["knowledge_source_id"], ["knowledge_sources.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_source_documents_id", "source_documents", ["id"])
    op.create_index("ix_source_documents_knowledge_source_id", "source_documents", ["knowledge_source_id"])
    op.create_index("ix_source_documents_indexing_status", "source_documents", ["indexing_status"])


def downgrade() -> None:
    op.drop_index("ix_source_documents_indexing_status", table_name="source_documents")
    op.drop_index("ix_source_documents_knowledge_source_id", table_name="source_documents")
    op.drop_index("ix_source_documents_id", table_name="source_documents")
    op.drop_table("source_documents")

    op.drop_index("ix_knowledge_sources_indexing_status", table_name="knowledge_sources")
    op.drop_index("ix_knowledge_sources_source_type", table_name="knowledge_sources")
    op.drop_index("ix_knowledge_sources_id", table_name="knowledge_sources")
    op.drop_table("knowledge_sources")
