from __future__ import annotations
from typing import Dict, Literal, Optional
from pydantic import BaseModel, Field, field_validator

SubjectType = Literal["user", "expert"]
InferenceMode = Literal["user_inference", "expert_inference", "batch_recalculation"]

class SynapseMetadata(BaseModel):
    session_id: Optional[int] = None
    message_count: Optional[int] = None
    token_count: Optional[int] = None

class SynapseInferenceRequest(BaseModel):
    subject_type: SubjectType
    subject_id: Optional[int] = None
    mode: InferenceMode
    content: str = Field(..., min_length=1)
    metadata: Optional[SynapseMetadata] = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Content must not be empty.")
        return cleaned

class DimensionProbabilities(BaseModel):
    label: str
    probabilities: Dict[str, float]

class SynapseInferenceResponse(BaseModel):
    subject_type: SubjectType
    subject_id: Optional[int] = None
    mbti_type: str
    dimensions: Dict[str, DimensionProbabilities]
    confidence: float
    model_version: str
    profile_status: Literal["unstable", "stable"]
