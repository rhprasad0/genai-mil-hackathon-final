"""Lambda boundary tests for payload shape variants.

Source of truth: docs/testing-plan.md section 5.4 (base64 body, malformed
JSON, unknown route, internal exception → JSON-RPC error).
"""

from __future__ import annotations

import base64
import json

import pytest

from ao_radar_mcp import handler


_BASE_ENV = {
    "LOG_LEVEL": "INFO",
    "MCP_SERVER_NAME": "ao-radar-mcp",
    "MCP_SERVER_VERSION": "0.1.0",
    "DEMO_DATA_ENVIRONMENT": "synthetic_demo",
}


@pytest.fixture(autouse=True)
def _set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    handler.reset_caches_for_tests()
    for key, value in _BASE_ENV.items():
        monkeypatch.setenv(key, value)
    yield
    handler.reset_caches_for_tests()


def _api_event(method: str, path: str, *, body: str, base64_encoded: bool = False) -> dict:
    return {
        "version": "2.0",
        "rawPath": path,
        "headers": {"content-type": "application/json"},
        "requestContext": {"http": {"method": method, "path": path}},
        "body": body,
        "isBase64Encoded": base64_encoded,
    }


def test_decodes_base64_encoded_body() -> None:
    request = json.dumps({"jsonrpc": "2.0", "id": 7, "method": "tools/list"})
    encoded = base64.b64encode(request.encode("utf-8")).decode("ascii")
    response = handler.lambda_handler(
        _api_event("POST", "/mcp", body=encoded, base64_encoded=True), context=None
    )
    payload = json.loads(response["body"])
    assert "result" in payload


def test_malformed_json_returns_jsonrpc_parse_error() -> None:
    response = handler.lambda_handler(
        _api_event("POST", "/mcp", body="not json"), context=None
    )
    payload = json.loads(response["body"])
    assert payload["error"]["code"] == -32700
    assert "stack" not in payload  # No stack trace leaked


def test_invalid_envelope_returns_invalid_request() -> None:
    response = handler.lambda_handler(
        _api_event("POST", "/mcp", body="[1, 2, 3]"), context=None
    )
    payload = json.loads(response["body"])
    assert payload["error"]["code"] == -32600


def test_internal_exception_returns_clean_jsonrpc_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Force a tool handler to raise and confirm the response is sanitized."""

    def _boom(payload):  # type: ignore[no-untyped-def]
        raise RuntimeError("simulated tool failure")

    handler.reset_caches_for_tests()

    # Build the server, then monkeypatch one tool's handler to raise.
    from ao_radar_mcp.handler import _ensure_server  # noqa: WPS437 - test reaches in

    server = _ensure_server()
    server.tools["list_vouchers_awaiting_action"] = (
        server.tools["list_vouchers_awaiting_action"]
    )
    server.tools["list_vouchers_awaiting_action"].handler = _boom  # type: ignore[assignment]

    body = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 11,
            "method": "tools/call",
            "params": {
                "name": "list_vouchers_awaiting_action",
                "arguments": {},
            },
        }
    )
    response = handler.lambda_handler(
        _api_event("POST", "/mcp", body=body), context=None
    )
    payload = json.loads(response["body"])
    assert payload["error"]["code"] == -32603
    # No traceback in the body.
    assert "Traceback" not in response["body"]
    assert "simulated tool failure" not in response["body"]
