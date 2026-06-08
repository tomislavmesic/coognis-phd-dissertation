from datetime import datetime

from pydantic import BaseModel, Field


class ExpertCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    is_active: bool = True
    domain_codes: list[str] = Field(default_factory=list)


class ExpertResponse(BaseModel):
    id: int
    name: str
    email: str | None
    is_active: bool
    domain_codes: list[str]
    platform_user_id: int | None = None
    is_contactable: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class ExpertAnalysisResponse(BaseModel):
    expert_id: int
    manual_mbti: str | None
    inferred_mbti: str
    effective_mbti: str
    confidence: float
    model_version: str


class ExpertMatchRequest(BaseModel):
    domain_codes: list[str] = Field(default_factory=list)
    target_mbti: str | None = Field(default=None, min_length=4, max_length=4)
    limit: int = Field(default=10, ge=1, le=100)


class ExpertMatchResult(BaseModel):
    expert_id: int
    name: str
    domain_codes: list[str]
    effective_mbti: str | None
    is_contactable: bool = False
    domain_similarity_score: float
    profile_compatibility_score: float
    availability_score: float
    historical_satisfaction_score: float
    total_score: float


class ExpertMatchResponse(BaseModel):
    items: list[ExpertMatchResult]
    total: int


class KnowledgeItemCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    domain_code: str = Field(min_length=1, max_length=100)
    status: str = Field(default="draft", min_length=1, max_length=50)
    source_expert_id: int | None = Field(default=None, ge=1)


class KnowledgeItemUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = Field(default=None, min_length=1)
    domain_code: str | None = Field(default=None, min_length=1, max_length=100)
    status: str | None = Field(default=None, min_length=1, max_length=50)
    source_expert_id: int | None = Field(default=None, ge=1)


class KnowledgeItemResponse(BaseModel):
    id: int
    title: str
    content: str
    domain_code: str
    status: str
    source_expert_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeItemListResponse(BaseModel):
    items: list[KnowledgeItemResponse]
    total: int
    skip: int
    limit: int


class UexKnowledgeContextResponse(BaseModel):
    content: str
    items: list[KnowledgeItemResponse] = Field(default_factory=list)
