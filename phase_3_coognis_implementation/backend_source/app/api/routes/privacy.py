from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.api.security import validate_session_write_request
from app.schemas.privacy import (
    AccountDeletionRequestCreate,
    AdminDataRequestActionResponse,
    AdminDataRequestItemResponse,
    ConsentUpdateRequest,
    PrivacyActionResponse,
)
from app.services.privacy import PrivacyService

router = APIRouter()

ROLE_PERMISSIONS = {
    "viewer": {"GET"},
    "editor": {"GET", "POST", "PUT"},
    "admin": {"GET", "POST", "PUT", "DELETE"},
}


def require_admin_role(
    method: str,
    x_admin_role: Annotated[str | None, Header(alias="X-Admin-Role")] = None,
) -> str:
    role = (x_admin_role or "").lower()
    if role not in ROLE_PERMISSIONS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required.")
    if method not in ROLE_PERMISSIONS[role]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient admin role.")
    return role


def get_authenticated_user_id(request: Request) -> int:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No active session.")
    return int(user_id)


@router.patch("/user/privacy/consent", response_model=PrivacyActionResponse)
def update_consent_settings(
    payload: ConsentUpdateRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
) -> PrivacyActionResponse:
    validate_session_write_request(request)
    user_id = get_authenticated_user_id(request)
    try:
        return PrivacyService(db).update_consent_settings(user_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/user/privacy/deletion-request", response_model=PrivacyActionResponse)
def request_account_deletion(
    payload: AccountDeletionRequestCreate,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
) -> PrivacyActionResponse:
    validate_session_write_request(request)
    user_id = get_authenticated_user_id(request)
    try:
        return PrivacyService(db).request_account_deletion(user_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/admin/data-requests", response_model=list[AdminDataRequestItemResponse])
def list_data_requests(
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("GET", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> list[AdminDataRequestItemResponse]:
    return PrivacyService(db).list_data_requests()


@router.get("/admin/data-requests/{id}", response_model=AdminDataRequestItemResponse)
def get_data_request(
    id: int,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("GET", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> AdminDataRequestItemResponse:
    try:
        return PrivacyService(db).get_data_request(id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/admin/data-requests/{id}/complete", response_model=AdminDataRequestActionResponse)
def complete_data_request(
    id: int,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("POST", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> AdminDataRequestActionResponse:
    try:
        return PrivacyService(db).complete_data_request(id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/admin/data-requests/{id}/reject", response_model=AdminDataRequestActionResponse)
def reject_data_request(
    id: int,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("POST", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> AdminDataRequestActionResponse:
    try:
        return PrivacyService(db).reject_data_request(id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
