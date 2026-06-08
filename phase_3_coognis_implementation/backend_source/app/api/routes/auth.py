from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.api.security import validate_request_origin
from app.schemas.auth import (
    CurrentUserResponse,
    CurrentUserUpdateRequest,
    LoginRequest,
    LoginResponse,
    LoginTwoFactorResponse,
    LogoutResponse,
    PasswordResetRequest,
    PasswordResetConfirmRequest,
    PasswordChangeRequest,
    PasswordResetResponse,
    RegisterRequest,
    RegisterResponse,
    TwoFactorConfirmRequest,
    TwoFactorConfirmResponse,
    TwoFactorRecoveryCodesResponse,
    TwoFactorSetupResponse,
    VerifyTwoFactorRequest,
)
from app.schemas.module import ModuleStatusResponse
from app.services.auth import AuthService, AuthServiceError

router = APIRouter()


def apply_trusted_device_cookie(response: Response, service: AuthService) -> None:
    if service.trusted_device_cookie_to_set:
        response.set_cookie(
            key=service.trusted_device_cookie_name,
            value=str(service.trusted_device_cookie_to_set["value"]),
            max_age=int(service.trusted_device_cookie_to_set["max_age"]),
            httponly=True,
            secure=service.trusted_device_https_only,
            samesite=service.trusted_device_same_site,
            path="/",
        )
    elif service.clear_trusted_device_cookie:
        response.delete_cookie(
            key=service.trusted_device_cookie_name,
            path="/",
            samesite=service.trusted_device_same_site,
        )


def build_error_response(exc: AuthServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "details": exc.details,
        },
    )


@router.get("", response_model=ModuleStatusResponse, summary="AUTH module status")
def get_auth_status() -> ModuleStatusResponse:
    return ModuleStatusResponse(module="AUTH")


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
) -> RegisterResponse:
    validate_request_origin(request)
    try:
        return AuthService(db, request.session).register(payload)
    except AuthServiceError as exc:
        return build_error_response(exc)


@router.post("/login", response_model=LoginResponse | LoginTwoFactorResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
) -> LoginResponse | LoginTwoFactorResponse:
    service = AuthService(
        db,
        request.session,
        request_cookies=request.cookies,
        user_agent=request.headers.get("user-agent"),
    )
    validate_request_origin(request)
    try:
        result = service.login(payload, client_ip=request.client.host if request.client else None)
        apply_trusted_device_cookie(response, service)
        return result
    except AuthServiceError as exc:
        error_response = build_error_response(exc)
        apply_trusted_device_cookie(error_response, service)
        return error_response


@router.post("/2fa/setup", response_model=TwoFactorSetupResponse)
def setup_two_factor(
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
    challenge_id: str | None = None,
) -> TwoFactorSetupResponse:
    validate_request_origin(request)
    try:
        return AuthService(db, request.session).begin_two_factor_setup(challenge_id)
    except AuthServiceError as exc:
        return build_error_response(exc)


@router.post("/2fa/confirm", response_model=TwoFactorConfirmResponse)
def confirm_two_factor(
    payload: TwoFactorConfirmRequest,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
) -> TwoFactorConfirmResponse:
    service = AuthService(
        db,
        request.session,
        request_cookies=request.cookies,
        user_agent=request.headers.get("user-agent"),
    )
    validate_request_origin(request)
    try:
        result = service.confirm_two_factor(
            verification_code=payload.verification_code,
            challenge_id=payload.challenge_id,
            remember_device=payload.remember_device,
            client_ip=request.client.host if request.client else None,
        )
        apply_trusted_device_cookie(response, service)
        return result
    except AuthServiceError as exc:
        error_response = build_error_response(exc)
        apply_trusted_device_cookie(error_response, service)
        return error_response


@router.post("/2fa/verify", response_model=LoginResponse)
def verify_two_factor(
    payload: VerifyTwoFactorRequest,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
) -> LoginResponse:
    service = AuthService(
        db,
        request.session,
        request_cookies=request.cookies,
        user_agent=request.headers.get("user-agent"),
    )
    validate_request_origin(request)
    try:
        result = service.verify_two_factor(
            verification_code=payload.verification_code,
            challenge_id=payload.challenge_id,
            remember_device=payload.remember_device,
            client_ip=request.client.host if request.client else None,
        )
        apply_trusted_device_cookie(response, service)
        return result
    except AuthServiceError as exc:
        error_response = build_error_response(exc)
        apply_trusted_device_cookie(error_response, service)
        return error_response


@router.post("/2fa/recovery-codes/regenerate", response_model=TwoFactorRecoveryCodesResponse)
def regenerate_recovery_codes(
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
) -> TwoFactorRecoveryCodesResponse:
    validate_request_origin(request)
    try:
        return AuthService(db, request.session).regenerate_recovery_codes()
    except AuthServiceError as exc:
        return build_error_response(exc)


@router.post("/logout", response_model=LogoutResponse)
def logout(
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
) -> LogoutResponse:
    validate_request_origin(request)
    del db
    return AuthService(None, request.session).logout()


@router.get("/me", response_model=CurrentUserResponse)
def get_current_user(
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
) -> CurrentUserResponse:
    try:
        return AuthService(db, request.session).get_current_user()
    except AuthServiceError as exc:
        return build_error_response(exc)


@router.patch("/me", response_model=CurrentUserResponse)
def update_current_user(
    payload: CurrentUserUpdateRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
) -> CurrentUserResponse:
    validate_request_origin(request)
    try:
        return AuthService(db, request.session).update_current_user(payload)
    except AuthServiceError as exc:
        return build_error_response(exc)


@router.post("/password-reset/request", response_model=PasswordResetResponse)
def request_password_reset(
    payload: PasswordResetRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
) -> PasswordResetResponse:
    validate_request_origin(request)
    return AuthService(db, {}).request_password_reset(str(payload.email))


@router.post("/password-reset/confirm", response_model=PasswordResetResponse)
def confirm_password_reset(
    payload: PasswordResetConfirmRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
) -> PasswordResetResponse:
    validate_request_origin(request)
    try:
        return AuthService(db, {}).confirm_password_reset(
            token=payload.token,
            password=payload.password,
            password_confirmation=payload.password_confirmation,
        )
    except AuthServiceError as exc:
        return build_error_response(exc)


@router.post("/password/change", response_model=PasswordResetResponse)
def change_password(
    payload: PasswordChangeRequest,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
) -> PasswordResetResponse:
    service = AuthService(
        db,
        request.session,
        request_cookies=request.cookies,
        user_agent=request.headers.get("user-agent"),
    )
    validate_request_origin(request)
    try:
        result = service.change_password(
            current_password=payload.current_password,
            new_password=payload.new_password,
            new_password_confirmation=payload.new_password_confirmation,
        )
        apply_trusted_device_cookie(response, service)
        return result
    except AuthServiceError as exc:
        error_response = build_error_response(exc)
        apply_trusted_device_cookie(error_response, service)
        return error_response
