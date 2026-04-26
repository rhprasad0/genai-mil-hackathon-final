"""Lambda boundary tests for ``ao_radar_mcp.handler``.

Source of truth: docs/testing-plan.md section 5.4.

Every test in this file constructs a realistic API Gateway HTTP API v2.0
event dict and calls ``lambda_handler`` directly.  No mocks of the handler
itself — these tests are the ones that catch deployment-shape regressions.
"""

from __future__ import annotations

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


def _api_gw_v2_event(
    method: str, path: str, *, body: str = "", base64_encoded: bool = False
) -> dict:
    return {
        "version": "2.0",
        "routeKey": f"{method} {path}",
        "rawPath": path,
        "headers": {"content-type": "application/json"},
        "requestContext": {
            "http": {"method": method, "path": path},
            "stage": "$default",
        },
        "body": body,
        "isBase64Encoded": base64_encoded,
    }


def test_health_route_returns_apigw_v2_response_shape() -> None:
    response = handler.lambda_handler(
        _api_gw_v2_event("GET", "/health"), context=None
    )
    assert response["statusCode"] == 200
    assert response["isBase64Encoded"] is False
    assert response["headers"]["content-type"].startswith("application/json")
    body = json.loads(response["body"])
    assert body["server"] == "ao-radar-mcp"


def test_post_mcp_initialize_returns_server_identity() -> None:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    response = handler.lambda_handler(
        _api_gw_v2_event("POST", "/mcp", body=body), context=None
    )
    payload = json.loads(response["body"])
    assert payload["result"]["serverInfo"]["name"] == "ao-radar-mcp"


def test_post_mcp_tools_list_returns_full_catalog() -> None:
    body = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    response = handler.lambda_handler(
        _api_gw_v2_event("POST", "/mcp", body=body), context=None
    )
    payload = json.loads(response["body"])
    names = [tool["name"] for tool in payload["result"]["tools"]]
    assert names[0] == "list_vouchers_awaiting_action"
    assert "prepare_ao_review_brief" in names
    assert len(names) == 17


def test_unknown_route_returns_404_json() -> None:
    response = handler.lambda_handler(
        _api_gw_v2_event("GET", "/db"), context=None
    )
    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert body["error"] == "not_found"


def test_post_to_health_returns_405() -> None:
    response = handler.lambda_handler(
        _api_gw_v2_event("POST", "/health"), context=None
    )
    assert response["statusCode"] == 405
