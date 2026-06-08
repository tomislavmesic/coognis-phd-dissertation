from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ChatMode = Literal["system", "handoff", "expert"]


class MindChatMessageRequest(BaseModel):
    session_id: int = Field(ge=1)
    query: str = Field(min_length=1)
    use_synapse: bool = True
    use_uex: bool = True
    use_ulm: bool = False


class ExpertChatMessageRequest(BaseModel):
    session_id: int = Field(ge=1)
    content: str = Field(min_length=1)


class ExpertSuggestion(BaseModel):
    expert_id: int
    name: str
    total_score: float
    is_contactable: bool = False
    domain_codes: list[str] = Field(default_factory=list)


class MindDebugKnowledgeItem(BaseModel):
    id: int
    title: str
    domain_code: str


class MindDebugUlmChunk(BaseModel):
    source_id: int | None = None
    document_id: int | None = None
    title: str | None = None
    chunk_index: int | None = None
    source_type: str | None = None
    score: float | None = None


class MindPageDebug(BaseModel):
    style_label: str | None = None
    intent_label: str | None = None
    sections: list[str] = Field(default_factory=list)


class MindDebugPageExpertSuggestion(BaseModel):
    name: str
    domain_codes: list[str] = Field(default_factory=list)
    is_contactable: bool = False
    reason: str | None = None


class MindDebugPageUlmSource(BaseModel):
    title: str | None = None
    chunk_index: int | None = None
    source_type: str | None = None
    url: str | None = None


class MindDebugPageUlmGrounding(BaseModel):
    summary: str
    source_count: int = 0
    chunk_count: int = 0
    sources: list[MindDebugPageUlmSource] = Field(default_factory=list)


class MindDebugPageInput(BaseModel):
    user_mbti: str | None = None
    query: str
    uex_knowledge: str
    expert_suggestion: MindDebugPageExpertSuggestion | None = None
    ulm_grounding: MindDebugPageUlmGrounding | None = None
    ulm_used: bool = False
    conversation_mode: ChatMode


class MindSynapseDebug(BaseModel):
    stored_mbti: str | None = None
    inferred_mbti: str | None = None
    effective_mbti: str | None = None
    confidence: float | None = None


class MindChatDebug(BaseModel):
    synapse: MindSynapseDebug | None = None
    inferred_domain_codes: list[str] = Field(default_factory=list)
    uex_knowledge_preview: str | None = None
    uex_knowledge_items: list[MindDebugKnowledgeItem] = Field(default_factory=list)
    ulm_chunks: list[MindDebugUlmChunk] = Field(default_factory=list)
    page: MindPageDebug | None = None
    page_input: MindDebugPageInput | None = None
    expert_suggestion_reason: str | None = None


class MindChatMessageResponse(BaseModel):
    final_response: str
    modules_used: list[str]
    assistant_message_id: int | None = None
    expert_suggestion: ExpertSuggestion | None = None
    debug: MindChatDebug | None = None


class ExpertChatMessageResponse(BaseModel):
    message: "ChatMessageResponse"
    expert_profile_updated: bool = False


class MindChatLogResponse(MindChatMessageResponse):
    id: int
    session_id: int
    query: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionStartRequest(BaseModel):
    user_id: int | None = Field(default=None, ge=1)
    title: str | None = Field(default=None, max_length=255)
    mode: ChatMode = "system"
    expert_id: int | None = Field(default=None, ge=1)
    handoff_reason: str | None = Field(default=None, max_length=1000)


class ChatSessionCloseRequest(BaseModel):
    session_id: int = Field(ge=1)


class ChatTypingRequest(BaseModel):
    session_id: int = Field(ge=1)
    is_typing: bool = True


class ChatHandoffRequest(BaseModel):
    session_id: int = Field(ge=1)
    expert_id: int = Field(ge=1)
    reason: str | None = None


class ChatSessionResponse(BaseModel):
    id: int
    user_id: int | None
    user_name: str | None = None
    title: str | None
    mode: ChatMode
    status: str
    assigned_expert_id: int | None = None
    assigned_expert_name: str | None = None
    created_at: datetime
    closed_at: datetime | None = None
    closed_by_role: str | None = None
    closed_by_name: str | None = None
    typing_actor_role: str | None = None
    typing_updated_at: datetime | None = None
    feedback_mode: str | None = None
    feedback_pending_for_current_user: bool = False
    last_message_at: datetime | None = None
    last_activity_at: datetime | None = None
    last_message_role: str | None = None
    last_message_preview: str | None = None
    unread_message_count: int = 0
    needs_attention: bool = False

    model_config = {"from_attributes": True}


class ChatUnreadSummaryResponse(BaseModel):
    attention_count: int


class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    mode: ChatMode
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatHistoryResponse(BaseModel):
    items: list[ChatMessageResponse]
    total: int


class ChatSessionListResponse(BaseModel):
    items: list[ChatSessionResponse]
    total: int


class ExpertHandoffResponse(BaseModel):
    id: int
    session_id: int
    expert_id: int
    reason: str | None
    from_mode: ChatMode
    to_mode: ChatMode
    created_at: datetime

    model_config = {"from_attributes": True}
