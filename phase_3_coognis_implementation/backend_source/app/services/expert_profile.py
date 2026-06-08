from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Expert, ExpertProfile, User
from app.schemas.synapse import SynapseProfileUpdateRequest
from app.services.synapse import SynapseService
from app.services.synapse.profile import SynapseProfileService


class ExpertProfileService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.synapse_profile_service = SynapseProfileService(db)

    def get_profile(self, expert_id: int) -> ExpertProfile | None:
        return self.db.execute(
            select(ExpertProfile).where(ExpertProfile.expert_id == expert_id)
        ).scalar_one_or_none()

    def get_or_create_profile(self, expert_id: int) -> ExpertProfile:
        profile = self.get_profile(expert_id)
        if profile is not None:
            return profile

        profile = ExpertProfile(expert_id=expert_id)
        self.db.add(profile)
        self.db.flush()
        return profile

    def find_expert_for_user(self, user_id: int) -> Expert | None:
        user = self.db.get(User, user_id)
        if user is None or user.role != "expert":
            return None

        return self.db.execute(
            select(Expert).where(Expert.email == user.email.lower())
        ).scalar_one_or_none()

    def process_interaction(
        self,
        *,
        expert_id: int,
        message_text: str,
        synapse_service: SynapseService | None,
    ) -> ExpertProfile:
        profile = self.get_or_create_profile(expert_id)
        cleaned_text = str(message_text or "").strip()

        if not cleaned_text:
            self.db.commit()
            self.db.refresh(profile)
            return profile

        profile.accumulated_interaction_text = self._append_text(
            profile.accumulated_interaction_text,
            cleaned_text,
        )
        profile.interaction_count += 1

        if self._should_refresh_profile(profile) and synapse_service is not None:
            inference_result = synapse_service.infer(profile.accumulated_interaction_text)
            self.synapse_profile_service.create_inference_run(
                SynapseProfileUpdateRequest(
                    content=profile.accumulated_interaction_text,
                    subject_type="expert",
                    subject_id=expert_id,
                    mode="expert_inference",
                ),
                inference_result,
            )
            profile.inferred_mbti = inference_result.mbti_type
            profile.confidence = inference_result.confidence
            profile.effective_mbti = profile.manual_mbti or inference_result.mbti_type
            profile.last_inference_interaction_count = profile.interaction_count
            profile.last_inference_text_length = len(profile.accumulated_interaction_text)
            profile.last_inferred_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(profile)
        return profile

    def _should_refresh_profile(self, profile: ExpertProfile) -> bool:
        total_chars = len(profile.accumulated_interaction_text or "")

        if profile.inferred_mbti is None:
            return (
                profile.interaction_count >= settings.expert_profile_min_interactions
                and total_chars >= settings.expert_profile_min_text_chars
            )

        new_interactions = profile.interaction_count - profile.last_inference_interaction_count
        new_chars = total_chars - profile.last_inference_text_length

        return (
            new_interactions >= settings.expert_profile_refresh_every_interactions
            and new_chars >= settings.expert_profile_refresh_min_new_text_chars
        )

    def _append_text(self, existing_text: str, new_text: str) -> str:
        combined = f"{existing_text}\n\n{new_text}".strip() if existing_text else new_text
        if len(combined) <= settings.expert_profile_text_window_chars:
            return combined
        return combined[-settings.expert_profile_text_window_chars :]
