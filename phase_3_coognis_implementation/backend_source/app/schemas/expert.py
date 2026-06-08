from datetime import datetime

from pydantic import BaseModel


class ExpertDashboardAssignedConversationResponse(BaseModel):
    id: int
    title: str | None
    user_name: str
    status: str
    mode: str
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime | None = None
    last_activity_at: datetime | None = None
    last_message_preview: str | None = None
    unread_message_count: int = 0
    needs_attention: bool = False


class ExpertAssignedSessionListResponse(BaseModel):
    items: list[ExpertDashboardAssignedConversationResponse]
    total: int


class ExpertDashboardProfileSummaryResponse(BaseModel):
    name: str
    email: str
    specialization: str
    availability: str
    registration_status: str
    two_factor_enabled: bool


class ExpertDashboardKnowledgeSummaryResponse(BaseModel):
    published_guidance_notes: int
    reusable_annotations: int
    review_templates: int


class ExpertDashboardFeedbackSummaryResponse(BaseModel):
    clarity_score: float | None
    usefulness_score: float | None
    satisfaction_score: float | None
    communication_quality_score: float | None
    total_feedback_entries: int


class ExpertDashboardSummaryResponse(BaseModel):
    assigned_conversations: list[ExpertDashboardAssignedConversationResponse]
    profile_summary: ExpertDashboardProfileSummaryResponse
    knowledge_contributions: ExpertDashboardKnowledgeSummaryResponse
    feedback_summary: ExpertDashboardFeedbackSummaryResponse
