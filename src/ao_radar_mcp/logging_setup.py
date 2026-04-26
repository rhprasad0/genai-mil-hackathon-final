"""Structured logging helper for the MCP Lambda.

Sources of truth:
  - docs/application-implementation-plan.md sections 5 and 6 (no body
    logging at INFO; never log secret values).

The helper is intentionally minimal: a JSON formatter that emits one log
line per record without echoing request bodies, fraud-mock payloads, or
Secrets Manager values.  Tools should call ``get_logger`` rather than
``logging.getLogger`` so we can centralize the format later if needed.
"""

from __future__ import annotations

import json
import logging
import os
from logging import Logger, LogRecord
from typing import Final

_DEFAULT_LEVEL: Final[str] = "INFO"
_LOGGER_NAME: Final[str] = "ao_radar_mcp"
_DENYLIST_KEYS: Final[frozenset[str]] = frozenset(
    {"password", "secret", "token", "authorization", "api_key", "apikey"}
)


class JsonFormatter(logging.Formatter):
    """Compact JSON formatter that strips obvious credential-shaped keys."""

    def format(self, record: LogRecord) -> str:
        payload: dict[str, object] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Carry structured ``extra`` keys when present, but never log
        # anything that looks like a secret.
        for key, value in record.__dict__.items():
            if key in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
            }:
                continue
            if key.lower() in _DENYLIST_KEYS:
                payload[key] = "[redacted]"
                continue
            payload[key] = value
        return json.dumps(payload, default=str, sort_keys=True)


_configured = False


def configure(level: str | None = None) -> None:
    """Configure the package logger once per process.

    Subsequent calls re-set the level only.  The handler is replaced if the
    formatter has not been installed yet.
    """

    global _configured

    chosen_level = (level or os.environ.get("LOG_LEVEL") or _DEFAULT_LEVEL).upper()
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(chosen_level)
    logger.propagate = False

    if not _configured:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.handlers = [handler]
        _configured = True
    else:
        for handler in logger.handlers:
            handler.setLevel(chosen_level)


def get_logger(suffix: str | None = None) -> Logger:
    """Return the package logger (or a child logger if ``suffix`` is set)."""

    if not _configured:
        configure()
    if suffix:
        return logging.getLogger(f"{_LOGGER_NAME}.{suffix}")
    return logging.getLogger(_LOGGER_NAME)


__all__ = ["configure", "get_logger", "JsonFormatter"]
