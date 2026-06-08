from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.api.security import validate_session_write_request
from app.schemas.mind import (
    ChatHistoryResponse,
    ChatHandoffRequest,
    ChatSessionListResponse,
    ChatSessionCloseRequest,
    ChatSessionResponse,
    ChatSessionStartRequest,
    ChatUnreadSummaryResponse,
    ChatTypingRequest,
    ExpertChatMessageRequest,
    ExpertChatMessageResponse,
    ExpertHandoffResponse,
    MindChatMessageRequest,
    MindChatMessageResponse,
)
from app.schemas.module import ModuleStatusResponse
from app.services.local_llm import LocalLlmClient
from app.services.mind import MindService
from app.services.page import PageService, get_page_llm_client, get_page_service
from app.services.synapse import SynapseService, get_synapse_service
from app.services.uex import UexService
from app.services.ulm import UlmService, get_llm_client

router = APIRouter()


@router.get("", response_model=ModuleStatusResponse, summary="MIND module status")
def get_mind_status() -> ModuleStatusResponse:
    return ModuleStatusResponse(module="MIND")


def build_mind_service(
    db: Session,
    synapse_service: SynapseService,
    page_service: PageService,
    page_llm_client: LocalLlmClient,
    ulm_llm_client: LocalLlmClient,
) -> MindService:
    return MindService(
        db=db,
        synapse_service=synapse_service,
        uex_service=UexService(db),
        ulm_service=UlmService(db),
        page_service=page_service,
        ulm_llm_client=ulm_llm_client,
        page_llm_client=page_llm_client,
    )


def build_mind_lifecycle_service(db: Session) -> MindService:
    return MindService(
        db=db,
        synapse_service=None,
        uex_service=UexService(db),
        ulm_service=None,
        page_service=None,
        ulm_llm_client=None,
        page_llm_client=None,
    )


@router.post("/chat/start", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
def start_chat(
    payload: ChatSessionStartRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
) -> ChatSessionResponse:
    validate_session_write_request(request)
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No active session.")

    try:
        return build_mind_lifecycle_service(db).start_session(actor_user_id=int(user_id), payload=payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/chat/close", response_model=ChatSessionResponse)
def close_chat(
    payload: ChatSessionCloseRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
) -> ChatSessionResponse:
    validate_session_write_request(request)
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No active session.")

    mind_service = build_mind_lifecycle_service(db)
    try:
        return mind_service.close_session(payload.session_id, actor_user_id=int(user_id))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/chat/typing", response_model=ChatSessionResponse)
def update_chat_typing(
    payload: ChatTypingRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
) -> ChatSessionResponse:
    validate_session_write_request(request)
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No active session.")

    mind_service = build_mind_lifecycle_service(db)
    try:
        return mind_service.update_typing_status(actor_user_id=int(user_id), payload=payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/chat/handoff", response_model=ExpertHandoffResponse)
def handoff_chat(
    payload: ChatHandoffRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
) -> ExpertHandoffResponse:
    validate_session_write_request(request)
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No active session.")

    mind_service = build_mind_lifecycle_service(db)
    try:
        return mind_service.handoff_to_expert(actor_user_id=int(user_id), payload=payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/chat", response_model=ChatSessionListResponse)
def list_chats(
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
    user_id: int | None = None,
) -> ChatSessionListResponse:
    actor_user_id = request.session.get("user_id")
    if not actor_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No active session.")

    try:
        return build_mind_lifecycle_service(db).list_sessions(user_id, actor_user_id=int(actor_user_id))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/chat/unread-summary", response_model=ChatUnreadSummaryResponse)
def get_chat_unread_summary(
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
) -> ChatUnreadSummaryResponse:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No active session.")

    mind_service = build_mind_lifecycle_service(db)
    try:
        return mind_service.get_unread_summary(int(user_id))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/chat/{id}", response_model=ChatSessionResponse)
def get_chat(
    id: int,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
) -> ChatSessionResponse:
    user_id = request.session.get("user_id")
    mind_service = build_mind_lifecycle_service(db)
    try:
        return mind_service.get_session(id, actor_user_id=int(user_id) if user_id else None)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/chat/{id}/history", response_model=ChatHistoryResponse)
def get_chat_history(
    id: int,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
) -> ChatHistoryResponse:
    actor_user_id = request.session.get("user_id")
    mind_service = build_mind_lifecycle_service(db)
    try:
        return mind_service.get_history(id, actor_user_id=int(actor_user_id) if actor_user_id else None)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/chat/message", response_model=MindChatMessageResponse)
def chat_message(
    payload: MindChatMessageRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
    synapse_service: Annotated[SynapseService, Depends(get_synapse_service)],
    page_service: Annotated[PageService, Depends(get_page_service)],
    page_llm_client: Annotated[LocalLlmClient, Depends(get_page_llm_client)],
    ulm_llm_client: Annotated[LocalLlmClient, Depends(get_llm_client)],
) -> MindChatMessageResponse:
    validate_session_write_request(request)
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No active session.")

    mind_service = build_mind_service(db, synapse_service, page_service, page_llm_client, ulm_llm_client)
    try:
        return mind_service.respond(
            actor_user_id=int(user_id),
            session_id=payload.session_id,
            query=payload.query,
            use_synapse=payload.use_synapse,
            use_uex=payload.use_uex,
            use_ulm=payload.use_ulm,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/chat/expert-message", response_model=ExpertChatMessageResponse)
def expert_chat_message(
    payload: ExpertChatMessageRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
    synapse_service: Annotated[SynapseService, Depends(get_synapse_service)],
) -> ExpertChatMessageResponse:
    validate_session_write_request(request)
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No active session.")

    mind_service = MindService(
        db=db,
        synapse_service=synapse_service,
        uex_service=UexService(db),
        ulm_service=None,
        page_service=None,
        ulm_llm_client=None,
        page_llm_client=None,
    )
    try:
        return mind_service.post_expert_message(expert_user_id=int(user_id), payload=payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
