from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import User, UserProfile
from app.schemas.synapse import SynapseProfileUpdateRequest
from app.services.synapse import SynapseService
from app.services.synapse.profile import SynapseProfileService

MBTI_TYPES = {
    "INTJ", "INTP", "ENTJ", "ENTP",
    "INFJ", "INFP", "ENFJ", "ENFP",
    "ISTJ", "ISFJ", "ESTJ", "ESFJ",
    "ISTP", "ISFP", "ESTP", "ESFP",
}


class UserProfileService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.synapse_profile_service = SynapseProfileService(db)

    def get_profile(self, user_id: int) -> UserProfile | None:
        return self.db.query(UserProfile).filter(UserProfile.user_id == user_id).one_or_none()

    def get_or_create_profile(self, user_id: int) -> UserProfile:
        profile = self.get_profile(user_id)
        if profile is not None:
            return profile

        profile = UserProfile(user_id=user_id)
        self.db.add(profile)
        self.db.flush()
        return profile

    def apply_manual_mbti(self, user_id: int, manual_mbti: str | None) -> UserProfile:
        profile = self.get_or_create_profile(user_id)
        normalized_manual_mbti = self._normalize_mbti(manual_mbti)
        profile.manual_mbti = normalized_manual_mbti
        profile.effective_mbti = normalized_manual_mbti or profile.inferred_mbti
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def process_chat_interaction(self, user_id: int, message_text: str, synapse_service: SynapseService | None) -> UserProfile | None:
        user = self.db.get(User, user_id)
        if user is None or not user.ai_profiling_consent:
            return self.get_profile(user_id)

        profile = self.get_or_create_profile(user_id)
        cleaned_text = str(message_text or "").strip()
        if not cleaned_text:
            self.db.commit()
            self.db.refresh(profile)
            return profile

        profile.accumulated_chat_text = self._append_text(profile.accumulated_chat_text, cleaned_text)
        profile.interaction_count += 1

        if self._should_refresh_profile(profile) and synapse_service is not None:
            inference_result = synapse_service.infer(profile.accumulated_chat_text)
            self.synapse_profile_service.create_inference_run(
                SynapseProfileUpdateRequest(
                    content=profile.accumulated_chat_text,
                    subject_type="user",
                    subject_id=user.id,
                    mode="user_inference",
                ),
                inference_result,
            )
            profile.inferred_mbti = inference_result.mbti_type
            profile.confidence = inference_result.confidence
            profile.effective_mbti = profile.manual_mbti or inference_result.mbti_type
            profile.last_inference_interaction_count = profile.interaction_count
            profile.last_inference_text_length = len(profile.accumulated_chat_text)
            profile.last_inferred_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(profile)
        return profile

    def _should_refresh_profile(self, profile: UserProfile) -> bool:
        total_chars = len(profile.accumulated_chat_text or "")

        if profile.inferred_mbti is None:
            return (
                profile.interaction_count >= settings.user_profile_min_interactions
                and total_chars >= settings.user_profile_min_text_chars
            )

        new_interactions = profile.interaction_count - profile.last_inference_interaction_count
        new_chars = total_chars - profile.last_inference_text_length

        return (
            new_interactions >= settings.user_profile_refresh_every_interactions
            and new_chars >= settings.user_profile_refresh_min_new_text_chars
        )

    def _append_text(self, existing_text: str, new_text: str) -> str:
        combined = f"{existing_text}\n\n{new_text}".strip() if existing_text else new_text
        if len(combined) <= settings.user_profile_text_window_chars:
            return combined
        return combined[-settings.user_profile_text_window_chars :]

    def _normalize_mbti(self, value: str | None) -> str | None:
        if value is None:
            return None

        normalized = value.strip().upper()
        if not normalized:
            return None
        if normalized not in MBTI_TYPES:
            raise ValueError("Invalid MBTI type.")
        return normalized
