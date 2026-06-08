from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.module import ModuleStatusResponse
from app.schemas.user import UserRecommendedExpertResponse
from app.services.user import UserService, UserServiceError

router = APIRouter()


def build_error_response(exc: UserServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "details": exc.details,
        },
    )


@router.get("", response_model=ModuleStatusResponse, summary="User module status")
def get_user_status() -> ModuleStatusResponse:
    return ModuleStatusResponse(module="USER")


@router.get("/dashboard/recommended-expert", response_model=UserRecommendedExpertResponse)
def get_recommended_expert(
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
) -> UserRecommendedExpertResponse:
    try:
        return UserService(db, request.session).get_recommended_expert()
    except UserServiceError as exc:
        return build_error_response(exc)
