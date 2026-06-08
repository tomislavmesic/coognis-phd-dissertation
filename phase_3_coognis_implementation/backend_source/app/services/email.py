from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.core.config import settings
from app.core.logging import get_logger, log_event

logger = get_logger("email")


class EmailService:
    def __init__(self) -> None:
        self.delivery_mode = settings.email_delivery_mode.lower()
        self.from_address = settings.email_from_address
        self.brand_name = settings.app_public_name

    def send_registration_received_email(self, recipient_email: str, first_name: str) -> bool:
        subject = f"{self.brand_name} registration received"
        body = (
            f"Hello {first_name},\n\n"
            "Your registration has been received and is pending admin approval.\n"
            f"You will be notified once your account is approved.\n\n{self.brand_name}"
        )
        return self._send_email(recipient_email, subject, body, event="registration_received_email")

    def send_account_created_email(
        self,
        recipient_email: str,
        first_name: str,
        role: str,
        temporary_password: str,
    ) -> bool:
        subject = f"Your {self.brand_name} account has been created"
        body = (
            f"Hello {first_name},\n\n"
            f"An administrator created your {self.brand_name} {role} account.\n"
            f"Login email: {recipient_email}\n"
            f"Temporary password: {temporary_password}\n\n"
            f"Please sign in and change your password as soon as possible.\n\n{self.brand_name}"
        )
        return self._send_email(recipient_email, subject, body, event="account_created_email")

    def send_registration_approved_email(self, recipient_email: str, first_name: str, role: str) -> bool:
        subject = f"Your {self.brand_name} account has been approved"
        body = (
            f"Hello {first_name},\n\n"
            f"Your {self.brand_name} {role} account has been approved and is now active.\n"
            f"You can now sign in with the password you chose during registration.\n\n{self.brand_name}"
        )
        return self._send_email(recipient_email, subject, body, event="registration_approved_email")

    def send_password_reset_email(self, recipient_email: str, first_name: str, reset_link: str) -> bool:
        subject = f"Reset your {self.brand_name} password"
        body = (
            f"Hello {first_name},\n\n"
            f"A password reset request was received for your {self.brand_name} account.\n"
            f"Use this link to set a new password: {reset_link}\n\n"
            f"If you did not request this reset, you can ignore this email.\n\n{self.brand_name}"
        )
        return self._send_email(recipient_email, subject, body, event="password_reset_email")

    def send_admin_registration_request_email(
        self,
        recipient_email: str,
        *,
        user_full_name: str,
        user_email: str,
    ) -> bool:
        subject = f"New {self.brand_name} registration request"
        body = (
            "Hello,\n\n"
            f"A new user registration request has been submitted in {self.brand_name}.\n"
            f"Name: {user_full_name}\n"
            f"Email: {user_email}\n\n"
            "Review the request in the admin registration approvals queue.\n\n"
            f"{self.brand_name}"
        )
        return self._send_email(recipient_email, subject, body, event="admin_registration_request_email")

    def send_admin_profiling_withdrawal_request_email(
        self,
        recipient_email: str,
        *,
        user_full_name: str,
        user_email: str,
    ) -> bool:
        subject = f"{self.brand_name} profiling consent withdrawal request"
        body = (
            "Hello,\n\n"
            f"A user withdrew AI profiling consent in {self.brand_name}.\n"
            f"Name: {user_full_name}\n"
            f"Email: {user_email}\n\n"
            "Review the privacy request in the admin data requests queue.\n\n"
            f"{self.brand_name}"
        )
        return self._send_email(recipient_email, subject, body, event="admin_profiling_withdrawal_request_email")

    def send_admin_account_deletion_request_email(
        self,
        recipient_email: str,
        *,
        user_full_name: str,
        user_email: str,
        reason: str | None = None,
    ) -> bool:
        subject = f"{self.brand_name} account deletion request"
        body = (
            "Hello,\n\n"
            f"A user requested full account deletion in {self.brand_name}.\n"
            f"Name: {user_full_name}\n"
            f"Email: {user_email}\n"
            f"Reason: {reason or 'No reason provided.'}\n\n"
            "Review the privacy request in the admin data requests queue.\n\n"
            f"{self.brand_name}"
        )
        return self._send_email(recipient_email, subject, body, event="admin_account_deletion_request_email")

    def send_expert_handoff_email(
        self,
        recipient_email: str,
        *,
        expert_name: str,
        user_name: str,
        session_id: int,
        session_title: str | None = None,
        reason: str | None = None,
    ) -> bool:
        subject = f"New {self.brand_name} expert handoff"
        body = (
            f"Hello {expert_name},\n\n"
            f"A user handed off a conversation to you in {self.brand_name}.\n"
            f"User: {user_name}\n"
            f"Session: #{session_id}"
            f"{f' ({session_title})' if session_title else ''}\n"
            f"Reason: {reason or 'No handoff reason provided.'}\n\n"
            "Sign in to review and continue the conversation.\n\n"
            f"{self.brand_name}"
        )
        return self._send_email(recipient_email, subject, body, event="expert_handoff_email")

    def _send_email(self, recipient_email: str, subject: str, body: str, *, event: str) -> bool:
        if self.delivery_mode == "log":
            log_event(
                logger,
                event,
                delivery_mode="log",
                to=recipient_email,
                subject=subject,
                body=body,
            )
            return False

        if self.delivery_mode != "smtp":
            log_event(
                logger,
                "email_delivery_skipped",
                delivery_mode=self.delivery_mode,
                to=recipient_email,
                subject=subject,
            )
            return False

        message = EmailMessage()
        message["From"] = self.from_address
        message["To"] = recipient_email
        message["Subject"] = subject
        message.set_content(body)

        try:
            if settings.smtp_use_tls:
                with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as smtp:
                    self._login_and_send(smtp, message)
            else:
                with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
                    smtp.ehlo()
                    if settings.smtp_use_starttls:
                        smtp.starttls()
                        smtp.ehlo()
                    self._login_and_send(smtp, message)
        except Exception as exc:  # pragma: no cover - depends on environment
            log_event(
                logger,
                "email_delivery_failed",
                delivery_mode="smtp",
                to=recipient_email,
                subject=subject,
                error=str(exc),
            )
            return False

        log_event(
            logger,
            event,
            delivery_mode="smtp",
            to=recipient_email,
            subject=subject,
        )
        return True

    def _login_and_send(self, smtp: smtplib.SMTP, message: EmailMessage) -> None:
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password or "")
        smtp.send_message(message)
