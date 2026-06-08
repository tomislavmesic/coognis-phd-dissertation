from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

SubjectType = Literal["user", "expert"]
InferenceMode = Literal["user_inference", "expert_inference", "batch_recalculation"]


class SynapseDimensionResult(BaseModel):
    label: str
    probabilities: dict[str, float]


class SynapseInferenceResult(BaseModel):
    mbti_type: str
    dimensions: dict[str, SynapseDimensionResult]
    confidence: float
    model_version: str
    profile_status: Literal["unstable", "stable"]


class SynapseInferRequest(BaseModel):
    content: str = Field(min_length=1)
    subject_type: SubjectType | None = None
    subject_id: int | None = Field(default=None, ge=1)
    mode: InferenceMode = "user_inference"

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Content must not be empty.")
        return cleaned


class SynapseProfileUpdateRequest(BaseModel):
    content: str = Field(min_length=1)
    subject_type: SubjectType
    subject_id: int = Field(ge=1)
    mode: InferenceMode = "user_inference"

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Content must not be empty.")
        return cleaned


class SynapseRunResponse(SynapseInferenceResult):
    id: int
    subject_type: SubjectType | None = None
    subject_id: int | None = None
    mode: InferenceMode | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
