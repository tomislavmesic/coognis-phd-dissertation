from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.admin import (
    AdminChatSessionResponse,
    AdminConversationDetailResponse,
    AdminConversationHandoffResponse,
    AdminConversationOverviewResponse,
    AdminDashboardResponse,
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
    UlmSourceAdminResponse,
    UlmSourceAdminUpdateRequest,
    UserCreateRequest,
    UserCredentialActionResponse,
    UserResponse,
    UserUpdateRequest,
)
from app.schemas.module import ModuleStatusResponse
from app.services.admin import AdminService

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


@router.get("", response_model=ModuleStatusResponse, summary="ADMIN module status")
def get_admin_status(
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("GET", x_admin_role))]
) -> ModuleStatusResponse:
    return ModuleStatusResponse(module="ADMIN")


@router.get("/dashboard", response_model=AdminDashboardResponse)
def get_dashboard_summary(
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("GET", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> AdminDashboardResponse:
    return AdminService(db).get_dashboard_summary()


@router.post("/two-factor/bulk", response_model=BulkTwoFactorUpdateResponse)
def bulk_update_two_factor(
    payload: BulkTwoFactorUpdateRequest,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("POST", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> BulkTwoFactorUpdateResponse:
    try:
        return AdminService(db).bulk_update_two_factor(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/registrations", response_model=list[RegistrationQueueItemResponse])
def list_pending_registrations(
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("GET", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> list[RegistrationQueueItemResponse]:
    return AdminService(db).list_pending_registrations()


@router.post("/registrations/{id}/approve", response_model=RegistrationApprovalActionResponse)
def approve_registration(
    id: int,
    payload: RegistrationApprovalActionRequest,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("POST", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> RegistrationApprovalActionResponse:
    try:
        return AdminService(db).approve_registration(id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/registrations/{id}/reject", response_model=RegistrationApprovalActionResponse)
def reject_registration(
    id: int,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("POST", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> RegistrationApprovalActionResponse:
    try:
        return AdminService(db).reject_registration(id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/users", response_model=list[UserResponse])
def list_users(
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("GET", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> list[UserResponse]:
    return AdminService(db).list_users()


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateRequest,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("POST", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> UserResponse:
    try:
        return AdminService(db).create_user(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/users/{id}", response_model=UserResponse)
def get_user(
    id: int,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("GET", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> UserResponse:
    try:
        return AdminService(db).get_user(id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/users/{id}", response_model=UserResponse)
def update_user(
    id: int,
    payload: UserUpdateRequest,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("PUT", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> UserResponse:
    try:
        return AdminService(db).update_user(id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/users/{id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_user(
    id: int,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("DELETE", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> Response:
    try:
        AdminService(db).delete_user(id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/chat-sessions/{id}", response_model=ChatSessionDeleteResponse)
def delete_chat_session(
    id: int,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("DELETE", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> ChatSessionDeleteResponse:
    try:
        return AdminService(db).delete_chat_session(id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/chat-sessions", response_model=list[AdminChatSessionResponse])
def list_deletable_chat_sessions(
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("GET", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> list[AdminChatSessionResponse]:
    return AdminService(db).list_deletable_chat_sessions()


@router.get("/conversations", response_model=list[AdminConversationOverviewResponse])
def list_conversations(
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("GET", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> list[AdminConversationOverviewResponse]:
    return AdminService(db).list_conversations()


@router.get("/conversations/{id}", response_model=AdminConversationDetailResponse)
def get_conversation(
    id: int,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("GET", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> AdminConversationDetailResponse:
    try:
        return AdminService(db).get_conversation(id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/handoffs", response_model=list[AdminConversationHandoffResponse])
def list_handoffs(
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("GET", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> list[AdminConversationHandoffResponse]:
    return AdminService(db).list_handoffs()


@router.post("/users/{id}/reset-password", response_model=UserCredentialActionResponse)
def reset_user_password(
    id: int,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("POST", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> UserCredentialActionResponse:
    try:
        return AdminService(db).reset_user_password(id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/users/{id}/resend-credentials", response_model=UserCredentialActionResponse)
def resend_user_credentials(
    id: int,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("POST", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> UserCredentialActionResponse:
    try:
        return AdminService(db).resend_user_credentials(id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/users/{id}/reset-two-factor", response_model=UserCredentialActionResponse)
def reset_user_two_factor(
    id: int,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("POST", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> UserCredentialActionResponse:
    try:
        return AdminService(db).reset_user_two_factor(id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/users/{id}/trusted-devices", response_model=list[TrustedDeviceAdminResponse])
def list_user_trusted_devices(
    id: int,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("GET", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> list[TrustedDeviceAdminResponse]:
    try:
        return AdminService(db).list_user_trusted_devices(id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/users/{id}/trusted-devices/{device_id}/revoke", response_model=UserCredentialActionResponse)
def revoke_user_trusted_device(
    id: int,
    device_id: int,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("POST", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> UserCredentialActionResponse:
    try:
        return AdminService(db).revoke_user_trusted_device(id, device_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/users/{id}/trusted-devices/revoke-all", response_model=UserCredentialActionResponse)
def revoke_all_user_trusted_devices(
    id: int,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("POST", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> UserCredentialActionResponse:
    try:
        return AdminService(db).revoke_all_user_trusted_devices(id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/experts", response_model=list[ExpertAdminResponse])
def list_experts(
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("GET", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> list[ExpertAdminResponse]:
    return AdminService(db).list_experts()


@router.get("/domains", response_model=list[DomainOptionResponse])
def list_domain_options(
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("GET", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> list[DomainOptionResponse]:
    return AdminService(db).list_domain_options()


@router.get("/module-settings", response_model=ModuleSettingsResponse)
def get_module_settings(
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("GET", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> ModuleSettingsResponse:
    return AdminService(db).get_module_settings()


@router.put("/module-settings", response_model=ModuleSettingsResponse)
def update_module_settings(
    payload: ModuleSettingsUpdateRequest,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("PUT", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> ModuleSettingsResponse:
    try:
        return AdminService(db).update_module_settings(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/general-settings", response_model=GeneralSettingsResponse)
def get_general_settings(
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("GET", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> GeneralSettingsResponse:
    return AdminService(db).get_general_settings()


@router.put("/general-settings", response_model=GeneralSettingsResponse)
def update_general_settings(
    payload: GeneralSettingsUpdateRequest,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("PUT", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> GeneralSettingsResponse:
    return AdminService(db).update_general_settings(payload)


@router.post("/experts", response_model=ExpertAdminResponse, status_code=status.HTTP_201_CREATED)
def create_expert(
    payload: ExpertAdminCreateRequest,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("POST", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> ExpertAdminResponse:
    return AdminService(db).create_expert(payload)


@router.get("/experts/{id}", response_model=ExpertAdminResponse)
def get_expert(
    id: int,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("GET", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> ExpertAdminResponse:
    try:
        return AdminService(db).get_expert(id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/experts/{id}", response_model=ExpertAdminResponse)
def update_expert(
    id: int,
    payload: ExpertAdminUpdateRequest,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("PUT", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> ExpertAdminResponse:
    try:
        return AdminService(db).update_expert(id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/experts/{id}/provision-account", response_model=ExpertProvisionResponse)
def provision_expert_account(
    id: int,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("POST", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> ExpertProvisionResponse:
    try:
        return AdminService(db).provision_expert_account(id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/experts/{id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_expert(
    id: int,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("DELETE", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> Response:
    try:
        AdminService(db).delete_expert(id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/knowledge", response_model=list[KnowledgeAdminResponse])
def list_knowledge(
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("GET", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> list[KnowledgeAdminResponse]:
    return AdminService(db).list_knowledge()


@router.post("/knowledge", response_model=KnowledgeAdminResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge(
    payload: KnowledgeAdminCreateRequest,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("POST", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> KnowledgeAdminResponse:
    return AdminService(db).create_knowledge(payload)


@router.get("/knowledge/{id}", response_model=KnowledgeAdminResponse)
def get_knowledge(
    id: int,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("GET", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> KnowledgeAdminResponse:
    try:
        return AdminService(db).get_knowledge(id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/knowledge/{id}", response_model=KnowledgeAdminResponse)
def update_knowledge(
    id: int,
    payload: KnowledgeAdminUpdateRequest,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("PUT", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> KnowledgeAdminResponse:
    try:
        return AdminService(db).update_knowledge(id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/knowledge/{id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_knowledge(
    id: int,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("DELETE", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> Response:
    try:
        AdminService(db).delete_knowledge(id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/profiles", response_model=list[ProfileAdminResponse])
def list_profiles(
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("GET", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> list[ProfileAdminResponse]:
    return AdminService(db).list_profiles()


@router.post("/profiles", response_model=ProfileAdminResponse, status_code=status.HTTP_201_CREATED)
def create_profile(
    payload: ProfileAdminCreateRequest,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("POST", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> ProfileAdminResponse:
    return AdminService(db).create_profile(payload)


@router.get("/profiles/{id}", response_model=ProfileAdminResponse)
def get_profile(
    id: int,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("GET", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> ProfileAdminResponse:
    try:
        return AdminService(db).get_profile(id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/profiles/{id}", response_model=ProfileAdminResponse)
def update_profile(
    id: int,
    payload: ProfileAdminUpdateRequest,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("PUT", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> ProfileAdminResponse:
    try:
        return AdminService(db).update_profile(id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/profiles/{id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_profile(
    id: int,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("DELETE", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> Response:
    try:
        AdminService(db).delete_profile(id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/ulm-sources", response_model=list[UlmSourceAdminResponse])
def list_ulm_sources(
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("GET", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> list[UlmSourceAdminResponse]:
    return AdminService(db).list_ulm_sources()


@router.post("/ulm-sources", response_model=UlmSourceAdminResponse, status_code=status.HTTP_201_CREATED)
def create_ulm_source(
    payload: UlmSourceAdminCreateRequest,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("POST", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> UlmSourceAdminResponse:
    try:
        return AdminService(db).create_ulm_source(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/ulm-sources/upload", response_model=UlmSourceAdminResponse, status_code=status.HTTP_201_CREATED)
async def upload_ulm_source(
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("POST", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
) -> UlmSourceAdminResponse:
    try:
        content_bytes = await file.read()
        return AdminService(db).ingest_ulm_source_upload(
            filename=file.filename or "uploaded-document",
            content_bytes=content_bytes,
            title=title,
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/ulm-sources/{id}", response_model=UlmSourceAdminDetailResponse)
def get_ulm_source(
    id: int,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("GET", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> UlmSourceAdminDetailResponse:
    try:
        return AdminService(db).get_ulm_source(id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/ulm-sources/{id}", response_model=UlmSourceAdminResponse)
def update_ulm_source(
    id: int,
    payload: UlmSourceAdminUpdateRequest,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("PUT", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> UlmSourceAdminResponse:
    try:
        return AdminService(db).update_ulm_source(id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/ulm-sources/{id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_ulm_source(
    id: int,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("DELETE", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> Response:
    try:
        AdminService(db).delete_ulm_source(id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/ulm-sources/{id}/refresh", response_model=UlmSourceAdminDetailResponse)
def refresh_ulm_source(
    id: int,
    _: Annotated[str, Depends(lambda x_admin_role=Header(default=None, alias="X-Admin-Role"): require_admin_role("POST", x_admin_role))],
    db: Annotated[Session, Depends(get_db_session)],
) -> UlmSourceAdminDetailResponse:
    try:
        return AdminService(db).refresh_ulm_source(id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
