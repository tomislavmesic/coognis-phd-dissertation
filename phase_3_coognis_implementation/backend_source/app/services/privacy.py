from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import DataRequest, User
from app.schemas.privacy import (
    AccountDeletionRequestCreate,
    AdminDataRequestActionResponse,
    AdminDataRequestItemResponse,
    ConsentUpdateRequest,
    PrivacyActionResponse,
)
from app.services.email import EmailService


class PrivacyService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.email_service = EmailService()

    def update_consent_settings(self, user_id: int, payload: ConsentUpdateRequest) -> PrivacyActionResponse:
        user = self._get_user(user_id)
        profiling_withdrawn = False

        if payload.ai_profiling_consent is False and user.ai_profiling_consent:
            user.ai_profiling_consent = False
            user.profiling_opt_out_requested = True
            profiling_withdrawn = True
            self._create_or_refresh_request(
                user_id=user.id,
                request_type="profiling_opt_out",
                reason="user_withdrew_ai_profiling_consent",
            )

        self.db.commit()
        self.db.refresh(user)
        if profiling_withdrawn:
            self._notify_admins_about_profiling_withdrawal(user)
        return self._build_privacy_response(user, "Consent settings updated successfully.")

    def request_account_deletion(self, user_id: int, payload: AccountDeletionRequestCreate) -> PrivacyActionResponse:
        user = self._get_user(user_id)
        user.account_deletion_requested = True
        self._create_or_refresh_request(
            user_id=user.id,
            request_type="account_deletion",
            reason=payload.reason,
        )
        self.db.commit()
        self.db.refresh(user)
        self._notify_admins_about_account_deletion_request(user, payload.reason)
        return self._build_privacy_response(user, "Account deletion request submitted successfully.")

    def list_data_requests(self) -> list[AdminDataRequestItemResponse]:
        statement = (
            select(DataRequest)
            .options(joinedload(DataRequest.user))
            .order_by(DataRequest.created_at.desc(), DataRequest.id.desc())
        )
        items = self.db.execute(statement).scalars().all()
        return [
            AdminDataRequestItemResponse(
                id=item.id,
                request_type=item.request_type,
                status=item.status,
                reason=item.reason,
                user_id=item.user_id,
                full_name=item.user.name,
                email=item.user.email,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            for item in items
        ]

    def get_data_request(self, request_id: int) -> AdminDataRequestItemResponse:
        item = self._get_data_request(request_id)
        return AdminDataRequestItemResponse(
            id=item.id,
            request_type=item.request_type,
            status=item.status,
            reason=item.reason,
            user_id=item.user_id,
            full_name=item.user.name,
            email=item.user.email,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    def complete_data_request(self, request_id: int) -> AdminDataRequestActionResponse:
        item = self._get_data_request(request_id)
        item.status = "completed"
        self._sync_user_flags_for_request(item, completed=True)
        self.db.commit()
        return AdminDataRequestActionResponse(request_id=item.id, status=item.status)

    def reject_data_request(self, request_id: int) -> AdminDataRequestActionResponse:
        item = self._get_data_request(request_id)
        item.status = "rejected"
        self._sync_user_flags_for_request(item, completed=False)
        self.db.commit()
        return AdminDataRequestActionResponse(request_id=item.id, status=item.status)

    def _create_or_refresh_request(self, *, user_id: int, request_type: str, reason: str | None) -> DataRequest:
        statement = select(DataRequest).where(
            DataRequest.user_id == user_id,
            DataRequest.request_type == request_type,
            DataRequest.status == "pending",
        )
        existing = self.db.execute(statement).scalar_one_or_none()
        if existing is not None:
            existing.reason = reason
            return existing

        item = DataRequest(
            user_id=user_id,
            request_type=request_type,
            status="pending",
            reason=reason,
        )
        self.db.add(item)
        return item

    def _sync_user_flags_for_request(self, item: DataRequest, *, completed: bool) -> None:
        user = item.user or self._get_user(item.user_id)

        if item.request_type == "profiling_opt_out":
            user.profiling_opt_out_requested = False
            if not completed:
                user.ai_profiling_consent = True
        elif item.request_type == "account_deletion":
            user.account_deletion_requested = False if not completed else True

    def _notify_admins_about_profiling_withdrawal(self, user: User) -> None:
        for recipient_email in self._admin_notification_recipients():
            self.email_service.send_admin_profiling_withdrawal_request_email(
                recipient_email,
                user_full_name=user.name,
                user_email=user.email,
            )

    def _notify_admins_about_account_deletion_request(self, user: User, reason: str | None) -> None:
        for recipient_email in self._admin_notification_recipients():
            self.email_service.send_admin_account_deletion_request_email(
                recipient_email,
                user_full_name=user.name,
                user_email=user.email,
                reason=reason,
            )

    def _admin_notification_recipients(self) -> list[str]:
        statement = select(User.email).where(
            User.role == "admin",
            User.is_active.is_(True),
            User.registration_status == "approved",
        )
        emails = self.db.execute(statement).scalars().all()
        return sorted({str(email).strip().lower() for email in emails if email})

    def _get_user(self, user_id: int) -> User:
        user = self.db.get(User, user_id)
        if user is None:
            raise LookupError("User not found.")
        return user

    def _get_data_request(self, request_id: int) -> DataRequest:
        statement = select(DataRequest).options(joinedload(DataRequest.user)).where(DataRequest.id == request_id)
        item = self.db.execute(statement).scalar_one_or_none()
        if item is None:
            raise LookupError("Data request not found.")
        return item

    @staticmethod
    def _build_privacy_response(user: User, message: str) -> PrivacyActionResponse:
        return PrivacyActionResponse(
            message=message,
            ai_profiling_consent=user.ai_profiling_consent,
            gdpr_consent=user.gdpr_consent,
            profiling_opt_out_requested=user.profiling_opt_out_requested,
            account_deletion_requested=user.account_deletion_requested,
        )
