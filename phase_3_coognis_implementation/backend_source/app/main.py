from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger, log_event
from app.services.local_llm import validate_local_llm_runtime

logger = get_logger(__name__)


def create_application() -> FastAPI:
    configure_logging()
    _validate_auth_runtime()
    app = FastAPI(
        title=f"{settings.app_public_name} API",
        debug=settings.debug,
        version="0.1.0",
    )

    cors_allowed_origins = sorted(settings.auth_allowed_origins)
    if cors_allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    local_llm_runtime = validate_local_llm_runtime()
    log_event(
        logger,
        "local_llm_runtime",
        backend=local_llm_runtime.get("backend"),
        provider=local_llm_runtime.get("provider"),
        model=local_llm_runtime.get("model"),
        status=local_llm_runtime.get("status"),
        mode=local_llm_runtime.get("mode"),
        model_path=local_llm_runtime.get("model_path"),
    )

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.auth_session_secret,
        session_cookie=settings.auth_session_cookie_name,
        same_site=settings.auth_session_same_site,
        https_only=settings.auth_session_https_only,
        max_age=settings.auth_session_max_age_seconds,
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        request_id = str(uuid4())
        started_at = perf_counter()
        module_name = _resolve_module_name(request.url.path)

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = round((perf_counter() - started_at) * 1000, 2)
            log_event(
                logger,
                "module_request",
                request_id=request_id,
                module=module_name,
                method=request.method,
                path=request.url.path,
                status_code=500,
                duration_ms=duration_ms,
                error=exc.__class__.__name__,
            )
            raise

        duration_ms = round((perf_counter() - started_at) * 1000, 2)
        response.headers["X-Request-Id"] = request_id
        log_event(
            logger,
            "module_request",
            request_id=request_id,
            module=module_name,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


def _validate_auth_runtime() -> None:
    if settings.auth_session_same_site not in {"lax", "strict", "none"}:
        raise RuntimeError("AUTH_SESSION_SAME_SITE must be one of: lax, strict, none.")

    if settings.is_production and settings.auth_enforce_secure_defaults:
        if settings.auth_session_secret == "change-me-in-production":
            raise RuntimeError("AUTH_SESSION_SECRET must be changed in production.")
        if not settings.auth_session_https_only:
            raise RuntimeError("AUTH_SESSION_HTTPS_ONLY must be enabled in production.")


def _resolve_module_name(path: str) -> str:
    segments = [segment for segment in path.strip("/").split("/") if segment]
    if len(segments) >= 2 and segments[0] == settings.api_v1_prefix.strip("/"):
        return segments[1].upper()
    if segments:
        return segments[0].upper()
    return "SYSTEM"


app = create_application()
