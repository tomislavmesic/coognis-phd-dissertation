from io import BytesIO
import re
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models import ChatMessage, ChatSession, DataRequest, Expert, ExpertDomain, ExpertHandoff, ExpertProfile, KnowledgeItem, KnowledgeSource, SourceDocument, TrustedDevice, User
from app.schemas.admin import (
    AdminChatSessionResponse,
    AdminConversationDetailResponse,
    AdminConversationHandoffResponse,
    AdminConversationMessageResponse,
    AdminConversationOverviewResponse,
    AdminDashboardActiveExpertResponse,
    AdminDashboardActiveUserResponse,
    AdminDashboardConsentRequestResponse,
    AdminDashboardPendingRegistrationResponse,
    AdminDashboardResponse,
    AdminDashboardStatResponse,
    BulkTwoFactorUpdateRequest,
    BulkTwoFactorUpdateResponse,
    ChatSessionDeleteResponse,
    DomainOptionResponse,
    ExpertAdminCreateRequest,
    ExpertProvisionResponse,
    ExpertAdminResponse,
    ExpertAdminUpdateRequest,
    GeneralSettingsResponse,
    GeneralSettingsUpdateRequest,
    KnowledgeAdminCreateRequest,
    KnowledgeAdminResponse,
    KnowledgeAdminUpdateRequest,
    LlmProviderOptionResponse,
    ModuleSettingsResponse,
    ModuleSettingsUpdateRequest,
    ProfileAdminCreateRequest,
    ProfileAdminResponse,
    ProfileAdminUpdateRequest,
    RegistrationApprovalActionRequest,
    RegistrationApprovalActionResponse,
    RegistrationQueueItemResponse,
    TrustedDeviceAdminResponse,
    UlmSourceAdminCreateRequest,
    UlmSourceAdminDetailResponse,
    UlmSourceAdminChunkResponse,
    UlmSourceAdminResponse,
    UlmSourceAdminUpdateRequest,
    UserCreateRequest,
    UserCredentialActionResponse,
    UserResponse,
    UserUpdateRequest,
)
from app.services.email import EmailService
from app.services.module_settings import ModuleSettingsService
from app.services.password_security import hash_password
from app.services.ulm import UlmService
from app.services.user_profile import UserProfileService


class AdminService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.email_service = EmailService()
        self.module_settings_service = ModuleSettingsService(db)
        self.user_profile_service = UserProfileService(db)

    def list_users(self) -> list[UserResponse]:
        users = self.db.query(User).options(selectinload(User.profile)).order_by(User.id).all()
        return [self._build_user_response(item) for item in users]

    def bulk_update_two_factor(self, payload: BulkTwoFactorUpdateRequest) -> BulkTwoFactorUpdateResponse:
        if payload.role not in {"user", "expert"}:
            raise ValueError("Bulk 2FA updates are only allowed for user and expert roles.")
        if payload.role == "expert" and not payload.enabled:
            raise ValueError("Two-factor authentication is mandatory for expert accounts.")

        statement = select(User).where(User.role == payload.role)
        users = self.db.execute(statement).scalars().all()

        for user in users:
            user.two_factor_enabled = payload.enabled
            if not payload.enabled:
                user.two_factor_method = None
                user.totp_secret_encrypted = None
                user.recovery_codes_hashes = None
                user.two_factor_confirmed_at = None
                self._invalidate_trusted_devices(user.id)

        self.db.commit()

        action = "enabled" if payload.enabled else "disabled"
        return BulkTwoFactorUpdateResponse(
            role=payload.role,
            enabled=payload.enabled,
            affected_count=len(users),
            message=f"Two-factor authentication {action} for all {payload.role} accounts.",
        )

    def get_dashboard_summary(self) -> AdminDashboardResponse:
        pending_users = (
            self.db.query(User)
            .filter(User.registration_status == "pending_approval")
            .order_by(User.created_at.desc(), User.id.desc())
            .limit(5)
            .all()
        )
        active_users = (
            self.db.query(User)
            .filter(User.role == "user", User.is_active.is_(True))
            .order_by(User.created_at.desc(), User.id.desc())
            .limit(5)
            .all()
        )
        active_experts = (
            self.db.query(Expert)
            .filter(Expert.is_active.is_(True))
            .order_by(Expert.created_at.desc(), Expert.id.desc())
            .limit(5)
            .all()
        )
        consent_requests = (
            self.db.query(DataRequest)
            .join(User, User.id == DataRequest.user_id)
            .order_by(DataRequest.created_at.desc(), DataRequest.id.desc())
            .limit(5)
            .all()
        )

        pending_count = self.db.execute(
            select(func.count()).select_from(User).where(User.registration_status == "pending_approval")
        ).scalar_one()
        active_user_count = self.db.execute(
            select(func.count()).select_from(User).where(User.role == "user", User.is_active.is_(True))
        ).scalar_one()
        active_expert_count = self.db.execute(
            select(func.count()).select_from(Expert).where(Expert.is_active.is_(True))
        ).scalar_one()
        open_deletion_count = self.db.execute(
            select(func.count()).select_from(DataRequest).where(
                DataRequest.request_type == "account_deletion",
                DataRequest.status == "pending",
            )
        ).scalar_one()

        return AdminDashboardResponse(
            pending_registrations=[
                AdminDashboardPendingRegistrationResponse(
                    id=user.id,
                    name=self._build_user_display_name(user),
                    role=user.role.capitalize(),
                    submitted_at=user.created_at,
                    consents=self._format_consents(user.ai_profiling_consent, user.gdpr_consent),
                )
                for user in pending_users
            ],
            system_stats=[
                AdminDashboardStatResponse(label="Pending approvals", value=pending_count),
                AdminDashboardStatResponse(label="Active users", value=active_user_count),
                AdminDashboardStatResponse(label="Active experts", value=active_expert_count),
                AdminDashboardStatResponse(label="Open deletion requests", value=open_deletion_count),
            ],
            active_users=[
                AdminDashboardActiveUserResponse(
                    id=user.id,
                    name=self._build_user_display_name(user),
                    email=user.email,
                    status="Active" if user.is_active else "Inactive",
                    two_factor="Enabled" if user.two_factor_enabled else "Disabled",
                )
                for user in active_users
            ],
            active_experts=[
                self._build_dashboard_active_expert_response(expert)
                for expert in active_experts
            ],
            consent_requests=[
                AdminDashboardConsentRequestResponse(
                    id=item.id,
                    type=item.request_type.replace("_", " ").title(),
                    submitted_by=self._build_user_display_name(item.user),
                    status=item.status.replace("_", " ").title(),
                )
                for item in consent_requests
            ],
        )

    def list_pending_registrations(self) -> list[RegistrationQueueItemResponse]:
        users = (
            self.db.query(User)
            .filter(User.registration_status == "pending_approval")
            .order_by(User.created_at.desc(), User.id.desc())
            .all()
        )

        return [
            RegistrationQueueItemResponse(
                id=user.id,
                full_name=f"{user.first_name} {user.last_name}".strip() or user.name,
                email=user.email,
                requested_role=user.role,
                ai_profiling_consent=user.ai_profiling_consent,
                gdpr_consent=user.gdpr_consent,
                created_at=user.created_at,
            )
            for user in users
        ]

    def approve_registration(
        self,
        registration_id: int,
        payload: RegistrationApprovalActionRequest,
    ) -> RegistrationApprovalActionResponse:
        user = self._get_or_raise(User, registration_id, "Registration not found.")
        user.registration_status = "approved"
        user.is_active = True
        self.db.commit()

        credentials_email_triggered = False
        if payload.send_credentials_email:
            credentials_email_triggered = self.email_service.send_registration_approved_email(
                user.email,
                user.first_name,
                user.role,
            )

        return RegistrationApprovalActionResponse(
            registration_id=user.id,
            status="approved",
            credentials_email_triggered=credentials_email_triggered,
        )

    def reject_registration(self, registration_id: int) -> RegistrationApprovalActionResponse:
        user = self._get_or_raise(User, registration_id, "Registration not found.")
        user.registration_status = "rejected"
        user.is_active = False
        self.db.commit()

        return RegistrationApprovalActionResponse(
            registration_id=user.id,
            status="rejected",
            credentials_email_triggered=False,
        )

    def create_user(self, payload: UserCreateRequest) -> UserResponse:
        if self._email_exists(payload.email):
            raise ValueError("An account with this email already exists.")

        generated_password = None
        temporary_password = payload.temporary_password

        if payload.auto_generate_password:
            generated_password = self._generate_temporary_password()
            temporary_password = generated_password

        if not temporary_password:
            raise ValueError("Temporary password is required when auto-generate is disabled.")

        user = User(
            name=f"{payload.first_name} {payload.last_name}".strip(),
            first_name=payload.first_name.strip(),
            last_name=payload.last_name.strip(),
            email=payload.email.lower(),
            role=payload.role,
            is_active=payload.is_active,
            password_hash=self._hash_password(temporary_password),
            registration_status="approved",
            two_factor_enabled=payload.role in {"admin", "expert"},
            ai_profiling_consent=payload.ai_profiling_consent_recorded,
            gdpr_consent=payload.gdpr_consent_recorded,
            profiling_opt_out_requested=False,
            account_deletion_requested=False,
            can_access_chat_debug_panels=False,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        self._sync_expert_record_for_user(user)

        credentials_email_triggered = False
        if payload.send_credentials_email:
            credentials_email_triggered = self.email_service.send_account_created_email(
                user.email,
                user.first_name,
                user.role,
                temporary_password,
            )

        response = self._build_user_response(user)
        response.generated_temporary_password = generated_password
        response.credentials_email_triggered = credentials_email_triggered
        if not credentials_email_triggered:
            response.generated_temporary_password = generated_password or temporary_password
        return response

    def get_user(self, item_id: int) -> UserResponse:
        user = self.db.query(User).options(selectinload(User.profile)).filter(User.id == item_id).one_or_none()
        if user is None:
            raise LookupError("User not found.")
        return self._build_user_response(user)

    def update_user(self, item_id: int, payload: UserUpdateRequest) -> UserResponse:
        user = self._get_or_raise(User, item_id, "User not found.")

        if payload.email and payload.email.lower() != user.email.lower() and self._email_exists(payload.email):
            raise ValueError("An account with this email already exists.")

        updates = payload.model_dump(exclude_unset=True)

        for field, value in updates.items():
            if field == "manual_mbti":
                continue
            if field in {"first_name", "last_name"}:
                setattr(user, field, value.strip() if isinstance(value, str) else value)
                continue
            if field == "email" and isinstance(value, str):
                setattr(user, field, value.lower())
                continue
            if field == "two_factor_enabled" and value is False:
                effective_role = updates.get("role", user.role)
                if effective_role in {"admin", "expert"}:
                    raise ValueError("Two-factor authentication is mandatory for admin and expert accounts.")
                user.two_factor_method = None
                user.totp_secret_encrypted = None
                user.recovery_codes_hashes = None
                user.two_factor_confirmed_at = None
                self._invalidate_trusted_devices(user.id)
            setattr(user, field, value)

        if user.role in {"admin", "expert"}:
            user.two_factor_enabled = True

        if payload.first_name is not None or payload.last_name is not None:
            user.name = f"{user.first_name} {user.last_name}".strip()

        self.db.commit()
        if "manual_mbti" in updates:
            self.user_profile_service.apply_manual_mbti(user.id, updates.get("manual_mbti"))
        self.db.refresh(user)
        self._sync_expert_record_for_user(user)
        return self._build_user_response(user)

    def delete_user(self, item_id: int) -> None:
        user = self._get_or_raise(User, item_id, "User not found.")
        self.db.delete(user)
        self.db.commit()

    def list_deletable_chat_sessions(self) -> list[AdminChatSessionResponse]:
        sessions = (
            self.db.query(ChatSession)
            .options(selectinload(ChatSession.messages))
            .order_by(ChatSession.created_at.desc(), ChatSession.id.desc())
            .all()
        )

        eligible_sessions = []
        user_ids = {session.user_id for session in sessions if session.user_id is not None}
        expert_ids = {session.assigned_expert_id for session in sessions if session.assigned_expert_id is not None}

        users_by_id = {
            user.id: user
            for user in self.db.query(User).filter(User.id.in_(user_ids)).all()
        } if user_ids else {}
        experts_by_id = {
            expert.id: expert
            for expert in self.db.query(Expert).filter(Expert.id.in_(expert_ids)).all()
        } if expert_ids else {}

        for session in sessions:
            eligible_reason = self._get_chat_session_deletion_reason(session)
            if not eligible_reason:
                continue

            eligible_sessions.append(
                AdminChatSessionResponse(
                    id=session.id,
                    title=session.title,
                    status=session.status,
                    mode=session.mode,
                    user_id=session.user_id,
                    user_name=users_by_id.get(session.user_id).name if session.user_id in users_by_id else None,
                    assigned_expert_id=session.assigned_expert_id,
                    assigned_expert_name=(
                        experts_by_id.get(session.assigned_expert_id).name
                        if session.assigned_expert_id in experts_by_id
                        else None
                    ),
                    created_at=session.created_at,
                    closed_at=session.closed_at,
                    eligible_reason=eligible_reason,
                )
            )

        return eligible_sessions

    def list_conversations(self) -> list[AdminConversationOverviewResponse]:
        sessions = (
            self.db.query(ChatSession)
            .options(selectinload(ChatSession.messages))
            .order_by(ChatSession.created_at.desc(), ChatSession.id.desc())
            .all()
        )

        user_ids = {session.user_id for session in sessions if session.user_id is not None}
        expert_ids = {session.assigned_expert_id for session in sessions if session.assigned_expert_id is not None}
        users_by_id = {
            user.id: user for user in self.db.query(User).filter(User.id.in_(user_ids)).all()
        } if user_ids else {}
        experts_by_id = {
            expert.id: expert for expert in self.db.query(Expert).filter(Expert.id.in_(expert_ids)).all()
        } if expert_ids else {}

        return [
            self._build_admin_conversation_overview(session, users_by_id=users_by_id, experts_by_id=experts_by_id)
            for session in sessions
        ]

    def get_conversation(self, item_id: int) -> AdminConversationDetailResponse:
        session = (
            self.db.query(ChatSession)
            .options(
                selectinload(ChatSession.messages),
                selectinload(ChatSession.handoffs),
            )
            .filter(ChatSession.id == item_id)
            .one_or_none()
        )
        if session is None:
            raise LookupError("Conversation not found.")

        users_by_id = {}
        experts_by_id = {}
        if session.user_id is not None:
            user = self.db.get(User, session.user_id)
            if user is not None:
                users_by_id[user.id] = user
        if session.assigned_expert_id is not None:
            expert = self.db.get(Expert, session.assigned_expert_id)
            if expert is not None:
                experts_by_id[expert.id] = expert

        for handoff in session.handoffs:
            if handoff.expert_id not in experts_by_id:
                expert = self.db.get(Expert, handoff.expert_id)
                if expert is not None:
                    experts_by_id[expert.id] = expert

        return AdminConversationDetailResponse(
            conversation=self._build_admin_conversation_overview(
                session,
                users_by_id=users_by_id,
                experts_by_id=experts_by_id,
            ),
            messages=[
                AdminConversationMessageResponse(
                    id=message.id,
                    role=message.role,
                    mode=message.mode,
                    content=message.content,
                    created_at=message.created_at,
                )
                for message in sorted(session.messages, key=lambda item: item.id)
            ],
            handoffs=[
                AdminConversationHandoffResponse(
                    id=handoff.id,
                    session_id=handoff.session_id,
                    session_title=session.title,
                    expert_id=handoff.expert_id,
                    expert_name=experts_by_id.get(handoff.expert_id).name if handoff.expert_id in experts_by_id else None,
                    reason=handoff.reason,
                    from_mode=handoff.from_mode,
                    to_mode=handoff.to_mode,
                    created_at=handoff.created_at,
                )
                for handoff in sorted(session.handoffs, key=lambda item: item.created_at, reverse=True)
            ],
        )

    def list_handoffs(self) -> list[AdminConversationHandoffResponse]:
        handoffs = (
            self.db.query(ExpertHandoff, ChatSession.title, Expert.name)
            .join(ChatSession, ChatSession.id == ExpertHandoff.session_id)
            .join(Expert, Expert.id == ExpertHandoff.expert_id)
            .order_by(ExpertHandoff.created_at.desc(), ExpertHandoff.id.desc())
            .all()
        )

        return [
            AdminConversationHandoffResponse(
                id=handoff.id,
                session_id=handoff.session_id,
                session_title=session_title,
                expert_id=handoff.expert_id,
                expert_name=expert_name,
                reason=handoff.reason,
                from_mode=handoff.from_mode,
                to_mode=handoff.to_mode,
                created_at=handoff.created_at,
            )
            for handoff, session_title, expert_name in handoffs
        ]

    def delete_chat_session(self, item_id: int) -> ChatSessionDeleteResponse:
        session = self.db.query(ChatSession).options(selectinload(ChatSession.messages)).filter(ChatSession.id == item_id).one_or_none()
        if session is None:
            raise LookupError("Chat session not found.")

        eligible_reason = self._get_chat_session_deletion_reason(session)
        if not eligible_reason:
            raise ValueError("This chat session is not eligible for deletion.")

        session_id = session.id
        self.db.delete(session)
        self.db.commit()
        return ChatSessionDeleteResponse(
            session_id=session_id,
            deleted=True,
            message="Chat session deleted successfully.",
        )

    def _get_chat_session_deletion_reason(self, session: ChatSession) -> str | None:
        if session.messages:
            return None

        if session.status == "closed":
            if not settings.admin_allow_delete_closed_empty_chats:
                return None
            return "Closed empty chat"

        cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.admin_open_empty_chat_delete_age_hours)
        created_at = session.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        if created_at > cutoff:
            return None

        return f"Open empty chat older than {settings.admin_open_empty_chat_delete_age_hours} hours"

    def _build_admin_conversation_overview(
        self,
        session: ChatSession,
        *,
        users_by_id: dict[int, User],
        experts_by_id: dict[int, Expert],
    ) -> AdminConversationOverviewResponse:
        latest_message = None
        if session.messages:
            latest_message = max(session.messages, key=lambda item: item.id)
        last_message_at = latest_message.created_at if latest_message else None
        last_activity_at = max(
            (
                value
                for value in [last_message_at, session.typing_updated_at, session.closed_at, session.created_at]
                if value is not None
            ),
            default=session.created_at,
        )

        waiting_on = "No one"
        if session.status == "awaiting_expert":
            waiting_on = "Expert"
        elif session.status == "awaiting_user":
            waiting_on = "User"
        elif session.status == "active":
            waiting_on = "System" if session.mode == "system" else "Expert"
        elif session.status == "closed":
            waiting_on = "Closed"

        unread_message_count = 0
        if session.status == "awaiting_expert":
            unread_message_count = int(
                self.db.execute(
                    select(func.count(ChatMessage.id)).where(
                        ChatMessage.session_id == session.id,
                        ChatMessage.role == "user",
                        ChatMessage.id > (session.expert_last_seen_message_id or 0),
                    )
                ).scalar_one()
                or 0
            )
        elif session.status == "awaiting_user":
            unread_message_count = int(
                self.db.execute(
                    select(func.count(ChatMessage.id)).where(
                        ChatMessage.session_id == session.id,
                        ChatMessage.role == "expert",
                        ChatMessage.id > (session.user_last_seen_message_id or 0),
                    )
                ).scalar_one()
                or 0
            )

        return AdminConversationOverviewResponse(
            id=session.id,
            title=session.title,
            status=session.status,
            mode=session.mode,
            user_id=session.user_id,
            user_name=users_by_id.get(session.user_id).name if session.user_id in users_by_id else None,
            assigned_expert_id=session.assigned_expert_id,
            assigned_expert_name=(
                experts_by_id.get(session.assigned_expert_id).name
                if session.assigned_expert_id in experts_by_id
                else None
            ),
            created_at=session.created_at,
            closed_at=session.closed_at,
            last_message_at=last_message_at,
            last_activity_at=last_activity_at,
            last_message_role=latest_message.role if latest_message else None,
            last_message_preview=(latest_message.content[:120] if latest_message else None),
            message_count=len(session.messages),
            unread_message_count=unread_message_count,
            needs_attention=unread_message_count > 0,
            waiting_on=waiting_on,
            typing_actor_role=session.typing_actor_role,
        )

    def reset_user_password(self, item_id: int, *, send_credentials_email: bool = False) -> UserCredentialActionResponse:
        user = self._get_or_raise(User, item_id, "User not found.")

        temporary_password = self._generate_temporary_password()
        user.password_hash = self._hash_password(temporary_password)
        self._invalidate_trusted_devices(user.id)
        self.db.commit()

        credentials_email_triggered = False
        if send_credentials_email:
            credentials_email_triggered = self.email_service.send_account_created_email(
                user.email,
                user.first_name,
                user.role,
                temporary_password,
            )

        return UserCredentialActionResponse(
            user_id=user.id,
            action="password_reset",
            credentials_email_triggered=credentials_email_triggered,
            generated_temporary_password=None if credentials_email_triggered else temporary_password,
        )

    def resend_user_credentials(self, item_id: int) -> UserCredentialActionResponse:
        user = self._get_or_raise(User, item_id, "User not found.")

        temporary_password = self._generate_temporary_password()
        user.password_hash = self._hash_password(temporary_password)
        self._invalidate_trusted_devices(user.id)
        self.db.commit()

        credentials_email_triggered = self.email_service.send_account_created_email(
            user.email,
            user.first_name,
            user.role,
            temporary_password,
        )

        return UserCredentialActionResponse(
            user_id=user.id,
            action="credentials_reissued",
            credentials_email_triggered=credentials_email_triggered,
            generated_temporary_password=None if credentials_email_triggered else temporary_password,
        )

    def reset_user_two_factor(self, item_id: int) -> UserCredentialActionResponse:
        user = self._get_or_raise(User, item_id, "User not found.")
        user.two_factor_method = None
        user.totp_secret_encrypted = None
        user.recovery_codes_hashes = None
        user.two_factor_confirmed_at = None
        self._invalidate_trusted_devices(user.id)
        if user.role in {"admin", "expert"}:
            user.two_factor_enabled = True
        self.db.commit()

        return UserCredentialActionResponse(
            user_id=user.id,
            action="two_factor_reset",
            credentials_email_triggered=False,
            generated_temporary_password=None,
        )

    def list_experts(self) -> list[ExpertAdminResponse]:
        experts = (
            self.db.query(Expert)
            .options(selectinload(Expert.domains))
            .order_by(Expert.id)
            .all()
        )
        return [self._build_expert_response(item) for item in experts]

    def create_expert(self, payload: ExpertAdminCreateRequest) -> ExpertAdminResponse:
        expert = Expert(
            name=payload.name,
            email=payload.email.lower() if payload.email else None,
            is_active=payload.is_active,
        )
        self.db.add(expert)
        self.db.flush()
        self._replace_expert_domains(expert.id, payload.domain_codes)
        self.db.commit()
        expert = self.db.query(Expert).options(selectinload(Expert.domains)).filter(Expert.id == expert.id).one()
        return self._build_expert_response(expert)

    def get_expert(self, item_id: int) -> ExpertAdminResponse:
        expert = (
            self.db.query(Expert)
            .options(selectinload(Expert.domains))
            .filter(Expert.id == item_id)
            .one_or_none()
        )
        if expert is None:
            raise LookupError("Expert not found.")
        return self._build_expert_response(expert)

    def update_expert(self, item_id: int, payload: ExpertAdminUpdateRequest) -> ExpertAdminResponse:
        expert = self._get_or_raise(Expert, item_id, "Expert not found.")
        updates = payload.model_dump(exclude_unset=True)
        domain_codes = updates.pop("domain_codes", None)
        for field, value in updates.items():
            if field == "email" and isinstance(value, str):
                value = value.lower()
            setattr(expert, field, value)
        if domain_codes is not None:
            self._replace_expert_domains(expert.id, domain_codes)
        self.db.commit()
        expert = self.db.query(Expert).options(selectinload(Expert.domains)).filter(Expert.id == expert.id).one()
        return self._build_expert_response(expert)

    def provision_expert_account(self, item_id: int, *, send_credentials_email: bool = True) -> ExpertProvisionResponse:
        expert = self._get_or_raise(Expert, item_id, "Expert not found.")
        if not expert.email:
            raise ValueError(f"This expert must have an email address before a {settings.app_public_name} account can be provisioned.")

        existing_user = self._find_user_by_email(expert.email)
        if existing_user is not None:
            if existing_user.role != "expert":
                raise ValueError(f"This email already belongs to a non-expert {settings.app_public_name} account.")
            raise ValueError(f"This expert already has a provisioned {settings.app_public_name} expert account.")

        first_name, last_name = self._split_name(expert.name)
        temporary_password = self._generate_temporary_password()
        user = User(
            name=expert.name.strip(),
            first_name=first_name,
            last_name=last_name,
            email=expert.email.lower(),
            role="expert",
            is_active=expert.is_active,
            password_hash=self._hash_password(temporary_password),
            registration_status="approved",
            two_factor_enabled=True,
            ai_profiling_consent=False,
            gdpr_consent=False,
            profiling_opt_out_requested=False,
            account_deletion_requested=False,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        self._sync_expert_record_for_user(user)

        credentials_email_triggered = False
        if send_credentials_email:
            credentials_email_triggered = self.email_service.send_account_created_email(
                user.email,
                user.first_name,
                user.role,
                temporary_password,
            )

        return ExpertProvisionResponse(
            expert_id=expert.id,
            platform_user_id=user.id,
            action="provisioned",
            credentials_email_triggered=credentials_email_triggered,
            generated_temporary_password=None if credentials_email_triggered else temporary_password,
        )

    def delete_expert(self, item_id: int) -> None:
        expert = self._get_or_raise(Expert, item_id, "Expert not found.")
        self.db.delete(expert)
        self.db.commit()

    def list_knowledge(self) -> list[KnowledgeAdminResponse]:
        items = (
            self.db.query(KnowledgeItem)
            .options(selectinload(KnowledgeItem.source_expert))
            .order_by(KnowledgeItem.id)
            .all()
        )
        return [self._build_knowledge_response(item) for item in items]

    def create_knowledge(self, payload: KnowledgeAdminCreateRequest) -> KnowledgeAdminResponse:
        item = KnowledgeItem(**payload.model_dump())
        self.db.add(item)
        self.db.commit()
        item = (
            self.db.query(KnowledgeItem)
            .options(selectinload(KnowledgeItem.source_expert))
            .filter(KnowledgeItem.id == item.id)
            .one()
        )
        return self._build_knowledge_response(item)

    def get_knowledge(self, item_id: int) -> KnowledgeAdminResponse:
        item = (
            self.db.query(KnowledgeItem)
            .options(selectinload(KnowledgeItem.source_expert))
            .filter(KnowledgeItem.id == item_id)
            .one_or_none()
        )
        if item is None:
            raise LookupError("Knowledge item not found.")
        return self._build_knowledge_response(item)

    def update_knowledge(self, item_id: int, payload: KnowledgeAdminUpdateRequest) -> KnowledgeAdminResponse:
        item = self._get_or_raise(KnowledgeItem, item_id, "Knowledge item not found.")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        self.db.commit()
        item = (
            self.db.query(KnowledgeItem)
            .options(selectinload(KnowledgeItem.source_expert))
            .filter(KnowledgeItem.id == item.id)
            .one()
        )
        return self._build_knowledge_response(item)

    def delete_knowledge(self, item_id: int) -> None:
        item = self._get_or_raise(KnowledgeItem, item_id, "Knowledge item not found.")
        self.db.delete(item)
        self.db.commit()

    def list_domain_options(self) -> list[DomainOptionResponse]:
        expert_domain_codes = set(self.db.execute(select(ExpertDomain.domain_code)).scalars().all())
        knowledge_domain_codes = set(self.db.execute(select(KnowledgeItem.domain_code)).scalars().all())
        domain_codes = sorted(code for code in (expert_domain_codes | knowledge_domain_codes) if code)
        return [DomainOptionResponse(code=code) for code in domain_codes]

    def get_module_settings(self) -> ModuleSettingsResponse:
        state = self.module_settings_service.get_settings()
        return ModuleSettingsResponse(
            synapse_enabled=state.synapse_enabled,
            uex_enabled=state.uex_enabled,
            ulm_enabled=state.ulm_enabled,
            page_enabled=state.page_enabled,
            llm_provider=state.llm_provider,
            llm_model=state.llm_model,
            llm_available_providers=self._build_llm_provider_options(),
        )

    def update_module_settings(self, payload: ModuleSettingsUpdateRequest) -> ModuleSettingsResponse:
        state = self.module_settings_service.update_settings(
            synapse_enabled=payload.synapse_enabled,
            uex_enabled=payload.uex_enabled,
            ulm_enabled=payload.ulm_enabled,
            page_enabled=payload.page_enabled,
            llm_provider=payload.llm_provider,
            llm_model=payload.llm_model,
        )
        return ModuleSettingsResponse(
            synapse_enabled=state.synapse_enabled,
            uex_enabled=state.uex_enabled,
            ulm_enabled=state.ulm_enabled,
            page_enabled=state.page_enabled,
            llm_provider=state.llm_provider,
            llm_model=state.llm_model,
            llm_available_providers=self._build_llm_provider_options(),
        )

    def get_general_settings(self) -> GeneralSettingsResponse:
        state = self.module_settings_service.get_general_settings()
        return GeneralSettingsResponse(
            show_chat_debug_panels=state.show_chat_debug_panels,
            verbose_routing_logs=state.verbose_routing_logs,
            allow_expert_handoff=state.allow_expert_handoff,
            allow_ulm_in_chat=state.allow_ulm_in_chat,
        )

    def update_general_settings(self, payload: GeneralSettingsUpdateRequest) -> GeneralSettingsResponse:
        state = self.module_settings_service.update_general_settings(
            show_chat_debug_panels=payload.show_chat_debug_panels,
            verbose_routing_logs=payload.verbose_routing_logs,
            allow_expert_handoff=payload.allow_expert_handoff,
            allow_ulm_in_chat=payload.allow_ulm_in_chat,
        )
        return GeneralSettingsResponse(
            show_chat_debug_panels=state.show_chat_debug_panels,
            verbose_routing_logs=state.verbose_routing_logs,
            allow_expert_handoff=state.allow_expert_handoff,
            allow_ulm_in_chat=state.allow_ulm_in_chat,
        )

    def list_profiles(self) -> list[ProfileAdminResponse]:
        return [
            ProfileAdminResponse.model_validate(item)
            for item in self.db.query(ExpertProfile).order_by(ExpertProfile.id).all()
        ]

    def create_profile(self, payload: ProfileAdminCreateRequest) -> ProfileAdminResponse:
        profile = ExpertProfile(**payload.model_dump())
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return ProfileAdminResponse.model_validate(profile)

    def get_profile(self, item_id: int) -> ProfileAdminResponse:
        return ProfileAdminResponse.model_validate(
            self._get_or_raise(ExpertProfile, item_id, "Expert profile not found.")
        )

    def _build_llm_provider_options(self) -> list[LlmProviderOptionResponse]:
        return [
            LlmProviderOptionResponse(
                provider=option.provider,
                default_model=option.default_model,
                model_options=list(option.model_options),
            )
            for option in self.module_settings_service.get_llm_options()
        ]

    def update_profile(self, item_id: int, payload: ProfileAdminUpdateRequest) -> ProfileAdminResponse:
        profile = self._get_or_raise(ExpertProfile, item_id, "Expert profile not found.")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)
        self.db.commit()
        self.db.refresh(profile)
        return ProfileAdminResponse.model_validate(profile)

    def delete_profile(self, item_id: int) -> None:
        profile = self._get_or_raise(ExpertProfile, item_id, "Expert profile not found.")
        self.db.delete(profile)
        self.db.commit()

    def list_ulm_sources(self) -> list[UlmSourceAdminResponse]:
        sources = (
            self.db.query(KnowledgeSource)
            .options(selectinload(KnowledgeSource.documents))
            .order_by(KnowledgeSource.id.desc())
            .all()
        )
        return [self._build_ulm_source_response(item) for item in sources]

    def create_ulm_source(self, payload: UlmSourceAdminCreateRequest) -> UlmSourceAdminResponse:
        source = UlmService(self.db).ingest(payload)
        return self._build_ulm_source_response(
            self.db.query(KnowledgeSource).options(selectinload(KnowledgeSource.documents)).filter(KnowledgeSource.id == source.id).one()
        )

    def ingest_ulm_source_upload(
        self,
        *,
        filename: str,
        content_bytes: bytes,
        title: str | None = None,
    ) -> UlmSourceAdminResponse:
        extracted_text = self._extract_text_from_uploaded_file(filename=filename, content_bytes=content_bytes)
        normalized_title = (title or "").strip() or filename
        source = UlmService(self.db).ingest(
            UlmSourceAdminCreateRequest(
                title=normalized_title,
                document=extracted_text,
                url=None,
            )
        )
        return self._build_ulm_source_response(
            self.db.query(KnowledgeSource).options(selectinload(KnowledgeSource.documents)).filter(KnowledgeSource.id == source.id).one()
        )

    def get_ulm_source(self, item_id: int) -> UlmSourceAdminDetailResponse:
        source = (
            self.db.query(KnowledgeSource)
            .options(selectinload(KnowledgeSource.documents))
            .filter(KnowledgeSource.id == item_id)
            .one_or_none()
        )
        if source is None:
            raise LookupError("ULM source not found.")
        return self._build_ulm_source_detail_response(source)

    def update_ulm_source(self, item_id: int, payload: UlmSourceAdminUpdateRequest) -> UlmSourceAdminResponse:
        source = self._get_or_raise(KnowledgeSource, item_id, "ULM source not found.")
        for field, value in payload.model_dump(exclude_unset=True).items():
            if field == "title":
                first_document = (
                    self.db.query(SourceDocument)
                    .filter(SourceDocument.knowledge_source_id == source.id)
                    .order_by(SourceDocument.chunk_index.asc(), SourceDocument.id.asc())
                    .first()
                )
                if first_document is not None:
                    first_document.title = value
            else:
                setattr(source, field, value)
        self.db.commit()
        source = (
            self.db.query(KnowledgeSource)
            .options(selectinload(KnowledgeSource.documents))
            .filter(KnowledgeSource.id == source.id)
            .one()
        )
        return self._build_ulm_source_response(source)

    def delete_ulm_source(self, item_id: int) -> None:
        source = self._get_or_raise(KnowledgeSource, item_id, "ULM source not found.")
        self.db.delete(source)
        self.db.commit()

    def refresh_ulm_source(self, item_id: int) -> UlmSourceAdminDetailResponse:
        source = (
            self.db.query(KnowledgeSource)
            .options(selectinload(KnowledgeSource.documents))
            .filter(KnowledgeSource.id == item_id)
            .one_or_none()
        )
        if source is None:
            raise LookupError("ULM source not found.")
        if source.source_type != "url":
            raise ValueError("Only URL sources can be refreshed.")

        base_title = self._resolve_ulm_source_title(source)

        for document in list(source.documents or []):
            self.db.delete(document)

        source.indexing_status = "queued"
        self.db.flush()

        fetched_title, fetched_text = UlmService(self.db)._fetch_url_text(source.source_value)
        resolved_title = (base_title or fetched_title or source.source_value).strip() or None
        UlmService(self.db)._index_document_source(
            source=source,
            title=resolved_title,
            content=fetched_text,
            url=source.source_value,
        )

        self.db.commit()
        source = (
            self.db.query(KnowledgeSource)
            .options(selectinload(KnowledgeSource.documents))
            .filter(KnowledgeSource.id == source.id)
            .one()
        )
        return self._build_ulm_source_detail_response(source)

    def _get_or_raise(self, model, item_id: int, message: str):
        item = self.db.get(model, item_id)
        if item is None:
            raise LookupError(message)
        return item

    def _generate_temporary_password(self, length: int = 12) -> str:
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789"
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def _find_expert_by_email(self, email: str | None) -> Expert | None:
        if not email:
            return None

        statement = select(Expert).where(Expert.email == email.lower())
        return self.db.execute(statement).scalar_one_or_none()

    def _find_user_by_email(self, email: str | None) -> User | None:
        if not email:
            return None

        statement = select(User).where(User.email == email.lower())
        return self.db.execute(statement).scalar_one_or_none()

    def _sync_expert_record_for_user(self, user: User) -> None:
        expert = self._find_expert_by_email(user.email)

        if user.role != "expert":
            if expert is not None:
                expert.name = user.name
                expert.is_active = False
                self.db.commit()
            return

        if expert is None:
            expert = Expert(
                name=user.name,
                email=user.email,
                is_active=user.is_active,
            )
            self.db.add(expert)
        else:
            expert.name = user.name
            expert.email = user.email
            expert.is_active = user.is_active

        self.db.commit()

    def _build_user_response(self, user: User) -> UserResponse:
        profile = user.profile

        return UserResponse(
            id=user.id,
            name=user.name,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            registration_status=user.registration_status,
            two_factor_enabled=user.two_factor_enabled,
            ai_profiling_consent=user.ai_profiling_consent,
            gdpr_consent=user.gdpr_consent,
            can_access_chat_debug_panels=user.can_access_chat_debug_panels,
            profiling_opt_out_requested=user.profiling_opt_out_requested,
            account_deletion_requested=user.account_deletion_requested,
            created_at=user.created_at,
            updated_at=user.updated_at,
            manual_mbti=profile.manual_mbti if profile else None,
            inferred_mbti=profile.inferred_mbti if profile else None,
            effective_mbti=profile.effective_mbti if profile else None,
            profile_confidence=profile.confidence if profile else None,
            profile_interaction_count=profile.interaction_count if profile else 0,
        )

    def list_user_trusted_devices(self, item_id: int) -> list[TrustedDeviceAdminResponse]:
        self._get_or_raise(User, item_id, "User not found.")
        devices = (
            self.db.execute(
                select(TrustedDevice)
                .where(TrustedDevice.user_id == item_id)
                .order_by(TrustedDevice.last_used_at.desc().nullslast(), TrustedDevice.created_at.desc())
            )
            .scalars()
            .all()
        )
        return [TrustedDeviceAdminResponse.model_validate(device) for device in devices]

    def revoke_user_trusted_device(self, item_id: int, device_id: int) -> UserCredentialActionResponse:
        self._get_or_raise(User, item_id, "User not found.")
        device = (
            self.db.execute(
                select(TrustedDevice).where(
                    TrustedDevice.id == device_id,
                    TrustedDevice.user_id == item_id,
                )
            )
            .scalar_one_or_none()
        )
        if device is None:
            raise LookupError("Trusted device not found.")

        self.db.delete(device)
        self.db.commit()
        return UserCredentialActionResponse(
            user_id=item_id,
            action="trusted_device_revoked",
            credentials_email_triggered=False,
            generated_temporary_password=None,
        )

    def revoke_all_user_trusted_devices(self, item_id: int) -> UserCredentialActionResponse:
        self._get_or_raise(User, item_id, "User not found.")
        self._invalidate_trusted_devices(item_id)
        self.db.commit()
        return UserCredentialActionResponse(
            user_id=item_id,
            action="all_trusted_devices_revoked",
            credentials_email_triggered=False,
            generated_temporary_password=None,
        )

    def _build_expert_response(self, expert: Expert) -> ExpertAdminResponse:
        linked_user = self._find_user_by_email(expert.email)
        has_platform_account = linked_user is not None and linked_user.role == "expert"
        return ExpertAdminResponse(
            id=expert.id,
            name=expert.name,
            email=expert.email,
            is_active=expert.is_active,
            domain_codes=sorted(domain.domain_code for domain in expert.domains),
            platform_user_id=linked_user.id if has_platform_account else None,
            has_platform_account=has_platform_account,
            platform_account_active=bool(linked_user.is_active) if has_platform_account else False,
            platform_account_registration_status=linked_user.registration_status if has_platform_account else None,
            created_at=expert.created_at,
        )

    def _build_dashboard_active_expert_response(self, expert: Expert) -> AdminDashboardActiveExpertResponse:
        linked_user = self._find_user_by_email(expert.email)
        has_platform_account = linked_user is not None and linked_user.role == "expert"
        return AdminDashboardActiveExpertResponse(
            id=expert.id,
            name=self._build_user_display_name(linked_user) if has_platform_account else expert.name,
            email=expert.email or "No email",
            availability="Available" if expert.is_active else "Inactive",
            two_factor=(
                "Enabled"
                if has_platform_account and linked_user.two_factor_enabled
                else "Disabled"
                if has_platform_account
                else "No platform account"
            ),
        )

    def _build_knowledge_response(self, item: KnowledgeItem) -> KnowledgeAdminResponse:
        return KnowledgeAdminResponse(
            id=item.id,
            title=item.title,
            content=item.content,
            domain_code=item.domain_code,
            status=item.status,
            source_expert_id=item.source_expert_id,
            source_expert_name=item.source_expert.name if item.source_expert is not None else None,
            created_at=item.created_at,
        )

    def _build_ulm_source_response(self, source: KnowledgeSource) -> UlmSourceAdminResponse:
        documents = list(source.documents or [])
        indexed_chunk_count = sum(1 for item in documents if item.indexing_status == "indexed")
        last_updated_at = max((item.created_at for item in documents), default=source.created_at)
        return UlmSourceAdminResponse(
            id=source.id,
            source_type=source.source_type,
            source_value=source.source_value,
            title=self._resolve_ulm_source_title(source),
            indexing_status=source.indexing_status,
            document_count=len(documents),
            indexed_chunk_count=indexed_chunk_count,
            created_at=source.created_at,
            last_updated_at=last_updated_at,
        )

    def _build_ulm_source_detail_response(self, source: KnowledgeSource) -> UlmSourceAdminDetailResponse:
        documents = list(source.documents or [])
        indexed_chunk_count = sum(1 for item in documents if item.indexing_status == "indexed")
        last_updated_at = max((item.created_at for item in documents), default=source.created_at)
        return UlmSourceAdminDetailResponse(
            id=source.id,
            source_type=source.source_type,
            source_value=source.source_value,
            title=self._resolve_ulm_source_title(source),
            indexing_status=source.indexing_status,
            document_count=len(documents),
            indexed_chunk_count=indexed_chunk_count,
            created_at=source.created_at,
            last_updated_at=last_updated_at,
            documents=[
                UlmSourceAdminChunkResponse.model_validate(document)
                for document in documents
            ],
        )

    @staticmethod
    def _resolve_ulm_source_title(source: KnowledgeSource) -> str | None:
        first_document = source.documents[0] if source.documents else None
        if first_document is None or not first_document.title:
            return None
        return re.sub(r"\s+\(Chunk \d+/\d+\)$", "", first_document.title).strip()

    def _extract_text_from_uploaded_file(self, *, filename: str, content_bytes: bytes) -> str:
        extension = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

        if extension == "txt":
            return self._decode_text_file(content_bytes)
        if extension == "pdf":
            return self._extract_pdf_text(content_bytes)
        if extension == "docx":
            return self._extract_docx_text(content_bytes)

        raise ValueError("Unsupported file type. Upload a .txt, .pdf, or .docx document.")

    @staticmethod
    def _decode_text_file(content_bytes: bytes) -> str:
        for encoding in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                text = content_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError("Unable to decode the uploaded text file.")

        normalized = text.strip()
        if not normalized:
            raise ValueError("The uploaded text file is empty.")
        return normalized

    @staticmethod
    def _extract_pdf_text(content_bytes: bytes) -> str:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("PDF upload support requires pypdf to be installed.") from exc

        reader = PdfReader(BytesIO(content_bytes))
        text = "\n\n".join((page.extract_text() or "").strip() for page in reader.pages).strip()
        if not text:
            raise ValueError("No readable text was found in the uploaded PDF.")
        return text

    @staticmethod
    def _extract_docx_text(content_bytes: bytes) -> str:
        try:
            from docx import Document
        except ImportError as exc:
            raise RuntimeError("DOCX upload support requires python-docx to be installed.") from exc

        document = Document(BytesIO(content_bytes))
        text = "\n".join(paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()).strip()
        if not text:
            raise ValueError("No readable text was found in the uploaded DOCX file.")
        return text

    def _replace_expert_domains(self, expert_id: int, domain_codes: list[str]) -> None:
        requested_codes = sorted({code.strip() for code in domain_codes if code and code.strip()})
        existing_domains = self.db.execute(
            select(ExpertDomain).where(ExpertDomain.expert_id == expert_id)
        ).scalars().all()
        existing_by_code = {domain.domain_code: domain for domain in existing_domains}

        for code, domain in existing_by_code.items():
            if code not in requested_codes:
                self.db.delete(domain)

        for code in requested_codes:
            if code in existing_by_code:
                continue
            self.db.add(ExpertDomain(expert_id=expert_id, domain_code=code))

    @staticmethod
    def _format_consents(ai_profiling_consent: bool, gdpr_consent: bool) -> str:
        labels: list[str] = []
        if ai_profiling_consent:
            labels.append("AI")
        if gdpr_consent:
            labels.append("GDPR")
        return " + ".join(labels) if labels else "No consents"

    def _email_exists(self, email: str) -> bool:
        statement = select(User.id).where(User.email == email.lower())
        return self.db.execute(statement).scalar_one_or_none() is not None

    def _invalidate_trusted_devices(self, user_id: int) -> None:
        devices = self.db.execute(select(TrustedDevice).where(TrustedDevice.user_id == user_id)).scalars().all()
        for device in devices:
            self.db.delete(device)

    @staticmethod
    def _split_name(full_name: str) -> tuple[str, str]:
        segments = [segment for segment in (full_name or "").strip().split() if segment]
        if not segments:
            return "Expert", "User"
        if len(segments) == 1:
            return segments[0], "Expert"
        return segments[0], " ".join(segments[1:])

    @staticmethod
    def _build_user_display_name(user: User | None) -> str:
        if user is None:
            return "Unknown"

        full_name = " ".join(part for part in [user.first_name, user.last_name] if part).strip()
        return full_name or user.name or user.email

    def _hash_password(self, password: str) -> str:
        return hash_password(password)
