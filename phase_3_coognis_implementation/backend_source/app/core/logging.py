import json
import logging
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any


def configure_logging() -> None:
    root_logger = logging.getLogger()
    app_logger = logging.getLogger("app")

    if getattr(app_logger, "_json_logging_configured", False):
        return

    if not root_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        root_logger.addHandler(handler)
    else:
        for handler in root_logger.handlers:
            handler.setFormatter(logging.Formatter("%(message)s"))

    root_logger.setLevel(logging.INFO)
    app_logger.setLevel(logging.INFO)
    app_logger.propagate = True
    app_logger._json_logging_configured = True  # type: ignore[attr-defined]


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(f"app.{name}")


def log_event(logger: logging.Logger, event: str, **fields: Any) -> None:
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **_normalize(fields),
    }
    logger.info(json.dumps(payload, default=str, sort_keys=True))


def _normalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _normalize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    if hasattr(value, "model_dump"):
        return _normalize(value.model_dump())
    return value
