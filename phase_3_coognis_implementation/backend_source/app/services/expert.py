from __future__ import annotations

from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models import ChatMessage, ChatSession, Expert, ExpertDomain, FeedbackEntry, KnowledgeItem, User
from app.schemas.expert import (
    ExpertDashboardAssignedConversationResponse,
    ExpertDashboardFeedbackSummaryResponse,
    ExpertDashboardKnowledgeSummaryResponse,
    ExpertDashboardProfileSummaryResponse,
    ExpertDashboardSummaryResponse,
)


class ExpertServiceError(Exception):
    def __init__(self, *, status_code: int, code: str, message: str, details: Any = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


class ExpertService:
    def __init__(self, db: Session, session_data: dict[str, Any]) -> None:
        self.db = db
        self.session_data = session_data

    def get_dashboard_summary(self) -> ExpertDashboardSummaryResponse:
        user = self._get_authenticated_expert_user()
        expert = self._find_expert_by_email(user.email)

        if expert is None:
            return ExpertDashboardSummaryResponse(
                assigned_conversations=[],
                profile_summary=ExpertDashboardProfileSummaryResponse(
                    name=self._build_user_display_name(user),
                    email=user.email,
                    specialization="Not linked to a UEX expert profile",
                    availability="Available" if user.is_active else "Inactive",
                    registration_status=user.registration_status,
                    two_factor_enabled=user.two_factor_enabled,
                ),
                knowledge_contributions=ExpertDashboardKnowledgeSummaryResponse(
                    published_guidance_notes=0,
                    reusable_annotations=0,
                    review_templates=0,
                ),
                feedback_summary=ExpertDashboardFeedbackSummaryResponse(
                    clarity_score=None,
                    usefulness_score=None,
                    satisfaction_score=None,
                    communication_quality_score=None,
                    total_feedback_entries=0,
                ),
            )

        assigned_conversations = self._list_assigned_conversations(expert.id, limit=8)

        domain_codes = self.db.execute(
            select(ExpertDomain.domain_code)
            .where(ExpertDomain.expert_id == expert.id)
            .order_by(ExpertDomain.domain_code.asc())
        ).scalars().all()

        specialization = ", ".join(domain_codes) if domain_codes else "No specialization assigned"

        knowledge_counts = self.db.execute(
            select(
                func.count(KnowledgeItem.id).label("total_count"),
                func.sum(case((KnowledgeItem.status == "published", 1), else_=0)).label("published_count"),
                func.sum(case((KnowledgeItem.status == "annotated", 1), else_=0)).label("annotated_count"),
                func.sum(case((KnowledgeItem.status == "template", 1), else_=0)).label("template_count"),
            )
            .where(KnowledgeItem.source_expert_id == expert.id)
        ).one()

        feedback_aggregate = self.db.execute(
            select(
                func.avg(FeedbackEntry.clarity).label("clarity_score"),
                func.avg(FeedbackEntry.usefulness).label("usefulness_score"),
                func.avg(FeedbackEntry.satisfaction).label("satisfaction_score"),
                func.avg(FeedbackEntry.communication_quality).label("communication_quality_score"),
                func.count(FeedbackEntry.id).label("total_feedback_entries"),
            )
            .join(ChatSession, ChatSession.id == FeedbackEntry.session_id)
            .where(ChatSession.assigned_expert_id == expert.id)
        ).one()

        return ExpertDashboardSummaryResponse(
            assigned_conversations=assigned_conversations,
            profile_summary=ExpertDashboardProfileSummaryResponse(
                name=self._build_user_display_name(user),
                email=user.email,
                specialization=specialization,
                availability="Available" if expert.is_active else "Inactive",
                registration_status=user.registration_status,
                two_factor_enabled=user.two_factor_enabled,
            ),
            knowledge_contributions=ExpertDashboardKnowledgeSummaryResponse(
                published_guidance_notes=int(knowledge_counts.published_count or 0),
                reusable_annotations=int(knowledge_counts.annotated_count or 0),
                review_templates=int(knowledge_counts.template_count or 0),
            ),
            feedback_summary=ExpertDashboardFeedbackSummaryResponse(
                clarity_score=self._round_score(feedback_aggregate.clarity_score),
                usefulness_score=self._round_score(feedback_aggregate.usefulness_score),
                satisfaction_score=self._round_score(feedback_aggregate.satisfaction_score),
                communication_quality_score=self._round_score(feedback_aggregate.communication_quality_score),
                total_feedback_entries=int(feedback_aggregate.total_feedback_entries or 0),
            ),
        )

    def list_assigned_sessions(self) -> list[ExpertDashboardAssignedConversationResponse]:
        user = self._get_authenticated_expert_user()
        expert = self._find_expert_by_email(user.email)
        if expert is None:
            return []
        return self._list_assigned_conversations(expert.id)

    def _get_authenticated_expert_user(self) -> User:
        user_id = self.session_data.get("user_id")
        if not user_id:
            raise ExpertServiceError(
                status_code=401,
                code="NOT_AUTHENTICATED",
                message="No active session.",
            )

        user = self.db.get(User, user_id)
        if user is None:
            self.session_data.pop("user_id", None)
            raise ExpertServiceError(
                status_code=401,
                code="NOT_AUTHENTICATED",
                message="No active session.",
            )

        if user.role != "expert":
            raise ExpertServiceError(
                status_code=403,
                code="FORBIDDEN",
                message="Expert access is required.",
            )

        return user

    def _find_expert_by_email(self, email: str | None) -> Expert | None:
        if not email:
            return None

        return self.db.execute(
            select(Expert).where(func.lower(Expert.email) == email.lower())
        ).scalar_one_or_none()

    def _list_assigned_conversations(
        self,
        expert_id: int,
        *,
        limit: int | None = None,
    ) -> list[ExpertDashboardAssignedConversationResponse]:
        latest_message_subquery = (
            select(
                ChatMessage.session_id.label("session_id"),
                func.max(ChatMessage.created_at).label("updated_at"),
            )
            .group_by(ChatMessage.session_id)
            .subquery()
        )

        statement = (
            select(
                ChatSession.id,
                ChatSession.title,
                ChatSession.status,
                ChatSession.mode,
                ChatSession.created_at,
                ChatSession.expert_last_seen_message_id,
                User.name.label("user_name"),
                func.coalesce(latest_message_subquery.c.updated_at, ChatSession.created_at).label("updated_at"),
            )
            .outerjoin(User, User.id == ChatSession.user_id)
            .outerjoin(latest_message_subquery, latest_message_subquery.c.session_id == ChatSession.id)
            .where(ChatSession.assigned_expert_id == expert_id)
            .order_by(func.coalesce(latest_message_subquery.c.updated_at, ChatSession.created_at).desc())
        )

        if limit is not None:
            statement = statement.limit(limit)

        rows = self.db.execute(statement).all()

        conversations = []
        for row in rows:
            latest_message = (
                self.db.execute(
                    select(ChatMessage)
                    .where(ChatMessage.session_id == row.id)
                    .order_by(ChatMessage.id.desc())
                    .limit(1)
                )
                .scalars()
                .first()
            )
            unread_count = int(
                self.db.execute(
                    select(func.count(ChatMessage.id)).where(
                        ChatMessage.session_id == row.id,
                        ChatMessage.role == "user",
                        ChatMessage.id > (row.expert_last_seen_message_id or 0),
                    )
                ).scalar_one()
                or 0
            )
            conversations.append(
                ExpertDashboardAssignedConversationResponse(
                    id=row.id,
                    title=row.title,
                    user_name=row.user_name or "Unknown user",
                    status=row.status,
                    mode=row.mode,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    last_message_at=latest_message.created_at if latest_message is not None else None,
                    last_activity_at=row.updated_at,
                    last_message_preview=(
                        latest_message.content.strip()[:160]
                        if latest_message is not None and latest_message.content
                        else None
                    ),
                    unread_message_count=unread_count,
                    needs_attention=unread_count > 0,
                )
            )

        return conversations

    def _round_score(self, value: float | None) -> float | None:
        if value is None:
            return None

        return round(float(value), 1)

    def _build_user_display_name(self, user: User) -> str:
        full_name = " ".join(part for part in [user.first_name, user.last_name] if part).strip()
        return full_name or user.name or user.email
