from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.expert import ExpertAssignedSessionListResponse, ExpertDashboardSummaryResponse
from app.schemas.module import ModuleStatusResponse
from app.services.expert import ExpertService, ExpertServiceError

router = APIRouter()


def build_error_response(exc: ExpertServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "details": exc.details,
        },
    )


@router.get("", response_model=ModuleStatusResponse, summary="Expert module status")
def get_expert_status() -> ModuleStatusResponse:
    return ModuleStatusResponse(module="EXPERT")


@router.get("/dashboard", response_model=ExpertDashboardSummaryResponse)
def get_dashboard_summary(
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
) -> ExpertDashboardSummaryResponse:
    try:
        return ExpertService(db, request.session).get_dashboard_summary()
    except ExpertServiceError as exc:
        return build_error_response(exc)


@router.get("/chat-sessions", response_model=ExpertAssignedSessionListResponse)
def list_assigned_sessions(
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
) -> ExpertAssignedSessionListResponse:
    try:
        items = ExpertService(db, request.session).list_assigned_sessions()
        return ExpertAssignedSessionListResponse(items=items, total=len(items))
    except ExpertServiceError as exc:
        return build_error_response(exc)
