"""Tiny shared helpers for deployed JSON-RPC E2E tests.

Kept stdlib-only so the e2e tier does not need extra dependencies in CI.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

import pytest

_TIMEOUT_S = 30.0


def post_jsonrpc(base_url: str, payload: dict[str, Any], *, timeout_s: float = _TIMEOUT_S) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}/mcp",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            assert response.status == 200, f"expected 200, got {response.status}"
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:  # pragma: no cover - exercised only on outage
        pytest.fail(f"deployed MCP endpoint unreachable: {exc!r}")


def call_tool(
    base_url: str,
    tool_name: str,
    arguments: dict[str, Any],
    *,
    request_id: str | None = None,
    timeout_s: float = _TIMEOUT_S,
) -> dict[str, Any]:
    payload = {
        "jsonrpc": "2.0",
        "id": request_id or f"e2e-{tool_name}",
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }
    response = post_jsonrpc(base_url, payload, timeout_s=timeout_s)
    assert "error" not in response, response
    result = response["result"]
    structured = result.get("structuredContent")
    if structured is None:
        for block in result.get("content", []):
            if isinstance(block, dict) and block.get("type") == "json":
                return block["json"]
        pytest.fail(f"tools/call response missing structuredContent: {result!r}")
    assert isinstance(structured, dict), result
    return structured


__all__ = ["call_tool", "post_jsonrpc"]
