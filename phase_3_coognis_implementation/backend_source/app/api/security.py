from __future__ import annotations

from urllib.parse import urlparse

from fastapi import HTTPException, Request, status

from app.core.config import settings


def validate_request_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    referer = request.headers.get("referer")

    if origin:
        if not _is_allowed_origin(origin):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Origin not allowed.")
        return

    if referer:
        parsed = urlparse(referer)
        referer_origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else ""
        if referer_origin and not _is_allowed_origin(referer_origin):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Origin not allowed.")


def validate_session_write_request(request: Request) -> None:
    validate_request_origin(request)


def _is_allowed_origin(candidate: str) -> bool:
    normalized = candidate.rstrip("/")
    return normalized in settings.auth_allowed_origins
