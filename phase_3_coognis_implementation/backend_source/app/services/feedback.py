from sqlalchemy.orm import Session

from app.models import ChatSession, FeedbackEntry, User
from app.schemas.feedback import FeedbackCreateRequest, FeedbackResponse
from app.services.expert_profile import ExpertProfileService


class FeedbackService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.expert_profile_service = ExpertProfileService(db)

    def create_feedback(self, feedback_type: str, actor_user_id: int, payload: FeedbackCreateRequest) -> FeedbackResponse:
        session = self.db.get(ChatSession, payload.session_id)
        if session is None:
            raise LookupError("Session not found.")

        submitted_by_role = self._resolve_feedback_role(actor_user_id, session)
        existing = (
            self.db.query(FeedbackEntry)
            .filter(
                FeedbackEntry.session_id == payload.session_id,
                FeedbackEntry.feedback_type == feedback_type,
                FeedbackEntry.submitted_by_role == submitted_by_role,
            )
            .one_or_none()
        )
        if existing is not None:
            raise ValueError("Feedback for this conversation has already been submitted by this participant.")

        entry = FeedbackEntry(
            session_id=payload.session_id,
            feedback_type=feedback_type,
            submitted_by_role=submitted_by_role,
            clarity=payload.clarity,
            usefulness=payload.usefulness,
            personalization_fit=payload.personalization_fit,
            communication_quality=payload.communication_quality,
            satisfaction=payload.satisfaction,
            comment=payload.comment,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return FeedbackResponse.model_validate(entry)

    def _resolve_feedback_role(self, actor_user_id: int, session: ChatSession) -> str:
        user = self.db.get(User, actor_user_id)
        if user is None:
            raise LookupError("User not found.")

        if user.role == "expert":
            expert = self.expert_profile_service.find_expert_for_user(actor_user_id)
            if expert is None or session.assigned_expert_id != expert.id:
                raise ValueError("This conversation is not assigned to the current expert.")
            return "expert"

        if session.user_id != user.id:
            raise ValueError("This conversation is not assigned to the current user.")
        return "user"
