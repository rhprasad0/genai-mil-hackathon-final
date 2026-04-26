"""Unit tests for ``ao_radar_mcp.transport``.

Source of truth: docs/application-implementation-plan.md section 6,
docs/testing-plan.md section 5.4.
"""

from __future__ import annotations

import base64
import json

from ao_radar_mcp.server import build_server
from ao_radar_mcp.transport import (
    ERROR_INVALID_REQUEST,
    ERROR_METHOD_NOT_FOUND,
    ERROR_PARSE,
    ERROR_TOOL_NOT_FOUND,
    decode_body,
    handle_mcp_request,
    make_response,
)


def _server():
    return build_server(server_name="ao-radar-mcp", server_version="0.1.0")


def _event(body: str, *, base64_encoded: bool = False) -> dict:
    return {
        "version": "2.0",
        "rawPath": "/mcp",
        "headers": {"content-type": "application/json"},
        "requestContext": {"http": {"method": "POST", "path": "/mcp"}},
        "body": body,
        "isBase64Encoded": base64_encoded,
    }


def test_decode_body_passthrough() -> None:
    assert decode_body({"body": "hello", "isBase64Encoded": False}) == "hello"


def test_decode_body_base64() -> None:
    raw = "{\"jsonrpc\":\"2.0\"}"
    encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
    assert decode_body({"body": encoded, "isBase64Encoded": True}) == raw


def test_make_response_shape() -> None:
    resp = make_response(status_code=200, body={"ok": True})
    assert resp["statusCode"] == 200
    assert resp["isBase64Encoded"] is False
    assert resp["headers"]["content-type"] == "application/json"
    assert json.loads(resp["body"]) == {"ok": True}


def test_handle_mcp_request_initialize() -> None:
    server = _server()
    event = _event(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"}))
    resp = handle_mcp_request(server, event)
    body = json.loads(resp["body"])
    assert body["id"] == 1
    assert body["result"]["serverInfo"]["name"] == "ao-radar-mcp"


def test_handle_mcp_request_tools_list() -> None:
    server = _server()
    event = _event(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}))
    resp = handle_mcp_request(server, event)
    body = json.loads(resp["body"])
    assert body["id"] == 2
    assert len(body["result"]["tools"]) == 17


def test_handle_mcp_request_tools_call_dispatches_each_tool() -> None:
    server = _server()
    for name in server.tools:
        event = _event(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": name,
                    "method": "tools/call",
                    "params": {"name": name, "arguments": {}},
                }
            )
        )
        resp = handle_mcp_request(server, event)
        body = json.loads(resp["body"])
        assert "error" not in body, f"unexpected error for {name}: {body}"
        assert "result" in body


def test_handle_mcp_request_unknown_tool() -> None:
    server = _server()
    event = _event(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 9,
                "method": "tools/call",
                "params": {"name": "query_database", "arguments": {}},
            }
        )
    )
    resp = handle_mcp_request(server, event)
    body = json.loads(resp["body"])
    assert body["error"]["code"] == ERROR_TOOL_NOT_FOUND
    assert "query_database" in body["error"]["message"]


def test_handle_mcp_request_malformed_json_returns_parse_error() -> None:
    server = _server()
    event = _event("{not json")
    resp = handle_mcp_request(server, event)
    body = json.loads(resp["body"])
    assert body["error"]["code"] == ERROR_PARSE


def test_handle_mcp_request_empty_body_returns_invalid_request() -> None:
    server = _server()
    event = _event("")
    resp = handle_mcp_request(server, event)
    body = json.loads(resp["body"])
    assert body["error"]["code"] == ERROR_INVALID_REQUEST


def test_handle_mcp_request_unknown_method() -> None:
    server = _server()
    event = _event(json.dumps({"jsonrpc": "2.0", "id": 7, "method": "destroy"}))
    resp = handle_mcp_request(server, event)
    body = json.loads(resp["body"])
    assert body["error"]["code"] == ERROR_METHOD_NOT_FOUND
