from datetime import datetime

from pydantic import BaseModel, Field


class AuthUserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    role: str
    is_active: bool
    registration_status: str
    two_factor_enabled: bool
    two_factor_method: str | None = None
    two_factor_confirmed_at: datetime | None = None
    recovery_codes_remaining: int = 0
    ai_profiling_consent: bool
    gdpr_consent: bool
    can_access_chat_debug_panels: bool
    profiling_opt_out_requested: bool
    account_deletion_requested: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RegisterRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=255)
    last_name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=255)
    password_confirmation: str = Field(min_length=8, max_length=255)
    ai_profiling_consent: bool
    gdpr_consent: bool


class RegisterResponse(BaseModel):
    registration_status: str
    message: str
    notification_email_sent: bool = False


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=255)


class LoginResponse(BaseModel):
    user: AuthUserResponse
    message: str


class LoginTwoFactorResponse(BaseModel):
    requires_2fa: bool = True
    challenge_id: str
    setup_required: bool = False
    remember_device_days: int = 0
    user: AuthUserResponse
    redirect_to: str
    message: str


class TwoFactorSetupResponse(BaseModel):
    challenge_id: str | None = None
    method: str = "totp"
    secret: str
    provisioning_uri: str
    account_name: str
    issuer: str
    message: str


class TwoFactorConfirmRequest(BaseModel):
    verification_code: str = Field(min_length=6, max_length=32)
    challenge_id: str | None = Field(default=None, min_length=1, max_length=255)
    remember_device: bool = False


class TwoFactorConfirmResponse(BaseModel):
    user: AuthUserResponse
    redirect_to: str | None = None
    recovery_codes: list[str] | None = None
    message: str


class TwoFactorRecoveryCodesResponse(BaseModel):
    recovery_codes: list[str]
    recovery_codes_remaining: int
    message: str


class VerifyTwoFactorRequest(BaseModel):
    verification_code: str = Field(min_length=1, max_length=32)
    challenge_id: str | None = Field(default=None, min_length=1, max_length=255)
    remember_device: bool = False


class LogoutResponse(BaseModel):
    message: str


class CurrentUserResponse(BaseModel):
    user: AuthUserResponse


class CurrentUserUpdateRequest(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=255)
    last_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: str | None = Field(default=None, min_length=3, max_length=255)
    ai_profiling_consent: bool | None = None
    gdpr_consent: bool | None = None


class PasswordResetRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)


class PasswordResetResponse(BaseModel):
    message: str


class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(min_length=16, max_length=255)
    password: str = Field(min_length=8, max_length=255)
    password_confirmation: str = Field(min_length=8, max_length=255)


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=255)
    new_password: str = Field(min_length=8, max_length=255)
    new_password_confirmation: str = Field(min_length=8, max_length=255)
