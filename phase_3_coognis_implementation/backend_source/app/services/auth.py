from __future__ import annotations

import base64
import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from time import time
from typing import Any
from uuid import uuid4

import pyotp
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger, log_event
from app.models import PasswordResetToken, TrustedDevice, User
from app.schemas.auth import (
    AuthUserResponse,
    CurrentUserResponse,
    CurrentUserUpdateRequest,
    LoginRequest,
    LoginResponse,
    LoginTwoFactorResponse,
    LogoutResponse,
    PasswordResetResponse,
    RegisterRequest,
    RegisterResponse,
    TwoFactorConfirmResponse,
    TwoFactorRecoveryCodesResponse,
    TwoFactorSetupResponse,
)
from app.services.auth_rate_limiter import auth_rate_limiter
from app.services.email import EmailService
from app.services.password_security import hash_password, verify_password

logger = get_logger("auth")


class AuthServiceError(Exception):
    def __init__(self, *, status_code: int, code: str, message: str, details: Any = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


class AuthService:
    def __init__(
        self,
        db: Session | None,
        session_data: dict[str, Any],
        *,
        request_cookies: dict[str, str] | None = None,
        user_agent: str | None = None,
    ) -> None:
        self.db = db
        self.session_data = session_data
        self.request_cookies = request_cookies or {}
        self.user_agent = user_agent or ""
        self.email_service = EmailService()
        self.trusted_device_cookie_to_set: dict[str, Any] | None = None
        self.clear_trusted_device_cookie: bool = False

    @property
    def trusted_device_cookie_name(self) -> str:
        return settings.auth_trusted_device_cookie_name

    @property
    def trusted_device_same_site(self) -> str:
        return settings.auth_session_same_site

    @property
    def trusted_device_https_only(self) -> bool:
        return settings.auth_session_https_only

    def register(self, payload: RegisterRequest) -> RegisterResponse:
        if payload.password != payload.password_confirmation:
            raise AuthServiceError(
                status_code=422,
                code="VALIDATION_ERROR",
                message="Password confirmation must match the password.",
            )

        if not payload.ai_profiling_consent or not payload.gdpr_consent:
            raise AuthServiceError(
                status_code=422,
                code="CONSENT_REQUIRED",
                message="Both required consent checkboxes must be accepted.",
            )

        existing = self._get_user_by_email(payload.email)
        if existing is not None:
            self._log_auth_event(
                "auth_registration_duplicate",
                email=str(payload.email).lower(),
                existing_user_id=existing.id,
                role=existing.role,
            )
            return RegisterResponse(
                registration_status=existing.registration_status,
                message="Registration submitted successfully.",
                notification_email_sent=False,
            )

        user = User(
            name=f"{payload.first_name} {payload.last_name}".strip(),
            first_name=payload.first_name.strip(),
            last_name=payload.last_name.strip(),
            email=str(payload.email).lower(),
            role="user",
            is_active=True,
            password_hash=self._hash_password(payload.password),
            registration_status="pending_approval",
            two_factor_enabled=False,
            ai_profiling_consent=payload.ai_profiling_consent,
            gdpr_consent=payload.gdpr_consent,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        notification_email_sent = self.email_service.send_registration_received_email(user.email, user.first_name)
        self._notify_admins_about_registration_request(user)
        self._log_auth_event(
            "auth_registration_submitted",
            user_id=user.id,
            email=user.email,
            role=user.role,
            registration_status=user.registration_status,
        )

        return RegisterResponse(
            registration_status="pending_approval",
            message="Registration submitted successfully.",
            notification_email_sent=notification_email_sent,
        )

    def _notify_admins_about_registration_request(self, user: User) -> None:
        for recipient_email in self._admin_notification_recipients():
            self.email_service.send_admin_registration_request_email(
                recipient_email,
                user_full_name=user.name,
                user_email=user.email,
            )

    def _admin_notification_recipients(self) -> list[str]:
        statement = select(User.email).where(
            User.role == "admin",
            User.is_active.is_(True),
            User.registration_status == "approved",
        )
        emails = self.db.execute(statement).scalars().all()
        return sorted({str(email).strip().lower() for email in emails if email})

    def login(self, payload: LoginRequest, *, client_ip: str | None = None) -> LoginResponse | LoginTwoFactorResponse:
        self._enforce_rate_limit(
            category="login",
            subject=str(payload.email).lower(),
            client_ip=client_ip,
            limit=settings.auth_login_rate_limit_attempts,
        )
        user = self._get_user_by_email(payload.email)

        verification = (
            verify_password(payload.password, user.password_hash)
            if user is not None and user.password_hash
            else None
        )
        if user is None or verification is None or not verification.valid:
            self._log_auth_event(
                "auth_login_failed",
                email=str(payload.email).lower(),
                client_ip=client_ip,
                reason="invalid_credentials",
            )
            raise AuthServiceError(
                status_code=401,
                code="INVALID_CREDENTIALS",
                message="Email or password is incorrect.",
            )

        if verification.needs_rehash:
            user.password_hash = hash_password(payload.password)
            self.db.commit()
            self.db.refresh(user)
            self._log_auth_event(
                "auth_password_rehashed",
                user_id=user.id,
                email=user.email,
                scheme="argon2id",
            )

        if not user.is_active:
            self._log_auth_event(
                "auth_login_failed",
                user_id=user.id,
                email=user.email,
                client_ip=client_ip,
                reason="account_disabled",
            )
            raise AuthServiceError(
                status_code=403,
                code="ACCOUNT_DISABLED",
                message="This account is disabled.",
            )

        if user.registration_status == "pending_approval":
            self._log_auth_event(
                "auth_login_failed",
                user_id=user.id,
                email=user.email,
                client_ip=client_ip,
                reason="pending_approval",
            )
            raise AuthServiceError(
                status_code=403,
                code="ACCOUNT_PENDING_APPROVAL",
                message="This account is pending approval.",
            )

        if user.registration_status == "rejected":
            self._log_auth_event(
                "auth_login_failed",
                user_id=user.id,
                email=user.email,
                client_ip=client_ip,
                reason="account_rejected",
            )
            raise AuthServiceError(
                status_code=403,
                code="ACCOUNT_REJECTED",
                message="This account has been rejected.",
            )

        if self._requires_two_factor(user):
            trusted_device = self._get_valid_trusted_device(user)
            if trusted_device is not None:
                trusted_device.last_used_at = self._now_utc()
                self.db.commit()
                self._set_authenticated_user(user.id)
                self._reset_rate_limit("login", str(payload.email).lower(), client_ip=client_ip)
                self._log_auth_event(
                    "auth_trusted_device_accepted",
                    user_id=user.id,
                    email=user.email,
                    client_ip=client_ip,
                    role=user.role,
                )
                self._log_auth_event(
                    "auth_login_succeeded",
                    user_id=user.id,
                    email=user.email,
                    client_ip=client_ip,
                    role=user.role,
                    two_factor_skipped="trusted_device",
                )
                return LoginResponse(user=self._serialize_user(user), message="Login successful.")

            pending = self._create_pending_two_factor_challenge(
                user=user,
                setup_required=not self._has_configured_totp(user),
            )
            self.session_data.pop("user_id", None)
            self._log_auth_event(
                "auth_2fa_challenge_issued",
                user_id=user.id,
                email=user.email,
                client_ip=client_ip,
                setup_required=bool(pending["setup_required"]),
                role=user.role,
            )

            return LoginTwoFactorResponse(
                challenge_id=str(pending["challenge_id"]),
                setup_required=bool(pending["setup_required"]),
                remember_device_days=self._trusted_device_days_for_role(user.role),
                user=self._serialize_user(user),
                redirect_to=self._resolve_dashboard_path(user.role),
                message=(
                    "Two-factor setup is required before continuing."
                    if pending["setup_required"]
                    else "Two-factor verification required."
                ),
            )

        self._set_authenticated_user(user.id)
        self._reset_rate_limit("login", str(payload.email).lower(), client_ip=client_ip)
        self._log_auth_event(
            "auth_login_succeeded",
            user_id=user.id,
            email=user.email,
            client_ip=client_ip,
            role=user.role,
        )
        return LoginResponse(user=self._serialize_user(user), message="Login successful.")

    def begin_two_factor_setup(self, challenge_id: str | None) -> TwoFactorSetupResponse:
        user, pending = self._resolve_two_factor_subject(challenge_id, require_setup=True)

        existing_setup = self.session_data.get("pending_2fa_setup") or {}
        if existing_setup.get("user_id") == user.id:
            secret = str(existing_setup["secret"])
        else:
            secret = pyotp.random_base32()
            self.session_data["pending_2fa_setup"] = {
                "user_id": user.id,
                "challenge_id": pending.get("challenge_id") if pending else None,
                "secret": secret,
                "issued_at": int(time()),
            }

        return TwoFactorSetupResponse(
            challenge_id=pending.get("challenge_id") if pending else None,
            secret=secret,
            provisioning_uri=self._build_totp_provisioning_uri(user, secret),
            account_name=user.email,
            issuer=settings.app_public_name,
            message="Authenticator setup details generated.",
        )

    def confirm_two_factor(
        self,
        verification_code: str,
        challenge_id: str | None,
        remember_device: bool = False,
        *,
        client_ip: str | None = None,
    ) -> TwoFactorConfirmResponse:
        user, pending = self._resolve_two_factor_subject(challenge_id, require_setup=True)
        setup_state = self.session_data.get("pending_2fa_setup")
        if not setup_state or setup_state.get("user_id") != user.id:
            raise AuthServiceError(
                status_code=400,
                code="TWO_FACTOR_SETUP_NOT_STARTED",
                message="Two-factor setup has not been started.",
            )

        self._enforce_rate_limit(
            category="two_factor",
            subject=f"setup:{user.id}",
            client_ip=client_ip,
            limit=settings.auth_2fa_rate_limit_attempts,
        )

        secret = str(setup_state["secret"])
        if not self._verify_totp_code(secret, verification_code):
            self._log_auth_event(
                "auth_2fa_setup_failed",
                user_id=user.id,
                email=user.email,
                client_ip=client_ip,
                reason="invalid_code",
            )
            raise AuthServiceError(
                status_code=422,
                code="INVALID_VERIFICATION_CODE",
                message="Invalid verification code.",
            )

        user.totp_secret_encrypted = self._encrypt_totp_secret(secret)
        user.two_factor_method = "totp"
        user.two_factor_enabled = True
        recovery_codes = self._generate_recovery_codes()
        user.recovery_codes_hashes = self._serialize_recovery_code_hashes(recovery_codes)
        user.two_factor_confirmed_at = self._now_utc()
        self.db.commit()
        self.db.refresh(user)

        self.session_data.pop("pending_2fa_setup", None)
        self._reset_rate_limit("two_factor", f"setup:{user.id}", client_ip=client_ip)
        self._maybe_issue_trusted_device(user, remember_device)
        self._log_auth_event(
            "auth_2fa_enabled",
            user_id=user.id,
            email=user.email,
            client_ip=client_ip,
            method="totp",
            remembered_device=bool(remember_device and self.trusted_device_cookie_to_set),
        )

        redirect_to = self._resolve_dashboard_path(user.role)
        if pending:
            self._set_authenticated_user(user.id)
            return TwoFactorConfirmResponse(
                user=self._serialize_user(user),
                redirect_to=redirect_to,
                recovery_codes=recovery_codes,
                message="Two-factor authentication enabled and login completed.",
            )

        return TwoFactorConfirmResponse(
            user=self._serialize_user(user),
            redirect_to=redirect_to,
            recovery_codes=recovery_codes,
            message="Two-factor authentication enabled.",
        )

    def verify_two_factor(
        self,
        verification_code: str,
        challenge_id: str | None,
        remember_device: bool = False,
        *,
        client_ip: str | None = None,
    ) -> LoginResponse:
        user, pending = self._resolve_pending_login_challenge(challenge_id, require_setup=False)
        self._enforce_rate_limit(
            category="two_factor",
            subject=str(user.id),
            client_ip=client_ip,
            limit=settings.auth_2fa_rate_limit_attempts,
        )

        secret = self._get_decrypted_totp_secret(user)
        verified_with_recovery = False
        if secret and self._verify_totp_code(secret, verification_code):
            pass
        elif self._consume_recovery_code(user, verification_code):
            verified_with_recovery = True
            self.db.commit()
            self.db.refresh(user)
        else:
            self._log_auth_event(
                "auth_2fa_verify_failed",
                user_id=user.id,
                email=user.email,
                client_ip=client_ip,
                reason="invalid_code",
            )
            raise AuthServiceError(
                status_code=422,
                code="INVALID_VERIFICATION_CODE",
                message="Invalid verification code.",
            )

        self._set_authenticated_user(user.id)
        self._maybe_issue_trusted_device(user, remember_device)
        self._reset_rate_limit("two_factor", str(user.id), client_ip=client_ip)
        self._reset_rate_limit("login", user.email.lower(), client_ip=client_ip)
        self._log_auth_event(
            "auth_2fa_verify_succeeded",
            user_id=user.id,
            email=user.email,
            client_ip=client_ip,
            method="recovery_code" if verified_with_recovery else "totp",
            remembered_device=bool(remember_device and self.trusted_device_cookie_to_set),
        )
        return LoginResponse(
            user=self._serialize_user(user),
            message=(
                "Recovery code accepted. Two-factor verification successful."
                if verified_with_recovery
                else "Two-factor verification successful."
            ),
        )

    def regenerate_recovery_codes(self) -> TwoFactorRecoveryCodesResponse:
        user = self._require_authenticated_user()
        if not self._has_configured_totp(user):
            raise AuthServiceError(
                status_code=409,
                code="TWO_FACTOR_SETUP_REQUIRED",
                message="Two-factor setup must be completed before regenerating recovery codes.",
            )

        recovery_codes = self._generate_recovery_codes()
        user.recovery_codes_hashes = self._serialize_recovery_code_hashes(recovery_codes)
        self.db.commit()
        self.db.refresh(user)
        self._log_auth_event(
            "auth_recovery_codes_regenerated",
            user_id=user.id,
            email=user.email,
        )
        return TwoFactorRecoveryCodesResponse(
            recovery_codes=recovery_codes,
            recovery_codes_remaining=len(recovery_codes),
            message="Recovery codes regenerated successfully.",
        )

    def logout(self) -> LogoutResponse:
        self.session_data.pop("user_id", None)
        self.session_data.pop("pending_2fa", None)
        self.session_data.pop("pending_2fa_setup", None)
        return LogoutResponse(message="Logout successful.")

    def get_current_user(self) -> CurrentUserResponse:
        return CurrentUserResponse(user=self._serialize_user(self._require_authenticated_user()))

    def update_current_user(self, payload: CurrentUserUpdateRequest) -> CurrentUserResponse:
        user = self._require_authenticated_user()
        updates = payload.model_dump(exclude_unset=True)
        if "first_name" in updates:
            user.first_name = updates["first_name"].strip()
        if "last_name" in updates:
            user.last_name = updates["last_name"].strip()
        if "email" in updates:
            normalized_email = str(updates["email"]).strip().lower()
            existing = self._get_user_by_email(normalized_email)
            if existing is not None and existing.id != user.id:
                raise AuthServiceError(
                    status_code=409,
                    code="EMAIL_ALREADY_EXISTS",
                    message="That email address is already in use.",
                )
            user.email = normalized_email
        if "ai_profiling_consent" in updates:
            user.ai_profiling_consent = bool(updates["ai_profiling_consent"])
            user.profiling_opt_out_requested = not user.ai_profiling_consent
        if "gdpr_consent" in updates:
            user.gdpr_consent = bool(updates["gdpr_consent"])

        user.name = f"{user.first_name} {user.last_name}".strip() or user.email

        self.db.commit()
        self.db.refresh(user)

        return CurrentUserResponse(user=self._serialize_user(user))

    def change_password(
        self,
        *,
        current_password: str,
        new_password: str,
        new_password_confirmation: str,
    ) -> PasswordResetResponse:
        user = self._require_authenticated_user()

        if new_password != new_password_confirmation:
            raise AuthServiceError(
                status_code=422,
                code="VALIDATION_ERROR",
                message="Password confirmation must match the new password.",
            )

        verification = verify_password(current_password, user.password_hash) if user.password_hash else None
        if verification is None or not verification.valid:
            raise AuthServiceError(
                status_code=401,
                code="INVALID_CURRENT_PASSWORD",
                message="Current password is incorrect.",
            )

        user.password_hash = self._hash_password(new_password)
        self._invalidate_trusted_devices(user.id)
        self.clear_trusted_device_cookie = True
        self.db.commit()
        self.db.refresh(user)
        self._log_auth_event(
            "auth_password_changed",
            user_id=user.id,
            email=user.email,
        )
        return PasswordResetResponse(message="Password changed successfully.")

    def request_password_reset(self, email: str) -> PasswordResetResponse:
        normalized_email = str(email).lower()
        user = self._get_user_by_email(normalized_email)
        if user is not None:
            raw_token = secrets.token_urlsafe(32)
            token = PasswordResetToken(
                user_id=user.id,
                token_hash=self._hash_reset_token(raw_token),
                expires_at=self._now_utc() + timedelta(seconds=settings.auth_password_reset_ttl_seconds),
            )
            self.db.add(token)
            self.db.commit()
            reset_link = self._build_password_reset_link(raw_token)
            self.email_service.send_password_reset_email(
                user.email,
                user.first_name or user.name or "there",
                reset_link,
            )
            self._log_auth_event(
                "auth_password_reset_requested",
                user_id=user.id,
                email=user.email,
            )
        else:
            self._log_auth_event(
                "auth_password_reset_requested",
                email=normalized_email,
                user_id=None,
            )

        return PasswordResetResponse(
            message="If an account exists for that email, a password reset message will be sent."
        )

    def confirm_password_reset(self, token: str, password: str, password_confirmation: str) -> PasswordResetResponse:
        if password != password_confirmation:
            raise AuthServiceError(
                status_code=422,
                code="VALIDATION_ERROR",
                message="Password confirmation must match the password.",
            )

        token_record = self._get_password_reset_token(token)
        if token_record is None or token_record.used_at is not None or self._is_password_reset_token_expired(token_record):
            self._log_auth_event("auth_password_reset_failed", reason="invalid_or_expired_token")
            raise AuthServiceError(
                status_code=400,
                code="PASSWORD_RESET_TOKEN_INVALID",
                message="Password reset token is invalid or has expired.",
            )

        user = self.db.get(User, token_record.user_id)
        if user is None:
            self._log_auth_event("auth_password_reset_failed", reason="user_not_found")
            raise AuthServiceError(
                status_code=404,
                code="USER_NOT_FOUND",
                message="User for the password reset token was not found.",
            )

        user.password_hash = self._hash_password(password)
        self._invalidate_trusted_devices(user.id)
        token_record.used_at = self._now_utc()
        self.db.commit()
        self._log_auth_event(
            "auth_password_reset_completed",
            user_id=user.id,
            email=user.email,
        )
        return PasswordResetResponse(message="Password reset successful.")

    def _ensure_email_available(self, email: str) -> None:
        existing = self._get_user_by_email(email)
        if existing is not None:
            raise AuthServiceError(
                status_code=409,
                code="EMAIL_ALREADY_EXISTS",
                message="An account with this email already exists.",
            )

    def _get_user_by_email(self, email: str) -> User | None:
        if self.db is None:
            return None

        statement = select(User).where(User.email == str(email).lower())
        return self.db.execute(statement).scalar_one_or_none()

    def _get_password_reset_token(self, raw_token: str) -> PasswordResetToken | None:
        if self.db is None:
            return None
        statement = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == self._hash_reset_token(raw_token)
        )
        return self.db.execute(statement).scalar_one_or_none()

    def _serialize_user(self, user: User) -> AuthUserResponse:
        if not user.first_name and user.name:
            parts = user.name.split(" ", 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ""

        payload = AuthUserResponse.model_validate(user).model_dump()
        payload["recovery_codes_remaining"] = self._count_recovery_codes(user)
        return AuthUserResponse.model_validate(payload)

    def _set_authenticated_user(self, user_id: int) -> None:
        self.session_data["user_id"] = user_id
        self.session_data.pop("pending_2fa", None)
        self.session_data.pop("pending_2fa_setup", None)

    def _trusted_device_days_for_role(self, role: str) -> int:
        return settings.auth_trusted_device_days_for_role(role)

    def _get_valid_trusted_device(self, user: User) -> TrustedDevice | None:
        remember_days = self._trusted_device_days_for_role(user.role)
        if remember_days <= 0 or self.db is None:
            return None

        raw_token = self.request_cookies.get(settings.auth_trusted_device_cookie_name)
        if not raw_token:
            return None

        token_hash = self._hash_trusted_device_token(raw_token)
        statement = select(TrustedDevice).where(
            TrustedDevice.user_id == user.id,
            TrustedDevice.token_hash == token_hash,
        )
        device = self.db.execute(statement).scalar_one_or_none()
        if device is None:
            self.clear_trusted_device_cookie = True
            return None

        if self._is_trusted_device_expired(device):
            self.db.delete(device)
            self.db.commit()
            self.clear_trusted_device_cookie = True
            return None

        expected_user_agent_hash = self._hash_user_agent()
        if device.user_agent_hash and expected_user_agent_hash and device.user_agent_hash != expected_user_agent_hash:
            self.clear_trusted_device_cookie = True
            return None

        return device

    def _require_authenticated_user(self) -> User:
        user_id = self.session_data.get("user_id")
        if not user_id:
            raise AuthServiceError(
                status_code=401,
                code="NOT_AUTHENTICATED",
                message="No active session.",
            )

        user = self.db.get(User, user_id)
        if user is None:
            self.session_data.pop("user_id", None)
            raise AuthServiceError(
                status_code=401,
                code="NOT_AUTHENTICATED",
                message="No active session.",
            )

        return user

    def _requires_two_factor(self, user: User) -> bool:
        return self._is_mandatory_two_factor_role(user.role) or user.two_factor_enabled

    def _has_configured_totp(self, user: User) -> bool:
        return bool(user.totp_secret_encrypted and user.two_factor_confirmed_at and user.two_factor_method == "totp")

    def _is_mandatory_two_factor_role(self, role: str) -> bool:
        return role in {"admin", "expert"}

    def _resolve_dashboard_path(self, role: str) -> str:
        if role == "expert":
            return "/expert"
        if role == "admin":
            return "/admin"
        return "/user"

    def _hash_password(self, password: str) -> str:
        return hash_password(password)

    def _verify_password(self, password: str, stored_value: str) -> bool:
        return verify_password(password, stored_value).valid

    def _create_pending_two_factor_challenge(self, *, user: User, setup_required: bool) -> dict[str, Any]:
        challenge_id = str(uuid4())
        pending = {
            "challenge_id": challenge_id,
            "user_id": user.id,
            "redirect_to": self._resolve_dashboard_path(user.role),
            "setup_required": setup_required,
            "issued_at": int(time()),
        }
        self.session_data["pending_2fa"] = pending
        self.session_data.pop("pending_2fa_setup", None)
        return pending

    def _maybe_issue_trusted_device(self, user: User, remember_device: bool) -> None:
        self.trusted_device_cookie_to_set = None
        if not remember_device or self.db is None:
            return

        remember_days = self._trusted_device_days_for_role(user.role)
        if remember_days <= 0:
            return

        raw_token = secrets.token_urlsafe(32)
        expires_at = self._now_utc() + timedelta(days=remember_days)
        device = TrustedDevice(
            user_id=user.id,
            token_hash=self._hash_trusted_device_token(raw_token),
            user_agent_hash=self._hash_user_agent(),
            expires_at=expires_at,
            last_used_at=self._now_utc(),
        )
        self.db.add(device)
        self.db.commit()
        self.trusted_device_cookie_to_set = {
            "value": raw_token,
            "max_age": int(timedelta(days=remember_days).total_seconds()),
            "expires_at": expires_at,
        }

    def _hash_trusted_device_token(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def _hash_user_agent(self) -> str | None:
        normalized = self.user_agent.strip()
        if not normalized:
            return None
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _is_trusted_device_expired(self, device: TrustedDevice) -> bool:
        expires_at = device.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return expires_at <= self._now_utc()

    def _invalidate_trusted_devices(self, user_id: int) -> None:
        if self.db is None:
            return

        statement = select(TrustedDevice).where(TrustedDevice.user_id == user_id)
        for device in self.db.execute(statement).scalars().all():
            self.db.delete(device)

    def _resolve_two_factor_subject(
        self,
        challenge_id: str | None,
        *,
        require_setup: bool,
    ) -> tuple[User, dict[str, Any] | None]:
        user_id = self.session_data.get("user_id")
        if user_id:
            user = self.db.get(User, user_id)
            if user is None:
                self.session_data.pop("user_id", None)
                raise AuthServiceError(
                    status_code=401,
                    code="NOT_AUTHENTICATED",
                    message="No active session.",
                )
            if user.two_factor_enabled and self._has_configured_totp(user):
                raise AuthServiceError(
                    status_code=409,
                    code="TWO_FACTOR_ALREADY_ENABLED",
                    message="Two-factor authentication is already enabled.",
                )
            return user, None

        user, pending = self._resolve_pending_login_challenge(challenge_id, require_setup=require_setup)
        return user, pending

    def _resolve_pending_login_challenge(
        self,
        challenge_id: str | None,
        *,
        require_setup: bool | None,
    ) -> tuple[User, dict[str, Any]]:
        pending = self.session_data.get("pending_2fa")
        if not pending:
            raise AuthServiceError(
                status_code=400,
                code="TWO_FACTOR_NOT_STARTED",
                message="No pending two-factor challenge was found.",
            )

        if challenge_id and pending.get("challenge_id") != challenge_id:
            self.session_data.pop("pending_2fa", None)
            self.session_data.pop("pending_2fa_setup", None)
            raise AuthServiceError(
                status_code=400,
                code="TWO_FACTOR_CHALLENGE_EXPIRED",
                message="Two-factor challenge is invalid or has expired.",
            )

        if self._is_pending_two_factor_expired(pending):
            self.session_data.pop("pending_2fa", None)
            self.session_data.pop("pending_2fa_setup", None)
            raise AuthServiceError(
                status_code=400,
                code="TWO_FACTOR_CHALLENGE_EXPIRED",
                message="Two-factor challenge is invalid or has expired.",
            )

        if require_setup is True and not pending.get("setup_required"):
            raise AuthServiceError(
                status_code=409,
                code="TWO_FACTOR_SETUP_NOT_REQUIRED",
                message="Two-factor setup is not required for this login challenge.",
            )

        if require_setup is False and pending.get("setup_required"):
            raise AuthServiceError(
                status_code=409,
                code="TWO_FACTOR_SETUP_REQUIRED",
                message="Two-factor setup must be completed before verification.",
            )

        user = self.db.get(User, pending.get("user_id"))
        if user is None:
            self.session_data.pop("pending_2fa", None)
            self.session_data.pop("pending_2fa_setup", None)
            raise AuthServiceError(
                status_code=404,
                code="USER_NOT_FOUND",
                message="User for the two-factor challenge was not found.",
            )

        return user, pending

    def _is_pending_two_factor_expired(self, pending: dict[str, Any]) -> bool:
        issued_at = int(pending.get("issued_at") or 0)
        return issued_at + settings.auth_2fa_challenge_ttl_seconds < int(time())

    def _build_totp_provisioning_uri(self, user: User, secret: str) -> str:
        issuer = settings.app_public_name
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=user.email, issuer_name=issuer)

    def _verify_totp_code(self, secret: str, verification_code: str) -> bool:
        totp = pyotp.TOTP(secret)
        return bool(totp.verify(verification_code.strip(), valid_window=1))

    def _encrypt_totp_secret(self, secret: str) -> str:
        token = self._get_fernet().encrypt(secret.encode("utf-8"))
        return token.decode("utf-8")

    def _get_decrypted_totp_secret(self, user: User) -> str | None:
        if not user.totp_secret_encrypted:
            return None

        try:
            value = self._get_fernet().decrypt(user.totp_secret_encrypted.encode("utf-8"))
        except InvalidToken as exc:
            raise AuthServiceError(
                status_code=500,
                code="TWO_FACTOR_CONFIGURATION_INVALID",
                message="Stored two-factor configuration is invalid.",
            ) from exc

        return value.decode("utf-8")

    def _generate_recovery_codes(self, count: int = 8) -> list[str]:
        codes: list[str] = []
        for _ in range(count):
            value = secrets.token_hex(4).upper()
            codes.append(f"{value[:4]}-{value[4:]}")
        return codes

    def _hash_recovery_code(self, code: str) -> str:
        normalized = code.replace("-", "").strip().upper()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _serialize_recovery_code_hashes(self, codes: list[str]) -> str:
        return json.dumps([self._hash_recovery_code(code) for code in codes])

    def _deserialize_recovery_code_hashes(self, raw_value: str | None) -> list[str]:
        if not raw_value:
            return []
        try:
            decoded = json.loads(raw_value)
        except json.JSONDecodeError:
            return []
        if not isinstance(decoded, list):
            return []
        return [str(item) for item in decoded]

    def _count_recovery_codes(self, user: User) -> int:
        return len(self._deserialize_recovery_code_hashes(user.recovery_codes_hashes))

    def _consume_recovery_code(self, user: User, verification_code: str) -> bool:
        hashes = self._deserialize_recovery_code_hashes(user.recovery_codes_hashes)
        hashed_code = self._hash_recovery_code(verification_code)
        if hashed_code not in hashes:
            return False
        hashes.remove(hashed_code)
        user.recovery_codes_hashes = json.dumps(hashes)
        return True

    def _get_fernet(self) -> Fernet:
        key_bytes = hashlib.sha256(settings.auth_session_secret.encode("utf-8")).digest()
        return Fernet(base64.urlsafe_b64encode(key_bytes))

    def _enforce_rate_limit(
        self,
        *,
        category: str,
        subject: str,
        client_ip: str | None,
        limit: int,
    ) -> None:
        keys = [self._rate_limit_key(category, subject)]
        if client_ip:
            keys.append(self._rate_limit_key(category, f"ip:{client_ip}"))

        for key in keys:
            allowed, retry_after = auth_rate_limiter.check(
                key,
                limit=limit,
                window_seconds=settings.auth_rate_limit_window_seconds,
            )
            if not allowed:
                self._log_auth_event(
                    "auth_rate_limited",
                    category=category,
                    subject=subject,
                    client_ip=client_ip,
                    retry_after_seconds=retry_after,
                )
                raise AuthServiceError(
                    status_code=429,
                    code="RATE_LIMITED",
                    message="Too many authentication attempts. Try again later.",
                    details={"retry_after_seconds": retry_after},
                )

    def _reset_rate_limit(self, category: str, subject: str, *, client_ip: str | None) -> None:
        auth_rate_limiter.reset(self._rate_limit_key(category, subject))
        if client_ip:
            auth_rate_limiter.reset(self._rate_limit_key(category, f"ip:{client_ip}"))

    def _rate_limit_key(self, category: str, subject: str) -> str:
        return f"{category}:{subject}"

    def _now_utc(self):
        return datetime.now(timezone.utc)

    def _hash_reset_token(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def _build_password_reset_link(self, raw_token: str) -> str:
        reset_base_url = settings.auth_password_reset_base_url
        if not reset_base_url and not settings.is_production:
            reset_base_url = "http://localhost:5173/reset-password"

        if reset_base_url:
            separator = "&" if "?" in reset_base_url else "?"
            return f"{reset_base_url}{separator}token={raw_token}"
        return f"token:{raw_token}"

    def _log_auth_event(self, event: str, **fields: Any) -> None:
        log_event(logger, event, **fields)

    def _is_password_reset_token_expired(self, token_record: PasswordResetToken) -> bool:
        expires_at = token_record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return expires_at <= self._now_utc()
