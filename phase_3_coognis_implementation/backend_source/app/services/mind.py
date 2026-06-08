from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger, log_event
from app.models import ChatMessage, ChatSession, Expert, ExpertHandoff, FeedbackEntry, MindChatLog, User
from app.schemas.mind import (
    ChatHistoryResponse,
    ChatHandoffRequest,
    ChatMessageResponse,
    ChatUnreadSummaryResponse,
    ChatTypingRequest,
    ExpertChatMessageRequest,
    ExpertChatMessageResponse,
    ChatSessionListResponse,
    ChatSessionResponse,
    ChatSessionStartRequest,
    ExpertHandoffResponse,
    ExpertSuggestion,
    MindChatDebug,
    MindDebugKnowledgeItem,
    MindDebugPageExpertSuggestion,
    MindDebugPageInput,
    MindDebugPageUlmGrounding,
    MindDebugPageUlmSource,
    MindDebugUlmChunk,
    MindPageDebug,
    MindSynapseDebug,
    MindChatMessageResponse,
)
from app.schemas.page import PageExpertSuggestion, PageRespondRequest, PageUlmGrounding, PageUlmSource, PageUserProfile
from app.schemas.synapse import SynapseInferenceResult
from app.schemas.uex import ExpertMatchRequest, ExpertMatchResponse
from app.schemas.ulm import UlmGenerateRequest
from app.services.expert_profile import ExpertProfileService
from app.services.email import EmailService
from app.services.local_llm import LocalLlmClient
from app.services.module_settings import ModuleSettingsService
from app.services.page import PageService
from app.services.synapse import SynapseService
from app.services.user_profile import UserProfileService
from app.services.uex import UexService
from app.services.ulm import UlmService

logger = get_logger(__name__)

OPEN_CHAT_SESSION_STATUSES = {"active", "awaiting_expert", "awaiting_user"}
EXPERT_MODE_SUPPRESSED_SYSTEM_RESPONSE = "I do not have enough relevant context to answer that."


class MindService:
    """Orchestration service for MIND chat responses."""

    def __init__(
        self,
        db: Session,
        synapse_service: SynapseService | None,
        uex_service: UexService,
        ulm_service: UlmService | None,
        page_service: PageService | None,
        ulm_llm_client: LocalLlmClient | None,
        page_llm_client: LocalLlmClient | None = None,
    ) -> None:
        self.db = db
        self.synapse_service = synapse_service
        self.uex_service = uex_service
        self.ulm_service = ulm_service
        self.page_service = page_service
        self.ulm_llm_client = ulm_llm_client
        self.page_llm_client = page_llm_client
        self.user_profile_service = UserProfileService(db)
        self.expert_profile_service = ExpertProfileService(db)
        self.module_settings_service = ModuleSettingsService(db)
        self.email_service = EmailService()

    def respond(
        self,
        *,
        actor_user_id: int,
        session_id: int,
        query: str,
        use_synapse: bool,
        use_uex: bool,
        use_ulm: bool,
    ) -> MindChatMessageResponse:
        if self.synapse_service is None or self.ulm_service is None or self.page_service is None:
            raise RuntimeError("MIND response dependencies are not configured.")
        session = self.db.get(ChatSession, session_id)
        if session is None:
            raise LookupError("Session not found.")
        actor_role, _ = self._resolve_session_actor(actor_user_id, session)
        if actor_role != "user":
            raise PermissionError("Only the conversation owner can send messages through the system channel.")
        actor_user = self.db.get(User, actor_user_id)
        if actor_user is None:
            raise LookupError("User not found.")
        if session.status not in OPEN_CHAT_SESSION_STATUSES:
            raise ValueError("This conversation is closed and cannot be reopened.")

        module_settings = self.module_settings_service.get_settings()
        general_settings = self.module_settings_service.get_general_settings()
        can_include_debug = self._can_expose_chat_debug_panels(actor_user, general_settings=general_settings)
        effective_use_synapse = bool(use_synapse and module_settings.synapse_enabled)
        effective_use_uex = bool(use_uex and module_settings.uex_enabled)
        effective_use_ulm = bool(use_ulm and module_settings.ulm_enabled and general_settings.allow_ulm_in_chat)
        effective_use_page = bool(module_settings.page_enabled)

        if session.mode == "expert":
            modules_used = ["MIND", "EXPERT"]
            should_notify_expert = self._should_notify_expert_on_first_user_message(session.id)
            self._store_chat_message(session_id=session.id, role="user", mode=session.mode, content=query)
            session.typing_actor_role = None
            session.typing_updated_at = None
            session.status = "awaiting_expert"
            self._store_log(
                session_id=session.id,
                query=query,
                final_response="",
                modules_used=modules_used,
                expert_suggestion=None,
            )
            self.db.commit()
            if should_notify_expert:
                self._notify_expert_about_session_message(session=session)
            return MindChatMessageResponse(
                final_response="",
                modules_used=modules_used,
                assistant_message_id=None,
                expert_suggestion=None,
                debug=(
                    MindChatDebug(
                        inferred_domain_codes=[],
                        uex_knowledge_preview=None,
                        uex_knowledge_items=[],
                        ulm_chunks=[],
                        page=None,
                        page_input=MindDebugPageInput(
                            user_mbti=None,
                            query=query,
                            uex_knowledge="No UEX knowledge available.",
                            expert_suggestion=None,
                            ulm_grounding=None,
                            ulm_used=False,
                            conversation_mode=session.mode,
                        ),
                        synapse=None,
                        expert_suggestion_reason=None,
                    )
                    if can_include_debug
                    else None
                ),
            )

        modules_used = ["MIND"]
        target_mbti = None
        stored_profile = None
        synapse_result = None
        if effective_use_synapse:
            stored_profile = self._record_user_interaction(session.user_id, query)
            synapse_result = self._resolve_user_profile(query, stored_profile.effective_mbti if stored_profile else None)
            target_mbti = synapse_result.mbti_type
            modules_used.append("SYNAPSE")

        inferred_domain_codes: list[str] = []
        uex_knowledge_content = "No UEX knowledge available."
        uex_knowledge_items: list[MindDebugKnowledgeItem] = []
        expert_suggestion = None
        if effective_use_uex:
            inferred_domain_codes = self.uex_service.suggest_domain_codes_for_text(query)
            uex_knowledge = self.uex_service.get_knowledge_context_for_query(
                query=query,
                domain_codes=inferred_domain_codes,
                limit=3,
            )
            uex_knowledge_content = uex_knowledge.content or "No UEX knowledge available."
            uex_knowledge_items = [
                MindDebugKnowledgeItem(
                    id=item.id,
                    title=item.title,
                    domain_code=item.domain_code,
                )
                for item in uex_knowledge.items
            ]
            if uex_knowledge.items and general_settings.allow_expert_handoff:
                expert_matches = self.uex_service.match_experts(
                    ExpertMatchRequest(domain_codes=inferred_domain_codes, target_mbti=target_mbti, limit=1)
                )
                expert_suggestion = self._build_expert_suggestion(expert_matches)
                modules_used.append("UEX")

        if effective_use_page:
            modules_used.append("PAGE")
        ulm_summary = "No ULM summary used."
        ulm_grounding = None
        retrieved_context = None
        if effective_use_ulm:
            retrieved_context = self.ulm_service.retrieve_context(query=query, limit=3)
            if retrieved_context.retrieved_chunks:
                ulm_result = self.ulm_service.generate(
                    UlmGenerateRequest(query=query, retrieved_chunks=retrieved_context.retrieved_chunks),
                    self.ulm_llm_client,
                )
                ulm_summary = ulm_result.explanation
                ulm_grounding = PageUlmGrounding(
                    summary=ulm_result.explanation,
                    source_count=len({chunk.source_id for chunk in retrieved_context.retrieved_chunks if chunk.source_id}),
                    chunk_count=len(retrieved_context.retrieved_chunks),
                    sources=[
                        PageUlmSource(
                            title=chunk.title,
                            chunk_index=chunk.chunk_index,
                            source_type=chunk.source_type,
                            url=chunk.url,
                        )
                        for chunk in retrieved_context.retrieved_chunks[:3]
                    ],
                )
                modules_used.insert(3, "ULM")

        if general_settings.verbose_routing_logs:
            log_event(
                logger,
                "mind_routing_decision",
                session_id=session.id,
                session_mode=session.mode,
                inferred_mbti=target_mbti,
                inferred_domain_codes=inferred_domain_codes,
                use_synapse_requested=use_synapse,
                use_uex_requested=use_uex,
                use_ulm_requested=use_ulm,
                effective_use_synapse=effective_use_synapse,
                effective_use_uex=effective_use_uex,
                effective_use_ulm=effective_use_ulm,
                effective_use_page=effective_use_page,
                synapse_used="SYNAPSE" in modules_used,
                uex_used="UEX" in modules_used,
                ulm_used="ULM" in modules_used,
                ulm_source_count=ulm_grounding.source_count if ulm_grounding else 0,
                ulm_chunk_count=ulm_grounding.chunk_count if ulm_grounding else 0,
                knowledge_context_length=len(uex_knowledge_content),
                expert_suggestion=expert_suggestion,
                modules_used=modules_used,
            )

        final_response = self._compose_non_page_response(
            query=query,
            uex_knowledge=uex_knowledge_content,
            expert_suggestion=expert_suggestion,
            ulm_summary=ulm_summary if "ULM" in modules_used else None,
            ulm_used="ULM" in modules_used,
        )
        page_result = None
        if effective_use_page:
            page_result = self.page_service.respond(
                PageRespondRequest(
                    user_profile=PageUserProfile(mbti=target_mbti),
                    query=query,
                    uex_knowledge=uex_knowledge_content,
                    expert_suggestion=(
                        PageExpertSuggestion(
                            name=expert_suggestion.name,
                            domain_codes=expert_suggestion.domain_codes,
                            is_contactable=expert_suggestion.is_contactable,
                            reason=(
                                f"Match score {expert_suggestion.total_score:.2f} based on current query routing."
                                if expert_suggestion
                                else None
                            ),
                        )
                        if expert_suggestion
                        else None
                    ),
                    ulm_grounding=ulm_grounding if "ULM" in modules_used else None,
                    ulm_used="ULM" in modules_used,
                    conversation_mode=session.mode,
                ),
                self.page_llm_client,
            )
            final_response = page_result.response

        session.typing_actor_role = None
        session.typing_updated_at = None
        session.status = "awaiting_expert" if session.mode == "expert" else "active"
        self._store_chat_message(session_id=session.id, role="user", mode=session.mode, content=query)
        suppress_assistant_message = (
            session.mode == "expert"
            and final_response.strip() == EXPERT_MODE_SUPPRESSED_SYSTEM_RESPONSE
        )
        assistant_message = None
        if not suppress_assistant_message:
            assistant_message = self._store_chat_message(
                session_id=session.id,
                role="assistant",
                mode=session.mode,
                content=final_response,
            )
        self._store_log(
            session_id=session.id,
            query=query,
            final_response=final_response,
            modules_used=modules_used,
            expert_suggestion=expert_suggestion,
        )

        return MindChatMessageResponse(
            final_response=final_response,
            modules_used=modules_used,
            assistant_message_id=assistant_message.id if assistant_message is not None else None,
            expert_suggestion=expert_suggestion,
            debug=(
                MindChatDebug(
                    inferred_domain_codes=inferred_domain_codes,
                    uex_knowledge_preview=uex_knowledge_content[:400] if uex_knowledge_content else None,
                    uex_knowledge_items=uex_knowledge_items,
                    ulm_chunks=[
                        MindDebugUlmChunk(
                            source_id=chunk.source_id,
                            document_id=chunk.document_id,
                            title=chunk.title,
                            chunk_index=chunk.chunk_index,
                            source_type=chunk.source_type,
                            score=chunk.score,
                        )
                        for chunk in (retrieved_context.retrieved_chunks if retrieved_context else [])
                    ],
                    page=(
                        MindPageDebug(
                            style_label=page_result.style_label,
                            intent_label=page_result.intent_label,
                            sections=page_result.sections,
                        )
                        if page_result is not None
                        else None
                    ),
                    page_input=MindDebugPageInput(
                        user_mbti=target_mbti,
                        query=query,
                        uex_knowledge=uex_knowledge_content,
                        expert_suggestion=(
                            MindDebugPageExpertSuggestion(
                                name=expert_suggestion.name,
                                domain_codes=expert_suggestion.domain_codes,
                                is_contactable=expert_suggestion.is_contactable,
                                reason=(
                                    f"Match score {expert_suggestion.total_score:.2f} based on current query routing."
                                    if expert_suggestion is not None
                                    else None
                                ),
                            )
                            if expert_suggestion is not None
                            else None
                        ),
                        ulm_grounding=(
                            MindDebugPageUlmGrounding(
                                summary=ulm_grounding.summary,
                                source_count=ulm_grounding.source_count,
                                chunk_count=ulm_grounding.chunk_count,
                                sources=[
                                    MindDebugPageUlmSource(
                                        title=source.title,
                                        chunk_index=source.chunk_index,
                                        source_type=source.source_type,
                                        url=source.url,
                                    )
                                    for source in ulm_grounding.sources
                                ],
                            )
                            if ulm_grounding is not None
                            else None
                        ),
                        ulm_used="ULM" in modules_used,
                        conversation_mode=session.mode,
                    ),
                    synapse=(
                        MindSynapseDebug(
                            stored_mbti=stored_profile.effective_mbti if stored_profile is not None else None,
                            inferred_mbti=synapse_result.mbti_type if synapse_result is not None else None,
                            effective_mbti=target_mbti,
                            confidence=synapse_result.confidence if synapse_result is not None else None,
                        )
                        if effective_use_synapse
                        else None
                    ),
                    expert_suggestion_reason=(
                        f"Match score {expert_suggestion.total_score:.2f}"
                        if expert_suggestion is not None
                        else None
                    ),
                )
                if can_include_debug
                else None
            ),
        )

    def start_session(self, *, actor_user_id: int, payload: ChatSessionStartRequest) -> ChatSessionResponse:
        user = self.db.get(User, actor_user_id)
        if user is None:
            raise LookupError("User not found.")
        if user.role != "user":
            raise PermissionError("Only users can start new conversations.")
        if payload.user_id is not None and payload.user_id != user.id:
            raise PermissionError("You cannot start a conversation for another user.")
        if payload.mode != "system":
            raise ValueError("New conversations must start in system mode.")

        assigned_expert_id = None
        initial_mode = "system"
        initial_status = "active"
        handoff_record = None

        if payload.expert_id is not None:
            general_settings = self.module_settings_service.get_general_settings()
            if not general_settings.allow_expert_handoff:
                raise ValueError("Expert handoff is currently disabled by platform settings.")

            expert = self.uex_service.get_expert(payload.expert_id)
            if not expert.is_contactable:
                raise ValueError(
                    f"This expert is available in UEX but does not have a provisioned {settings.app_public_name} expert account yet."
                )

            assigned_expert_id = payload.expert_id
            initial_mode = "expert"
            initial_status = "awaiting_expert"
            handoff_record = {
                "expert": expert,
                "reason": payload.handoff_reason,
            }

        session = ChatSession(
            user_id=user.id,
            title=payload.title,
            mode=initial_mode,
            status=initial_status,
            assigned_expert_id=assigned_expert_id,
        )
        self.db.add(session)
        self.db.flush()

        if handoff_record is not None:
            self.db.add(
                ExpertHandoff(
                    session_id=session.id,
                    expert_id=assigned_expert_id,
                    reason=handoff_record["reason"],
                    from_mode="system",
                    to_mode="expert",
                )
            )

        self.db.commit()
        self.db.refresh(session)
        return self._build_session_response(session, actor_user_id=actor_user_id)

    def close_session(self, session_id: int, actor_user_id: int | None = None) -> ChatSessionResponse:
        session = self.db.get(ChatSession, session_id)
        if session is None:
            raise LookupError("Session not found.")
        if actor_user_id is None:
            raise PermissionError("No active session.")
        self._resolve_session_actor(actor_user_id, session)
        if session.status == "closed":
            return self._build_session_response(session, actor_user_id=actor_user_id)
        session.status = "closed"
        session.closed_at = datetime.now(timezone.utc)
        closed_by_role, closed_by_name = self._resolve_session_actor(actor_user_id, session)
        session.closed_by_role = closed_by_role
        session.closed_by_name = closed_by_name
        session.typing_actor_role = None
        session.typing_updated_at = None
        self.db.commit()
        self.db.refresh(session)
        return self._build_session_response(session, actor_user_id=actor_user_id)

    def get_session(self, session_id: int, actor_user_id: int | None = None) -> ChatSessionResponse:
        session = self.db.get(ChatSession, session_id)
        if session is None:
            raise LookupError("Session not found.")
        if actor_user_id is None:
            raise PermissionError("No active session.")
        self._resolve_session_actor(actor_user_id, session)
        self._clear_stale_typing_state(session, commit=True)
        return self._build_session_response(session, actor_user_id=actor_user_id)

    def get_history(self, session_id: int, actor_user_id: int | None = None) -> ChatHistoryResponse:
        session = self.db.get(ChatSession, session_id)
        if session is None:
            raise LookupError("Session not found.")
        if actor_user_id is None:
            raise PermissionError("No active session.")
        self._resolve_session_actor(actor_user_id, session)
        statement = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.id.asc())
        )
        messages = self.db.execute(statement).scalars().all()
        if actor_user_id is not None:
            self._mark_session_seen(session, actor_user_id=actor_user_id, messages=messages)
        return ChatHistoryResponse(
            items=[ChatMessageResponse.model_validate(message) for message in messages],
            total=len(messages),
        )

    def list_sessions(self, user_id: int | None = None, actor_user_id: int | None = None) -> ChatSessionListResponse:
        if actor_user_id is None:
            raise PermissionError("No active session.")

        actor = self.db.get(User, actor_user_id)
        if actor is None:
            raise LookupError("User not found.")

        statement = select(ChatSession).order_by(ChatSession.created_at.desc(), ChatSession.id.desc())

        if actor.role == "expert":
            expert = self.expert_profile_service.find_expert_for_user(actor_user_id)
            if expert is None:
                return ChatSessionListResponse(items=[], total=0)
            statement = statement.where(ChatSession.assigned_expert_id == expert.id)
        elif actor.role == "user":
            if user_id is not None and user_id != actor.id:
                raise PermissionError("You cannot list another user's conversations.")
            statement = statement.where(ChatSession.user_id == actor.id)
        else:
            raise PermissionError("Admins should use admin chat endpoints.")

        sessions = self.db.execute(statement).scalars().all()
        changed = False
        for session in sessions:
            changed = self._clear_stale_typing_state(session) or changed
        if changed:
            self.db.commit()
        return ChatSessionListResponse(
            items=[self._build_session_response(session, actor_user_id=actor_user_id) for session in sessions],
            total=len(sessions),
        )

    def get_unread_summary(self, actor_user_id: int) -> ChatUnreadSummaryResponse:
        user = self.db.get(User, actor_user_id)
        if user is None:
            raise LookupError("User not found.")

        if user.role == "expert":
            expert = self.expert_profile_service.find_expert_for_user(actor_user_id)
            if expert is None:
                return ChatUnreadSummaryResponse(attention_count=0)
            sessions = self.db.execute(
                select(ChatSession).where(ChatSession.assigned_expert_id == expert.id)
            ).scalars().all()
        else:
            sessions = self.db.execute(
                select(ChatSession).where(ChatSession.user_id == user.id)
            ).scalars().all()

        attention_count = 0
        for session in sessions:
            _, needs_attention = self._resolve_unread_state(session, actor_user_id)
            if needs_attention:
                attention_count += 1

        return ChatUnreadSummaryResponse(attention_count=attention_count)

    def update_typing_status(self, *, actor_user_id: int, payload: ChatTypingRequest) -> ChatSessionResponse:
        session = self.db.get(ChatSession, payload.session_id)
        if session is None:
            raise LookupError("Session not found.")
        if session.status not in OPEN_CHAT_SESSION_STATUSES:
            raise ValueError("Session is closed.")

        actor_role = self._resolve_typing_actor_role(actor_user_id, session)
        if payload.is_typing:
            session.typing_actor_role = actor_role
            session.typing_updated_at = datetime.now(timezone.utc)
        elif session.typing_actor_role == actor_role:
            session.typing_actor_role = None
            session.typing_updated_at = None

        self.db.commit()
        self.db.refresh(session)
        return self._build_session_response(session, actor_user_id=actor_user_id)

    def handoff_to_expert(self, *, actor_user_id: int, payload: ChatHandoffRequest) -> ExpertHandoffResponse:
        session = self.db.get(ChatSession, payload.session_id)
        if session is None:
            raise LookupError("Session not found.")
        general_settings = self.module_settings_service.get_general_settings()
        if not general_settings.allow_expert_handoff:
            raise ValueError("Expert handoff is currently disabled by platform settings.")
        actor_role, _ = self._resolve_session_actor(actor_user_id, session)
        if actor_role != "user":
            raise PermissionError("Only the conversation owner can hand off a conversation.")
        if session.status not in OPEN_CHAT_SESSION_STATUSES:
            raise ValueError("This conversation is closed and cannot be reopened.")
        if session.mode == "expert":
            raise ValueError("This conversation is already in expert mode.")
        if session.mode != "system":
            raise ValueError("Only system-mode conversations can be handed off.")
        expert = self.uex_service.get_expert(payload.expert_id)
        if not expert.is_contactable:
            raise ValueError(
                f"This expert is available in UEX but does not have a provisioned {settings.app_public_name} expert account yet."
            )

        handoff = ExpertHandoff(
            session_id=session.id,
            expert_id=payload.expert_id,
            reason=payload.reason,
            from_mode=session.mode,
            to_mode="expert",
        )
        session.mode = "expert"
        session.status = "awaiting_expert"
        session.assigned_expert_id = payload.expert_id
        self.db.add(handoff)
        self.db.commit()
        self.db.refresh(handoff)
        return ExpertHandoffResponse.model_validate(handoff)

    def post_expert_message(self, *, expert_user_id: int, payload: ExpertChatMessageRequest) -> ExpertChatMessageResponse:
        session = self.db.get(ChatSession, payload.session_id)
        if session is None:
            raise LookupError("Session not found.")
        if session.status not in OPEN_CHAT_SESSION_STATUSES:
            raise ValueError("Session is closed.")
        if session.mode != "expert":
            raise ValueError("Session is not in expert mode.")

        expert = self.expert_profile_service.find_expert_for_user(expert_user_id)
        if expert is None:
            raise LookupError("Expert record not found for the current user.")
        if session.assigned_expert_id != expert.id:
            raise ValueError("This conversation is not assigned to the current expert.")

        message = self._store_chat_message(
            session_id=session.id,
            role="expert",
            mode="expert",
            content=payload.content.strip(),
            commit=False,
        )
        session.typing_actor_role = None
        session.typing_updated_at = None
        session.status = "awaiting_user"
        self.db.commit()
        self.db.refresh(message)

        expert_profile_updated = False
        if self.synapse_service is not None:
            self.expert_profile_service.process_interaction(
                expert_id=expert.id,
                message_text=payload.content,
                synapse_service=self.synapse_service,
            )
            expert_profile_updated = True

        return ExpertChatMessageResponse(
            message=ChatMessageResponse.model_validate(message),
            expert_profile_updated=expert_profile_updated,
        )

    def _infer_user_profile(self, query: str) -> SynapseInferenceResult:
        if self.synapse_service is None:
            raise RuntimeError("SYNAPSE service is not configured.")
        return self.synapse_service.infer(query)

    def _record_user_interaction(self, user_id: int | None, query: str):
        if user_id is None:
            return None
        return self.user_profile_service.process_chat_interaction(user_id, query, self.synapse_service)

    def _resolve_user_profile(self, query: str, stored_mbti: str | None) -> SynapseInferenceResult:
        if stored_mbti:
            live_result = self._infer_user_profile(query)
            live_result.mbti_type = stored_mbti
            return live_result
        return self._infer_user_profile(query)

    def _can_expose_chat_debug_panels(
        self,
        actor_user: User,
        *,
        general_settings=None,
    ) -> bool:
        state = general_settings or self.module_settings_service.get_general_settings()
        if not state.show_chat_debug_panels:
            return False
        return actor_user.role == "admin" or bool(actor_user.can_access_chat_debug_panels)

    def _build_expert_suggestion(
        self,
        matches: ExpertMatchResponse,
    ) -> ExpertSuggestion | None:
        if not matches.items:
            return None
        top = matches.items[0]
        return ExpertSuggestion(
            expert_id=top.expert_id,
            name=top.name,
            total_score=top.total_score,
            is_contactable=top.is_contactable,
            domain_codes=top.domain_codes,
        )

    def _compose_non_page_response(
        self,
        *,
        query: str,
        uex_knowledge: str,
        expert_suggestion: ExpertSuggestion | None,
        ulm_summary: str | None,
        ulm_used: bool,
    ) -> str:
        knowledge_text = (uex_knowledge or "").strip()
        if knowledge_text:
            primary = knowledge_text.splitlines()[0].strip()
        else:
            primary = "No strong knowledge context was available, so the response should stay focused on clarifying the request."

        parts = [primary]
        parts.append(
            f"Next step: clarify the specific details behind '{query.strip()[:120]}' and continue from the most relevant guidance above."
        )

        if expert_suggestion is not None:
            contact_note = (
                f"can be contacted through {settings.app_public_name}"
                if expert_suggestion.is_contactable
                else f"is not contactable through {settings.app_public_name} yet"
            )
            parts.append(f"Expert option: {expert_suggestion.name} looks relevant and {contact_note}.")

        if ulm_used and ulm_summary:
            parts.append(f"Grounding note: {ulm_summary[:220].strip()}")

        return "\n\n".join(parts)

    def _store_log(
        self,
        *,
        session_id: int,
        query: str,
        final_response: str,
        modules_used: list[str],
        expert_suggestion: ExpertSuggestion | None,
    ) -> None:
        log = MindChatLog(
            session_id=session_id,
            query=query,
            final_response=final_response,
            modules_used=modules_used,
            expert_suggestion=expert_suggestion.model_dump() if expert_suggestion else None,
        )
        self.db.add(log)
        self.db.commit()

    def _store_chat_message(self, *, session_id: int, role: str, mode: str, content: str, commit: bool = True):
        message = ChatMessage(
            session_id=session_id,
            role=role,
            mode=mode,
            content=content,
        )
        self.db.add(message)
        if commit:
            self.db.commit()
            self.db.refresh(message)
        return message

    def _resolve_typing_actor_role(self, actor_user_id: int, session: ChatSession) -> str:
        user = self.db.get(User, actor_user_id)
        if user is None:
            raise LookupError("User not found.")

        if user.role == "expert":
            expert = self.expert_profile_service.find_expert_for_user(actor_user_id)
            if expert is None or session.assigned_expert_id != expert.id:
                raise ValueError("This conversation is not assigned to the current expert.")
            return "expert"

        if session.user_id != user.id:
            raise ValueError("This conversation is not assigned to the current user.")
        return "user"

    def _clear_stale_typing_state(self, session: ChatSession, *, commit: bool = False) -> bool:
        if not session.typing_actor_role or session.typing_updated_at is None:
            return False

        typing_updated_at = session.typing_updated_at
        if typing_updated_at.tzinfo is None:
            typing_updated_at = typing_updated_at.replace(tzinfo=timezone.utc)

        cutoff = datetime.now(timezone.utc) - timedelta(seconds=settings.chat_typing_ttl_seconds)
        if typing_updated_at >= cutoff:
            return False

        session.typing_actor_role = None
        session.typing_updated_at = None
        if commit:
            self.db.commit()
        return True

    def _mark_session_seen(
        self,
        session: ChatSession,
        *,
        actor_user_id: int,
        messages: list[ChatMessage],
    ) -> None:
        actor_role, _ = self._resolve_session_actor(actor_user_id, session)
        if not messages:
            return

        latest_message_id = messages[-1].id
        if actor_role == "expert":
            if session.expert_last_seen_message_id == latest_message_id:
                return
            session.expert_last_seen_message_id = latest_message_id
        else:
            if session.user_last_seen_message_id == latest_message_id:
                return
            session.user_last_seen_message_id = latest_message_id

        self.db.commit()

    def _resolve_unread_state(self, session: ChatSession, actor_user_id: int) -> tuple[int, bool]:
        actor_role, _ = self._resolve_session_actor(actor_user_id, session)
        counterpart_role = "user" if actor_role == "expert" else "expert"
        last_seen_id = session.expert_last_seen_message_id if actor_role == "expert" else session.user_last_seen_message_id

        unread_count = self.db.execute(
            select(func.count(ChatMessage.id)).where(
                ChatMessage.session_id == session.id,
                ChatMessage.role == counterpart_role,
                ChatMessage.id > (last_seen_id or 0),
            )
        ).scalar_one()

        unread_count = int(unread_count or 0)
        return unread_count, unread_count > 0

    def _build_session_response(self, session: ChatSession, actor_user_id: int | None = None) -> ChatSessionResponse:
        user_name = None
        assigned_expert_name = None
        feedback_mode = "interaction" if session.mode == "expert" or session.assigned_expert_id is not None else "system"
        feedback_pending_for_current_user = False
        unread_message_count = 0
        needs_attention = False
        latest_message = (
            self.db.execute(
                select(ChatMessage)
                .where(ChatMessage.session_id == session.id)
                .order_by(ChatMessage.id.desc())
                .limit(1)
            )
            .scalars()
            .first()
        )

        if session.user_id is not None:
            user = self.db.get(User, session.user_id)
            user_name = user.name if user is not None else None

        if session.assigned_expert_id is not None:
            expert = self.db.get(Expert, session.assigned_expert_id)
            assigned_expert_name = expert.name if expert is not None else None

        if actor_user_id is not None and session.status == "closed":
            actor_role, _ = self._resolve_session_actor(actor_user_id, session)
            existing_feedback = (
                self.db.query(FeedbackEntry)
                .filter(
                    FeedbackEntry.session_id == session.id,
                    FeedbackEntry.feedback_type == feedback_mode,
                    FeedbackEntry.submitted_by_role == actor_role,
                )
                .one_or_none()
            )
            feedback_pending_for_current_user = existing_feedback is None

        if actor_user_id is not None:
            unread_message_count, needs_attention = self._resolve_unread_state(session, actor_user_id)

        last_message_at = latest_message.created_at if latest_message is not None else None
        last_activity_at = max(
            [
                value
                for value in [last_message_at, session.typing_updated_at, session.closed_at, session.created_at]
                if value is not None
            ],
            default=session.created_at,
        )

        return ChatSessionResponse(
            id=session.id,
            user_id=session.user_id,
            user_name=user_name,
            title=session.title,
            mode=session.mode,
            status=session.status,
            assigned_expert_id=session.assigned_expert_id,
            assigned_expert_name=assigned_expert_name,
            created_at=session.created_at,
            closed_at=session.closed_at,
            closed_by_role=session.closed_by_role,
            closed_by_name=session.closed_by_name,
            typing_actor_role=session.typing_actor_role,
            typing_updated_at=session.typing_updated_at,
            feedback_mode=feedback_mode,
            feedback_pending_for_current_user=feedback_pending_for_current_user,
            last_message_at=last_message_at,
            last_activity_at=last_activity_at,
            last_message_role=latest_message.role if latest_message is not None else None,
            last_message_preview=(
                latest_message.content.strip()[:160]
                if latest_message is not None and latest_message.content
                else None
            ),
            unread_message_count=unread_message_count,
            needs_attention=needs_attention,
        )

    def _notify_expert_about_session_message(self, *, session: ChatSession) -> None:
        if session.assigned_expert_id is None:
            return

        expert = self.uex_service.get_expert(session.assigned_expert_id)
        if not expert.email:
            return

        user_name = "Unknown user"
        if session.user_id is not None:
            user = self.db.get(User, session.user_id)
            if user is not None:
                user_name = user.name

        self.email_service.send_expert_handoff_email(
            expert.email,
            expert_name=expert.name,
            user_name=user_name,
            session_id=session.id,
            session_title=session.title,
            reason="The user sent the first message after expert handoff.",
        )

    def _should_notify_expert_on_first_user_message(self, session_id: int) -> bool:
        existing_user_message_count = int(
            self.db.execute(
                select(func.count(ChatMessage.id)).where(
                    ChatMessage.session_id == session_id,
                    ChatMessage.role == "user",
                    ChatMessage.mode == "expert",
                )
            ).scalar_one()
            or 0
        )
        return existing_user_message_count == 0

    def _resolve_session_actor(self, actor_user_id: int, session: ChatSession) -> tuple[str, str]:
        user = self.db.get(User, actor_user_id)
        if user is None:
            raise LookupError("User not found.")

        if user.role == "expert":
            expert = self.expert_profile_service.find_expert_for_user(actor_user_id)
            if expert is None or session.assigned_expert_id != expert.id:
                raise ValueError("This conversation is not assigned to the current expert.")
            return "expert", expert.name

        if session.user_id != user.id:
            raise ValueError("This conversation is not assigned to the current user.")
        return "user", user.name
