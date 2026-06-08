from pydantic import BaseModel, Field


class PageUserProfile(BaseModel):
    mbti: str | None = Field(default=None, min_length=4, max_length=4)


class PageExpertSuggestion(BaseModel):
    name: str
    domain_codes: list[str] = Field(default_factory=list)
    is_contactable: bool = False
    reason: str | None = None


class PageUlmSource(BaseModel):
    title: str | None = None
    chunk_index: int | None = None
    source_type: str | None = None
    url: str | None = None


class PageUlmGrounding(BaseModel):
    summary: str
    source_count: int = 0
    chunk_count: int = 0
    sources: list[PageUlmSource] = Field(default_factory=list)


class PageRespondRequest(BaseModel):
    user_profile: PageUserProfile
    query: str = Field(min_length=1)
    uex_knowledge: str = Field(min_length=1)
    expert_suggestion: PageExpertSuggestion | None = None
    ulm_grounding: PageUlmGrounding | None = None
    ulm_used: bool = False
    conversation_mode: str = Field(default="system", min_length=1, max_length=20)


class PageRespondResponse(BaseModel):
    response: str
    style_label: str | None = None
    intent_label: str | None = None
    sections: list[str] = Field(default_factory=list)
