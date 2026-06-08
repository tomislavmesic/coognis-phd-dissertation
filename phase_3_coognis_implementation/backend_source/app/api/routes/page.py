from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.api.security import validate_session_write_request
from app.models import User
from app.schemas.module import ModuleStatusResponse
from app.schemas.page import PageRespondRequest, PageRespondResponse
from app.services.local_llm import LocalLlmClient
from app.services.module_settings import ModuleSettingsService
from app.services.page import PageService, get_page_llm_client

router = APIRouter()


@router.get("", response_model=ModuleStatusResponse, summary="PAGE module status")
def get_page_status() -> ModuleStatusResponse:
    return ModuleStatusResponse(module="PAGE")


@router.post("/respond", response_model=PageRespondResponse)
def respond(
    payload: PageRespondRequest,
    request: Request,
    llm_client: Annotated[LocalLlmClient, Depends(get_page_llm_client)],
    db: Annotated[Session, Depends(get_db_session)],
) -> PageRespondResponse:
    validate_session_write_request(request)
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No active session.")

    user = db.get(User, int(user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    general_settings = ModuleSettingsService(db).get_general_settings()
    can_access_debug = general_settings.show_chat_debug_panels and (
        user.role == "admin" or user.can_access_chat_debug_panels
    )
    if not can_access_debug:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chat debug panels are not enabled for this account.",
        )

    service = PageService()
    return service.respond(payload, llm_client)
