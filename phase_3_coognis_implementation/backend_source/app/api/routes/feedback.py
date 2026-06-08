from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.api.security import validate_session_write_request
from app.schemas.feedback import FeedbackCreateRequest, FeedbackResponse
from app.schemas.module import ModuleStatusResponse
from app.services.feedback import FeedbackService

router = APIRouter()


@router.get("", response_model=ModuleStatusResponse, summary="FEEDBACK module status")
def get_feedback_status() -> ModuleStatusResponse:
    return ModuleStatusResponse(module="FEEDBACK")


@router.post("/response", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_response_feedback(
    payload: FeedbackCreateRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
) -> FeedbackResponse:
    validate_session_write_request(request)
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No active session.")
    service = FeedbackService(db)
    try:
        return service.create_feedback("response", int(user_id), payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/interaction", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_interaction_feedback(
    payload: FeedbackCreateRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
) -> FeedbackResponse:
    validate_session_write_request(request)
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No active session.")
    service = FeedbackService(db)
    try:
        return service.create_feedback("interaction", int(user_id), payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/system", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_system_feedback(
    payload: FeedbackCreateRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
) -> FeedbackResponse:
    validate_session_write_request(request)
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No active session.")
    service = FeedbackService(db)
    try:
        return service.create_feedback("system", int(user_id), payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
