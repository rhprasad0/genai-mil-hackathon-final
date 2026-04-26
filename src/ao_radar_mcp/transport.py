"""API Gateway HTTP API v2.0 ↔ JSON-RPC adapter.

Sources of truth:
  - docs/application-implementation-plan.md section 6 (transport choice,
    base64 body, integration shape, response envelope).
  - docs/testing-plan.md section 5.4 (boundary tests).

The adapter exposes a small set of helpers that ``handler.lambda_handler``
calls.  It deliberately does not depend on FastMCP or any third-party
adapter; the in-process MCP server in ``server.py`` is invoked directly.
Swapping to a real FastMCP runtime is a one-line change inside
``handle_mcp_request``.
"""

from __future__ import annotations

import base64
import json
from typing import Any

from .server import MCPServer, UnknownToolError

JSONRPC_VERSION: str = "2.0"

# JSON-RPC error codes (subset of https://www.jsonrpc.org/specification#error_object).
ERROR_PARSE: int = -32700
ERROR_INVALID_REQUEST: int = -32600
ERROR_METHOD_NOT_FOUND: int = -32601
ERROR_INVALID_PARAMS: int = -32602
ERROR_INTERNAL: int = -32603
ERROR_TOOL_NOT_FOUND: int = -32001
ERROR_REFUSED: int = -32002


def decode_body(event: dict[str, Any]) -> str:
    """Return the request body as a string, decoding base64 if needed."""

    body = event.get("body") or ""
    if event.get("isBase64Encoded"):
        try:
            return base64.b64decode(body).decode("utf-8")
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"failed to decode base64 body: {exc}") from exc
    return body


def make_response(
    *,
    status_code: int,
    body: dict[str, Any] | str,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Construct an API Gateway HTTP API v2.0 response."""

    if isinstance(body, dict):
        body_text = json.dumps(body, default=str)
    else:
        body_text = body
    out: dict[str, Any] = {
        "statusCode": status_code,
        "headers": {
            "content-type": "application/json",
            **(headers or {}),
        },
        "body": body_text,
        "isBase64Encoded": False,
    }
    return out


def make_jsonrpc_error(
    *,
    request_id: Any,
    code: int,
    message: str,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "error": error}


def make_jsonrpc_result(*, request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "result": result}


def handle_mcp_request(
    server: MCPServer,
    event: dict[str, Any],
) -> dict[str, Any]:
    """Dispatch an API Gateway POST /mcp event through the MCP server.

    Returns an API Gateway v2.0 response.  Never raises; always returns a
    JSON-RPC envelope or a JSON error body.
    """

    request_id: Any = None
    try:
        body_text = decode_body(event)
    except ValueError as exc:
        return make_response(
            status_code=400,
            body=make_jsonrpc_error(
                request_id=None,
                code=ERROR_PARSE,
                message="failed to decode request body",
                data={"detail": str(exc)},
            ),
        )

    if not body_text or not body_text.strip():
        return make_response(
            status_code=400,
            body=make_jsonrpc_error(
                request_id=None,
                code=ERROR_INVALID_REQUEST,
                message="empty request body",
            ),
        )

    try:
        payload = json.loads(body_text)
    except json.JSONDecodeError as exc:
        return make_response(
            status_code=400,
            body=make_jsonrpc_error(
                request_id=None,
                code=ERROR_PARSE,
                message="parse error",
                data={"detail": exc.msg, "lineno": exc.lineno, "colno": exc.colno},
            ),
        )

    if not isinstance(payload, dict):
        return make_response(
            status_code=400,
            body=make_jsonrpc_error(
                request_id=None,
                code=ERROR_INVALID_REQUEST,
                message="JSON-RPC envelope must be an object",
            ),
        )

    request_id = payload.get("id")
    method = payload.get("method")
    params = payload.get("params") or {}
    if not isinstance(method, str):
        return make_response(
            status_code=400,
            body=make_jsonrpc_error(
                request_id=request_id,
                code=ERROR_INVALID_REQUEST,
                message="JSON-RPC envelope is missing a string 'method'",
            ),
        )

    try:
        result = _dispatch(server, method, params)
    except UnknownToolError as exc:
        return make_response(
            status_code=200,
            body=make_jsonrpc_error(
                request_id=request_id,
                code=ERROR_TOOL_NOT_FOUND,
                message=f"unknown tool: {exc.args[0]!r}",
            ),
        )
    except _MethodNotFound as exc:
        return make_response(
            status_code=200,
            body=make_jsonrpc_error(
                request_id=request_id,
                code=ERROR_METHOD_NOT_FOUND,
                message=str(exc),
            ),
        )
    except _InvalidParams as exc:
        return make_response(
            status_code=200,
            body=make_jsonrpc_error(
                request_id=request_id,
                code=ERROR_INVALID_PARAMS,
                message=str(exc),
            ),
        )
    except Exception as exc:  # noqa: BLE001 - intentional broad catch
        return make_response(
            status_code=200,
            body=make_jsonrpc_error(
                request_id=request_id,
                code=ERROR_INTERNAL,
                message="internal error",
                data={"detail": exc.__class__.__name__},
            ),
        )

    return make_response(
        status_code=200,
        body=make_jsonrpc_result(request_id=request_id, result=result),
    )


class _MethodNotFound(LookupError):
    """Raised when the MCP method is not implemented by the server."""


class _InvalidParams(ValueError):
    """Raised when JSON-RPC ``params`` are malformed."""


def _dispatch(server: MCPServer, method: str, params: Any) -> Any:
    if method == "initialize":
        return server.initialize()
    if method == "tools/list":
        return server.list_tools()
    if method == "tools/call":
        if not isinstance(params, dict):
            raise _InvalidParams("tools/call params must be an object")
        name = params.get("name")
        if not isinstance(name, str) or not name:
            raise _InvalidParams("tools/call params.name is required")
        arguments = params.get("arguments") or {}
        if not isinstance(arguments, dict):
            raise _InvalidParams("tools/call params.arguments must be an object")
        return server.call_tool(name, arguments)
    raise _MethodNotFound(f"unknown MCP method: {method!r}")


__all__ = [
    "JSONRPC_VERSION",
    "ERROR_PARSE",
    "ERROR_INVALID_REQUEST",
    "ERROR_METHOD_NOT_FOUND",
    "ERROR_INVALID_PARAMS",
    "ERROR_INTERNAL",
    "ERROR_TOOL_NOT_FOUND",
    "ERROR_REFUSED",
    "decode_body",
    "make_response",
    "make_jsonrpc_error",
    "make_jsonrpc_result",
    "handle_mcp_request",
]
