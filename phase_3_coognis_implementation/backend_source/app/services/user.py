from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ChatMessage, ChatSession, User
from app.schemas.uex import ExpertMatchRequest
from app.schemas.user import UserRecommendedExpertItemResponse, UserRecommendedExpertResponse
from app.services.uex import UexService
from app.services.user_profile import UserProfileService


class UserServiceError(Exception):
    def __init__(self, *, status_code: int, code: str, message: str, details: Any = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


class UserService:
    def __init__(self, db: Session, session_data: dict[str, Any]) -> None:
        self.db = db
        self.session_data = session_data
        self.uex_service = UexService(db)
        self.user_profile_service = UserProfileService(db)

    def get_recommended_expert(self) -> UserRecommendedExpertResponse:
        user = self._get_authenticated_user()

        target_mbti = None
        profiling_used = False
        profile_source = None

        if user.ai_profiling_consent:
            profile = self.user_profile_service.get_profile(user.id)
            if profile is not None and profile.effective_mbti:
                target_mbti = profile.effective_mbti
                profiling_used = True
                profile_source = "manual_override" if profile.manual_mbti else "synapse_inferred"

        domain_codes = self._derive_domain_codes_for_user(user.id)

        matches = self.uex_service.match_experts(
            ExpertMatchRequest(
                domain_codes=domain_codes,
                target_mbti=target_mbti,
                limit=1,
            )
        )

        if not matches.items:
            return UserRecommendedExpertResponse(
                item=None,
                profiling_used=profiling_used,
                target_mbti=target_mbti,
                profile_source=profile_source,
                message="No expert recommendation is available yet.",
            )

        top_match = matches.items[0]
        expert = self.uex_service.get_expert(top_match.expert_id)

        if profiling_used and target_mbti:
            reason = "Recommended using your current profiling-enabled SYNAPSE compatibility signal."
            compatibility_note = f"Matched against your current stored effective profile: {target_mbti}."
            if domain_codes:
                compatibility_note += f" Domain cues were also detected: {', '.join(domain_codes)}."
        elif not user.ai_profiling_consent:
            reason = "Recommended using active expert availability because profiling consent is currently withdrawn."
            compatibility_note = "The match excludes profiling-based personalization signals."
            if domain_codes:
                compatibility_note += f" Recent topic cues still informed the recommendation: {', '.join(domain_codes)}."
        else:
            reason = "Recommended using active expert availability while no stored user profile is available yet."
            compatibility_note = "A stronger compatibility score will be available after a user profile is inferred."
            if domain_codes:
                compatibility_note += f" Current topic cues were detected from recent interactions: {', '.join(domain_codes)}."

        return UserRecommendedExpertResponse(
            item=UserRecommendedExpertItemResponse(
                expert_id=expert.id,
                name=expert.name,
                email=expert.email,
                is_active=expert.is_active,
                is_contactable=expert.is_contactable,
                domain_codes=expert.domain_codes,
                total_score=top_match.total_score,
                reason=reason,
                compatibility_note=compatibility_note,
            ),
            profiling_used=profiling_used,
            target_mbti=target_mbti,
            profile_source=profile_source,
            message="Recommended expert loaded successfully.",
        )

    def _get_authenticated_user(self) -> User:
        user_id = self.session_data.get("user_id")
        if not user_id:
            raise UserServiceError(
                status_code=401,
                code="NOT_AUTHENTICATED",
                message="No active session.",
            )

        user = self.db.get(User, user_id)
        if user is None:
            self.session_data.pop("user_id", None)
            raise UserServiceError(
                status_code=401,
                code="NOT_AUTHENTICATED",
                message="No active session.",
            )

        if user.role != "user":
            raise UserServiceError(
                status_code=403,
                code="FORBIDDEN",
                message="User access is required.",
            )

        return user

    def _derive_domain_codes_for_user(self, user_id: int) -> list[str]:
        recent_user_messages = self.db.execute(
            select(ChatMessage.content)
            .join(ChatSession, ChatSession.id == ChatMessage.session_id)
            .where(
                ChatSession.user_id == user_id,
                ChatMessage.role == "user",
            )
            .order_by(ChatMessage.id.desc())
            .limit(12)
        ).scalars().all()

        if not recent_user_messages:
            return []

        combined_text = "\n".join(reversed([message for message in recent_user_messages if message]))
        return self.uex_service.suggest_domain_codes_for_text(combined_text)
