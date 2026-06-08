from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

FeedbackType = Literal["response", "interaction", "system"]


class FeedbackCreateRequest(BaseModel):
    session_id: int = Field(ge=1)
    clarity: int = Field(ge=1, le=5)
    usefulness: int = Field(ge=1, le=5)
    personalization_fit: int = Field(ge=1, le=5)
    communication_quality: int = Field(ge=1, le=5)
    satisfaction: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


class FeedbackResponse(BaseModel):
    id: int
    session_id: int
    feedback_type: FeedbackType
    submitted_by_role: str
    clarity: int
    usefulness: int
    personalization_fit: int
    communication_quality: int
    satisfaction: int
    comment: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
