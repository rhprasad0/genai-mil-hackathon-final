"""Contract tests for unknown-tool dispatch.

Source of truth: docs/testing-plan.md section 6 G2.
"""

from __future__ import annotations

import json

from ao_radar_mcp.server import UnknownToolError, build_server
from ao_radar_mcp.transport import handle_mcp_request


def _server():
    return build_server(server_name="ao-radar-mcp", server_version="0.1.0")


def test_unknown_tool_via_call_raises_in_process() -> None:
    server = _server()
    try:
        server.call_tool("execute_sql", {"sql": "DROP TABLE everything"})
    except UnknownToolError as exc:
        assert "execute_sql" in str(exc)
    else:  # pragma: no cover - guard
        raise AssertionError("expected UnknownToolError")


def test_unknown_tool_via_transport_returns_jsonrpc_error() -> None:
    server = _server()
    body = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "fetch_url", "arguments": {"url": "http://example.com"}},
        }
    )
    event = {
        "version": "2.0",
        "rawPath": "/mcp",
        "headers": {"content-type": "application/json"},
        "requestContext": {"http": {"method": "POST", "path": "/mcp"}},
        "body": body,
        "isBase64Encoded": False,
    }
    response = handle_mcp_request(server, event)
    payload = json.loads(response["body"])
    assert payload["error"]["code"] == -32001
    assert "fetch_url" in payload["error"]["message"]
