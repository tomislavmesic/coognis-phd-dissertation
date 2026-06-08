from pydantic import BaseModel


class UserRecommendedExpertItemResponse(BaseModel):
    expert_id: int
    name: str
    email: str | None
    is_active: bool
    is_contactable: bool = False
    domain_codes: list[str]
    total_score: float
    reason: str
    compatibility_note: str


class UserRecommendedExpertResponse(BaseModel):
    item: UserRecommendedExpertItemResponse | None
    profiling_used: bool
    target_mbti: str | None
    profile_source: str | None = None
    message: str
