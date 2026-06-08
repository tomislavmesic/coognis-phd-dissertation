from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class AdminDashboardStatResponse(BaseModel):
    label: str
    value: int


class AdminDashboardPendingRegistrationResponse(BaseModel):
    id: int
    name: str
    role: str
    submitted_at: datetime
    consents: str


class AdminDashboardActiveUserResponse(BaseModel):
    id: int
    name: str
    email: str
    status: str
    two_factor: str


class AdminDashboardActiveExpertResponse(BaseModel):
    id: int
    name: str
    email: str
    availability: str
    two_factor: str


class AdminDashboardConsentRequestResponse(BaseModel):
    id: int
    type: str
    submitted_by: str
    status: str


class AdminDashboardResponse(BaseModel):
    pending_registrations: list[AdminDashboardPendingRegistrationResponse]
    system_stats: list[AdminDashboardStatResponse]
    active_users: list[AdminDashboardActiveUserResponse]
    active_experts: list[AdminDashboardActiveExpertResponse]
    consent_requests: list[AdminDashboardConsentRequestResponse]


class BulkTwoFactorUpdateRequest(BaseModel):
    role: str = Field(pattern="^(user|expert)$")
    enabled: bool


class BulkTwoFactorUpdateResponse(BaseModel):
    role: str
    enabled: bool
    affected_count: int
    message: str


class UserCreateRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=255)
    last_name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=3, max_length=255)
    role: str = Field(default="user", max_length=20)
    is_active: bool = True
    temporary_password: str | None = Field(default=None, min_length=8, max_length=255)
    auto_generate_password: bool = True
    ai_profiling_consent_recorded: bool = False
    gdpr_consent_recorded: bool = False
    send_credentials_email: bool = True


class UserUpdateRequest(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=255)
    last_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: str | None = Field(default=None, min_length=3, max_length=255)
    role: str | None = Field(default=None, max_length=20)
    is_active: bool | None = None
    two_factor_enabled: bool | None = None
    ai_profiling_consent: bool | None = None
    gdpr_consent: bool | None = None
    can_access_chat_debug_panels: bool | None = None
    registration_status: str | None = Field(default=None, max_length=50)
    manual_mbti: str | None = Field(default=None, min_length=4, max_length=4)


class UserResponse(BaseModel):
    id: int
    name: str
    first_name: str
    last_name: str
    email: str
    role: str
    is_active: bool
    registration_status: str
    two_factor_enabled: bool
    ai_profiling_consent: bool
    gdpr_consent: bool
    can_access_chat_debug_panels: bool
    profiling_opt_out_requested: bool
    account_deletion_requested: bool
    created_at: datetime
    updated_at: datetime
    generated_temporary_password: str | None = None
    credentials_email_triggered: bool = False
    manual_mbti: str | None = None
    inferred_mbti: str | None = None
    effective_mbti: str | None = None
    profile_confidence: float | None = None
    profile_interaction_count: int = 0

    model_config = {"from_attributes": True}


class RegistrationQueueItemResponse(BaseModel):
    id: int
    full_name: str
    email: str
    requested_role: str
    ai_profiling_consent: bool
    gdpr_consent: bool
    created_at: datetime


class RegistrationApprovalActionRequest(BaseModel):
    send_credentials_email: bool = True


class RegistrationApprovalActionResponse(BaseModel):
    registration_id: int
    status: str
    credentials_email_triggered: bool = False


class UserCredentialActionResponse(BaseModel):
    user_id: int
    action: str
    credentials_email_triggered: bool = False
    generated_temporary_password: str | None = None


class TrustedDeviceAdminResponse(BaseModel):
    id: int
    created_at: datetime
    expires_at: datetime
    last_used_at: datetime | None = None

    model_config = {"from_attributes": True}


class ExpertProvisionResponse(BaseModel):
    expert_id: int
    platform_user_id: int
    action: str
    credentials_email_triggered: bool = False
    generated_temporary_password: str | None = None


class ChatSessionDeleteResponse(BaseModel):
    session_id: int
    deleted: bool
    message: str


class AdminChatSessionResponse(BaseModel):
    id: int
    title: str | None
    status: str
    mode: str
    user_id: int | None
    user_name: str | None
    assigned_expert_id: int | None
    assigned_expert_name: str | None
    created_at: datetime
    closed_at: datetime | None
    eligible_reason: str


class AdminConversationOverviewResponse(BaseModel):
    id: int
    title: str | None
    status: str
    mode: str
    user_id: int | None
    user_name: str | None
    assigned_expert_id: int | None
    assigned_expert_name: str | None
    created_at: datetime
    closed_at: datetime | None
    last_message_at: datetime | None
    last_activity_at: datetime | None = None
    last_message_role: str | None
    last_message_preview: str | None
    message_count: int
    unread_message_count: int = 0
    needs_attention: bool = False
    waiting_on: str
    typing_actor_role: str | None = None


class AdminConversationMessageResponse(BaseModel):
    id: int
    role: str
    mode: str
    content: str
    created_at: datetime


class AdminConversationHandoffResponse(BaseModel):
    id: int
    session_id: int
    session_title: str | None = None
    expert_id: int
    expert_name: str | None = None
    reason: str | None
    from_mode: str
    to_mode: str
    created_at: datetime


class AdminConversationDetailResponse(BaseModel):
    conversation: AdminConversationOverviewResponse
    messages: list[AdminConversationMessageResponse]
    handoffs: list[AdminConversationHandoffResponse]


class ExpertAdminCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str | None = Field(default=None, min_length=3, max_length=255)
    is_active: bool = True
    domain_codes: list[str] = Field(default_factory=list)


class ExpertAdminUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: str | None = Field(default=None, min_length=3, max_length=255)
    is_active: bool | None = None
    domain_codes: list[str] | None = None


class ExpertAdminResponse(BaseModel):
    id: int
    name: str
    email: str | None
    is_active: bool
    domain_codes: list[str] = Field(default_factory=list)
    platform_user_id: int | None = None
    has_platform_account: bool = False
    platform_account_active: bool = False
    platform_account_registration_status: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeAdminCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    domain_code: str = Field(min_length=1, max_length=100)
    status: str = Field(default="draft", max_length=50)
    source_expert_id: int | None = Field(default=None, ge=1)


class KnowledgeAdminUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = Field(default=None, min_length=1)
    domain_code: str | None = Field(default=None, min_length=1, max_length=100)
    status: str | None = Field(default=None, max_length=50)
    source_expert_id: int | None = Field(default=None, ge=1)


class KnowledgeAdminResponse(BaseModel):
    id: int
    title: str
    content: str
    domain_code: str
    status: str
    source_expert_id: int | None
    source_expert_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DomainOptionResponse(BaseModel):
    code: str


class LlmProviderOptionResponse(BaseModel):
    provider: str
    default_model: str
    model_options: list[str] = Field(default_factory=list)


class ModuleSettingsResponse(BaseModel):
    synapse_enabled: bool
    uex_enabled: bool
    ulm_enabled: bool
    page_enabled: bool
    llm_provider: str
    llm_model: str
    llm_available_providers: list[LlmProviderOptionResponse] = Field(default_factory=list)


class ModuleSettingsUpdateRequest(BaseModel):
    synapse_enabled: bool | None = None
    uex_enabled: bool | None = None
    ulm_enabled: bool | None = None
    page_enabled: bool | None = None
    llm_provider: str | None = None
    llm_model: str | None = None


class GeneralSettingsResponse(BaseModel):
    show_chat_debug_panels: bool
    verbose_routing_logs: bool
    allow_expert_handoff: bool
    allow_ulm_in_chat: bool


class GeneralSettingsUpdateRequest(BaseModel):
    show_chat_debug_panels: bool | None = None
    verbose_routing_logs: bool | None = None
    allow_expert_handoff: bool | None = None
    allow_ulm_in_chat: bool | None = None


class ProfileAdminCreateRequest(BaseModel):
    expert_id: int = Field(ge=1)
    manual_mbti: str | None = Field(default=None, min_length=4, max_length=4)
    inferred_mbti: str | None = Field(default=None, min_length=4, max_length=4)
    effective_mbti: str | None = Field(default=None, min_length=4, max_length=4)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class ProfileAdminUpdateRequest(BaseModel):
    manual_mbti: str | None = Field(default=None, min_length=4, max_length=4)
    inferred_mbti: str | None = Field(default=None, min_length=4, max_length=4)
    effective_mbti: str | None = Field(default=None, min_length=4, max_length=4)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class ProfileAdminResponse(BaseModel):
    id: int
    expert_id: int
    manual_mbti: str | None
    inferred_mbti: str | None
    effective_mbti: str | None
    confidence: float | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UlmSourceAdminCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    document: str | None = Field(default=None, min_length=1)
    url: str | None = Field(default=None, max_length=2048)

    @model_validator(mode="after")
    def validate_source_input(self):
        if bool(self.document) == bool(self.url):
            raise ValueError("Provide exactly one of 'document' or 'url'.")
        return self


class UlmSourceAdminUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    source_value: str | None = Field(default=None, min_length=1, max_length=2048)
    indexing_status: str | None = Field(default=None, max_length=50)


class UlmSourceAdminResponse(BaseModel):
    id: int
    source_type: str
    source_value: str
    title: str | None = None
    indexing_status: str
    document_count: int = 0
    indexed_chunk_count: int = 0
    created_at: datetime
    last_updated_at: datetime

    model_config = {"from_attributes": True}


class UlmSourceAdminChunkResponse(BaseModel):
    id: int
    title: str | None
    content: str | None
    url: str | None
    chunk_index: int
    chunk_count: int
    indexing_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UlmSourceAdminDetailResponse(UlmSourceAdminResponse):
    documents: list[UlmSourceAdminChunkResponse] = Field(default_factory=list)
