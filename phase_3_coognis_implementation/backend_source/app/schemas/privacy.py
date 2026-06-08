from datetime import datetime

from pydantic import BaseModel, Field


class ConsentUpdateRequest(BaseModel):
    ai_profiling_consent: bool | None = None


class PrivacyActionResponse(BaseModel):
    message: str
    ai_profiling_consent: bool
    gdpr_consent: bool
    profiling_opt_out_requested: bool
    account_deletion_requested: bool


class DataRequestResponse(BaseModel):
    id: int
    user_id: int
    request_type: str
    status: str
    reason: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AccountDeletionRequestCreate(BaseModel):
    reason: str | None = Field(default=None, max_length=2000)


class AdminDataRequestItemResponse(BaseModel):
    id: int
    request_type: str
    status: str
    reason: str | None = None
    user_id: int
    full_name: str
    email: str
    created_at: datetime
    updated_at: datetime


class AdminDataRequestActionResponse(BaseModel):
    request_id: int
    status: str
