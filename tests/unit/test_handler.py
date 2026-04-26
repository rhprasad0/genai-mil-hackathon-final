"""Unit tests for ``ao_radar_mcp.handler``.

Source of truth: docs/application-implementation-plan.md section 6.
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


def _api_event(method: str, path: str, body: dict | None = None) -> dict:
    payload = json.dumps(body or {}) if body is not None else ""
    return {
        "version": "2.0",
        "routeKey": f"{method} {path}",
        "rawPath": path,
        "headers": {"content-type": "application/json"},
        "requestContext": {"http": {"method": method, "path": path}},
        "body": payload,
        "isBase64Encoded": False,
    }


def test_health_returns_200() -> None:
    response = handler.lambda_handler(_api_event("GET", "/health"), context=None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["ok"] is True
    assert body["server"] == "ao-radar-mcp"
    assert body["version"] == "0.1.0"


def test_unknown_route_returns_404() -> None:
    response = handler.lambda_handler(_api_event("GET", "/db"), context=None)
    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert body["error"] == "not_found"


def test_post_to_health_returns_405() -> None:
    response = handler.lambda_handler(_api_event("POST", "/health"), context=None)
    assert response["statusCode"] == 405


def test_initialize_returns_server_identity() -> None:
    event = _api_event(
        "POST",
        "/mcp",
        body={"jsonrpc": "2.0", "id": 1, "method": "initialize"},
    )
    response = handler.lambda_handler(event, context=None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["jsonrpc"] == "2.0"
    assert body["id"] == 1
    info = body["result"]["serverInfo"]
    assert info["name"] == "ao-radar-mcp"
    assert info["version"] == "0.1.0"


def test_tools_list_returns_full_catalog() -> None:
    event = _api_event(
        "POST",
        "/mcp",
        body={"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    )
    response = handler.lambda_handler(event, context=None)
    body = json.loads(response["body"])
    tool_names = [tool["name"] for tool in body["result"]["tools"]]
    assert tool_names[0] == "list_vouchers_awaiting_action"
    assert "prepare_ao_review_brief" in tool_names
    assert "set_voucher_review_status" in tool_names
    assert "get_audit_trail" in tool_names
    assert len(tool_names) == 17


def test_base64_body_decodes() -> None:
    body = {"jsonrpc": "2.0", "id": 3, "method": "initialize"}
    encoded = base64.b64encode(json.dumps(body).encode("utf-8")).decode("ascii")
    event = _api_event("POST", "/mcp")
    event["body"] = encoded
    event["isBase64Encoded"] = True
    response = handler.lambda_handler(event, context=None)
    body_out = json.loads(response["body"])
    assert body_out["id"] == 3
    assert "result" in body_out


def test_malformed_json_returns_jsonrpc_parse_error() -> None:
    event = _api_event("POST", "/mcp")
    event["body"] = "{not json"
    response = handler.lambda_handler(event, context=None)
    body = json.loads(response["body"])
    assert body["error"]["code"] == -32700


def test_unknown_method_returns_method_not_found() -> None:
    event = _api_event(
        "POST",
        "/mcp",
        body={"jsonrpc": "2.0", "id": 4, "method": "tools/destroy"},
    )
    response = handler.lambda_handler(event, context=None)
    body = json.loads(response["body"])
    assert body["error"]["code"] == -32601


def test_unknown_tool_returns_tool_not_found() -> None:
    event = _api_event(
        "POST",
        "/mcp",
        body={
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {"name": "execute_sql", "arguments": {"sql": "SELECT 1"}},
        },
    )
    response = handler.lambda_handler(event, context=None)
    body = json.loads(response["body"])
    assert body["error"]["code"] == -32001
    assert "execute_sql" in body["error"]["message"]


def test_startup_refuses_non_synthetic_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_DATA_ENVIRONMENT", "prod")
    handler.reset_caches_for_tests()
    response = handler.lambda_handler(_api_event("GET", "/health"), context=None)
    assert response["statusCode"] == 500
    body = json.loads(response["body"])
    assert body["error"] == "configuration_error"
