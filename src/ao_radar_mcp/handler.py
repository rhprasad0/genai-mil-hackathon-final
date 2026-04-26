"""Lambda entrypoint for the AO Radar MCP application.

Sources of truth:
  - docs/application-implementation-plan.md sections 6 and 12.
  - docs/spec.md sections 4.5 and 4.4.

Routes API Gateway HTTP API v2.0 events:
  - ``GET  /health`` → small JSON with ``{ok, server, version}``; no DB / no
    fraud-mock calls.
  - ``POST /mcp``    → JSON-RPC over Streamable HTTP via ``transport``.
  - anything else    → 404 JSON error.

On any unexpected exception inside a tool the response is a JSON-RPC error
envelope without a stack trace.  Startup fails closed when
``DEMO_DATA_ENVIRONMENT`` is anything other than ``synthetic_demo``.
"""

from __future__ import annotations

import os
from typing import Any

from .config import ALLOWED_DATA_ENVIRONMENT, AppConfig, ConfigurationError, load
from .logging_setup import configure as configure_logging
from .logging_setup import get_logger
from .server import MCPServer, build_server
from .transport import handle_mcp_request, make_response


_server_cache: MCPServer | None = None
_config_cache: AppConfig | None = None
_logger = None  # type: ignore[var-annotated]


def _ensure_logger() -> None:
    global _logger
    if _logger is None:
        configure_logging()
        _logger = get_logger("handler")


def _detect_phase(env: dict[str, str]) -> int:
    """Pick the highest phase whose required vars are populated."""

    if env.get("FRAUD_FUNCTION_NAME") and env.get("DB_SECRET_ARN"):
        return 3
    if env.get("DB_SECRET_ARN"):
        return 2
    return 1


def _ensure_config() -> AppConfig:
    global _config_cache
    if _config_cache is not None:
        return _config_cache
    env = dict(os.environ)
    if env.get("DEMO_DATA_ENVIRONMENT", "").strip() != ALLOWED_DATA_ENVIRONMENT:
        raise ConfigurationError(
            "AO Radar refuses to start unless DEMO_DATA_ENVIRONMENT == synthetic_demo"
        )
    phase = _detect_phase(env)
    _config_cache = load(phase=phase, env=env)
    return _config_cache


def _ensure_server() -> MCPServer:
    global _server_cache
    if _server_cache is not None:
        return _server_cache
    config = _ensure_config()
    _server_cache = build_server(
        server_name=config.mcp_server_name,
        server_version=config.mcp_server_version,
    )
    return _server_cache


def _route_key(event: dict[str, Any]) -> tuple[str, str]:
    method = (
        event.get("requestContext", {})
        .get("http", {})
        .get("method")
        or event.get("httpMethod")
        or ""
    ).upper()
    path = event.get("rawPath") or event.get("path") or ""
    return method, path


def _health_response(config: AppConfig) -> dict[str, Any]:
    return make_response(
        status_code=200,
        body={
            "ok": True,
            "server": config.mcp_server_name,
            "version": config.mcp_server_version,
        },
    )


def _not_found_response(method: str, path: str) -> dict[str, Any]:
    return make_response(
        status_code=404,
        body={
            "error": "not_found",
            "method": method,
            "path": path,
        },
    )


def _method_not_allowed(method: str, path: str) -> dict[str, Any]:
    return make_response(
        status_code=405,
        body={
            "error": "method_not_allowed",
            "method": method,
            "path": path,
        },
    )


def reset_caches_for_tests() -> None:
    """Clear cold-start caches.  Tests should call this between cases."""

    global _server_cache, _config_cache, _logger
    _server_cache = None
    _config_cache = None
    _logger = None


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda entrypoint for ``ao-radar-mcp``."""

    _ensure_logger()
    try:
        config = _ensure_config()
    except ConfigurationError as exc:
        return make_response(
            status_code=500,
            body={"error": "configuration_error", "detail": str(exc)},
        )
    except Exception as exc:  # noqa: BLE001
        return make_response(
            status_code=500,
            body={"error": "startup_failure", "detail": exc.__class__.__name__},
        )

    method, path = _route_key(event)
    if method == "GET" and path == "/health":
        return _health_response(config)
    if method == "POST" and path == "/mcp":
        try:
            server = _ensure_server()
        except Exception as exc:  # noqa: BLE001
            return make_response(
                status_code=500,
                body={
                    "error": "server_bootstrap_failure",
                    "detail": exc.__class__.__name__,
                },
            )
        return handle_mcp_request(server, event)
    if path in {"/health", "/mcp"}:
        return _method_not_allowed(method, path)
    return _not_found_response(method, path)


__all__ = ["lambda_handler", "reset_caches_for_tests"]
