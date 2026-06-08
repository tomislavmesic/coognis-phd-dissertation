"""Create expert core tables.

Revision ID: 20260319_000003
Revises: 20260319_000002
Create Date: 2026-03-19 00:00:03
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260319_000003"
down_revision: str | None = "20260319_000002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "experts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_experts_id", "experts", ["id"])

    op.create_table(
        "expert_domains",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("expert_id", sa.Integer(), nullable=False),
        sa.Column("domain_code", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["expert_id"], ["experts.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("expert_id", "domain_code", name="uq_expert_domains_expert_id_domain_code"),
    )
    op.create_index("ix_expert_domains_id", "expert_domains", ["id"])
    op.create_index("ix_expert_domains_expert_id", "expert_domains", ["expert_id"])
    op.create_index("ix_expert_domains_domain_code", "expert_domains", ["domain_code"])

    op.create_table(
        "knowledge_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("domain_code", sa.String(length=100), nullable=False),
        sa.Column("source_expert_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["source_expert_id"], ["experts.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_knowledge_items_id", "knowledge_items", ["id"])
    op.create_index("ix_knowledge_items_domain_code", "knowledge_items", ["domain_code"])
    op.create_index("ix_knowledge_items_source_expert_id", "knowledge_items", ["source_expert_id"])

    op.create_table(
        "expert_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("expert_id", sa.Integer(), nullable=False),
        sa.Column("manual_mbti", sa.String(length=4), nullable=True),
        sa.Column("inferred_mbti", sa.String(length=4), nullable=True),
        sa.Column("effective_mbti", sa.String(length=4), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["expert_id"], ["experts.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("expert_id"),
    )
    op.create_index("ix_expert_profiles_id", "expert_profiles", ["id"])
    op.create_index("ix_expert_profiles_expert_id", "expert_profiles", ["expert_id"])


def downgrade() -> None:
    op.drop_index("ix_expert_profiles_expert_id", table_name="expert_profiles")
    op.drop_index("ix_expert_profiles_id", table_name="expert_profiles")
    op.drop_table("expert_profiles")

    op.drop_index("ix_knowledge_items_source_expert_id", table_name="knowledge_items")
    op.drop_index("ix_knowledge_items_domain_code", table_name="knowledge_items")
    op.drop_index("ix_knowledge_items_id", table_name="knowledge_items")
    op.drop_table("knowledge_items")

    op.drop_index("ix_expert_domains_domain_code", table_name="expert_domains")
    op.drop_index("ix_expert_domains_expert_id", table_name="expert_domains")
    op.drop_index("ix_expert_domains_id", table_name="expert_domains")
    op.drop_table("expert_domains")

    op.drop_index("ix_experts_id", table_name="experts")
    op.drop_table("experts")
