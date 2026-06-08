from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.health import HealthCheckResponse

router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse, summary="Health check")
def health_check(
    db: Annotated[Session, Depends(get_db_session)],
) -> HealthCheckResponse:
    del db
    return HealthCheckResponse(status="ok")
