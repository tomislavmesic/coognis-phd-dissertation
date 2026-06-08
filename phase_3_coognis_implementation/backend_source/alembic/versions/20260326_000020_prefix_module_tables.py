"""prefix module tables

Revision ID: 20260326_000020
Revises: 20260326_000019
Create Date: 2026-03-26 17:00:00
"""

from collections.abc import Sequence

from alembic import op


revision: str = "20260326_000020"
down_revision: str | None = "20260326_000019"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _rename_index(old_name: str, new_name: str) -> None:
    op.execute(f'ALTER INDEX IF EXISTS "{old_name}" RENAME TO "{new_name}"')


def _rename_constraint(table_name: str, old_name: str, new_name: str) -> None:
    op.execute(
        f'ALTER TABLE "{table_name}" RENAME CONSTRAINT "{old_name}" TO "{new_name}"'
    )


def upgrade() -> None:
    op.rename_table("experts", "uex_experts")
    op.rename_table("expert_domains", "uex_expert_domains")
    op.rename_table("expert_profiles", "uex_expert_profiles")
    op.rename_table("knowledge_items", "uex_knowledge_items")

    op.rename_table("knowledge_sources", "ulm_knowledge_sources")
    op.rename_table("source_documents", "ulm_source_documents")

    op.rename_table("chat_sessions", "mind_chat_sessions")
    op.rename_table("chat_messages", "mind_chat_messages")
    op.rename_table("expert_handoffs", "mind_expert_handoffs")
    op.rename_table("feedback_entries", "mind_feedback_entries")

    op.rename_table("user_profiles", "synapse_user_profiles")

    _rename_index("ix_experts_id", "ix_uex_experts_id")
    _rename_index("ix_expert_domains_id", "ix_uex_expert_domains_id")
    _rename_index("ix_expert_domains_expert_id", "ix_uex_expert_domains_expert_id")
    _rename_index("ix_expert_domains_domain_code", "ix_uex_expert_domains_domain_code")
    _rename_constraint(
        "uex_expert_domains",
        "uq_expert_domains_expert_id_domain_code",
        "uq_uex_expert_domains_expert_id_domain_code",
    )
    _rename_index("ix_expert_profiles_id", "ix_uex_expert_profiles_id")
    _rename_index("ix_expert_profiles_expert_id", "ix_uex_expert_profiles_expert_id")
    _rename_index("ix_knowledge_items_id", "ix_uex_knowledge_items_id")
    _rename_index("ix_knowledge_items_domain_code", "ix_uex_knowledge_items_domain_code")
    _rename_index("ix_knowledge_items_source_expert_id", "ix_uex_knowledge_items_source_expert_id")
    _rename_index("ix_knowledge_items_status", "ix_uex_knowledge_items_status")

    _rename_index("ix_knowledge_sources_id", "ix_ulm_knowledge_sources_id")
    _rename_index("ix_knowledge_sources_source_type", "ix_ulm_knowledge_sources_source_type")
    _rename_index("ix_knowledge_sources_indexing_status", "ix_ulm_knowledge_sources_indexing_status")
    _rename_index("ix_source_documents_id", "ix_ulm_source_documents_id")
    _rename_index("ix_source_documents_knowledge_source_id", "ix_ulm_source_documents_knowledge_source_id")
    _rename_index("ix_source_documents_indexing_status", "ix_ulm_source_documents_indexing_status")
    _rename_index("ix_source_documents_chunk_index", "ix_ulm_source_documents_chunk_index")

    _rename_index("ix_chat_sessions_id", "ix_mind_chat_sessions_id")
    _rename_index("ix_chat_sessions_user_id", "ix_mind_chat_sessions_user_id")
    _rename_index("ix_chat_sessions_mode", "ix_mind_chat_sessions_mode")
    _rename_index("ix_chat_sessions_status", "ix_mind_chat_sessions_status")
    _rename_index("ix_chat_sessions_assigned_expert_id", "ix_mind_chat_sessions_assigned_expert_id")
    _rename_constraint(
        "mind_chat_sessions",
        "fk_chat_sessions_assigned_expert_id_experts",
        "fk_mind_chat_sessions_assigned_expert_id_uex_experts",
    )
    _rename_index("ix_chat_messages_id", "ix_mind_chat_messages_id")
    _rename_index("ix_chat_messages_session_id", "ix_mind_chat_messages_session_id")
    _rename_index("ix_chat_messages_mode", "ix_mind_chat_messages_mode")
    _rename_index("ix_expert_handoffs_id", "ix_mind_expert_handoffs_id")
    _rename_index("ix_expert_handoffs_session_id", "ix_mind_expert_handoffs_session_id")
    _rename_index("ix_expert_handoffs_expert_id", "ix_mind_expert_handoffs_expert_id")
    _rename_index("ix_feedback_entries_id", "ix_mind_feedback_entries_id")
    _rename_index("ix_feedback_entries_session_id", "ix_mind_feedback_entries_session_id")
    _rename_index("ix_feedback_entries_feedback_type", "ix_mind_feedback_entries_feedback_type")

    _rename_index("ix_user_profiles_id", "ix_synapse_user_profiles_id")
    _rename_index("ix_user_profiles_user_id", "ix_synapse_user_profiles_user_id")


def downgrade() -> None:
    _rename_index("ix_synapse_user_profiles_user_id", "ix_user_profiles_user_id")
    _rename_index("ix_synapse_user_profiles_id", "ix_user_profiles_id")

    _rename_index("ix_mind_feedback_entries_feedback_type", "ix_feedback_entries_feedback_type")
    _rename_index("ix_mind_feedback_entries_session_id", "ix_feedback_entries_session_id")
    _rename_index("ix_mind_feedback_entries_id", "ix_feedback_entries_id")
    _rename_index("ix_mind_expert_handoffs_expert_id", "ix_expert_handoffs_expert_id")
    _rename_index("ix_mind_expert_handoffs_session_id", "ix_expert_handoffs_session_id")
    _rename_index("ix_mind_expert_handoffs_id", "ix_expert_handoffs_id")
    _rename_index("ix_mind_chat_messages_mode", "ix_chat_messages_mode")
    _rename_index("ix_mind_chat_messages_session_id", "ix_chat_messages_session_id")
    _rename_index("ix_mind_chat_messages_id", "ix_chat_messages_id")
    _rename_constraint(
        "mind_chat_sessions",
        "fk_mind_chat_sessions_assigned_expert_id_uex_experts",
        "fk_chat_sessions_assigned_expert_id_experts",
    )
    _rename_index("ix_mind_chat_sessions_assigned_expert_id", "ix_chat_sessions_assigned_expert_id")
    _rename_index("ix_mind_chat_sessions_status", "ix_chat_sessions_status")
    _rename_index("ix_mind_chat_sessions_mode", "ix_chat_sessions_mode")
    _rename_index("ix_mind_chat_sessions_user_id", "ix_chat_sessions_user_id")
    _rename_index("ix_mind_chat_sessions_id", "ix_chat_sessions_id")

    _rename_index("ix_ulm_source_documents_chunk_index", "ix_source_documents_chunk_index")
    _rename_index("ix_ulm_source_documents_indexing_status", "ix_source_documents_indexing_status")
    _rename_index("ix_ulm_source_documents_knowledge_source_id", "ix_source_documents_knowledge_source_id")
    _rename_index("ix_ulm_source_documents_id", "ix_source_documents_id")
    _rename_index("ix_ulm_knowledge_sources_indexing_status", "ix_knowledge_sources_indexing_status")
    _rename_index("ix_ulm_knowledge_sources_source_type", "ix_knowledge_sources_source_type")
    _rename_index("ix_ulm_knowledge_sources_id", "ix_knowledge_sources_id")

    _rename_index("ix_uex_knowledge_items_status", "ix_knowledge_items_status")
    _rename_index("ix_uex_knowledge_items_source_expert_id", "ix_knowledge_items_source_expert_id")
    _rename_index("ix_uex_knowledge_items_domain_code", "ix_knowledge_items_domain_code")
    _rename_index("ix_uex_knowledge_items_id", "ix_knowledge_items_id")
    _rename_index("ix_uex_expert_profiles_expert_id", "ix_expert_profiles_expert_id")
    _rename_index("ix_uex_expert_profiles_id", "ix_expert_profiles_id")
    _rename_constraint(
        "uex_expert_domains",
        "uq_uex_expert_domains_expert_id_domain_code",
        "uq_expert_domains_expert_id_domain_code",
    )
    _rename_index("ix_uex_expert_domains_domain_code", "ix_expert_domains_domain_code")
    _rename_index("ix_uex_expert_domains_expert_id", "ix_expert_domains_expert_id")
    _rename_index("ix_uex_expert_domains_id", "ix_expert_domains_id")
    _rename_index("ix_uex_experts_id", "ix_experts_id")

    op.rename_table("synapse_user_profiles", "user_profiles")

    op.rename_table("mind_feedback_entries", "feedback_entries")
    op.rename_table("mind_expert_handoffs", "expert_handoffs")
    op.rename_table("mind_chat_messages", "chat_messages")
    op.rename_table("mind_chat_sessions", "chat_sessions")

    op.rename_table("ulm_source_documents", "source_documents")
    op.rename_table("ulm_knowledge_sources", "knowledge_sources")

    op.rename_table("uex_knowledge_items", "knowledge_items")
    op.rename_table("uex_expert_profiles", "expert_profiles")
    op.rename_table("uex_expert_domains", "expert_domains")
    op.rename_table("uex_experts", "experts")
