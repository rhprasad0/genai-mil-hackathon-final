"""Deployed E2E test for ``initialize`` over the wire.

Source of truth: docs/testing-plan.md section 5.6 (G1) and
docs/application-implementation-plan.md section 6 (FastMCP wiring).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

import pytest


pytestmark = pytest.mark.e2e

_TIMEOUT_S = 15.0
_REQUIRED_BOUNDARY_NEEDLES = (
    "synthetic pre-decision review aid",
    "human approving official",
)


def _post_jsonrpc(url: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_S) as response:
            assert response.status == 200, f"expected 200, got {response.status}"
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:  # pragma: no cover - exercised only on outage
        pytest.fail(f"deployed MCP endpoint unreachable: {exc!r}")


def test_deployed_initialize_returns_server_identity(mcp_base_url: str) -> None:
    """``initialize`` returns serverInfo, protocolVersion, capabilities, and the boundary reminder."""

    payload = {
        "jsonrpc": "2.0",
        "id": "init-e2e-1",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "ao-radar-e2e", "version": "0.1.0"},
        },
    }
    response = _post_jsonrpc(f"{mcp_base_url}/mcp", payload)

    assert response.get("jsonrpc") == "2.0", response
    assert response.get("id") == "init-e2e-1", response
    assert "error" not in response, response
    result = response["result"]

    server_info = result["serverInfo"]
    assert isinstance(server_info["name"], str) and "ao-radar" in server_info["name"].lower(), result
    assert isinstance(server_info["version"], str) and server_info["version"], result

    assert result["protocolVersion"] == "2024-11-05", result
    assert result["capabilities"]["tools"]["listChanged"] is False, result

    reminder = result["boundary_reminder"].lower()
    for needle in _REQUIRED_BOUNDARY_NEEDLES:
        assert needle in reminder, (
            f"expected canonical boundary clause {needle!r} in reminder, got {result['boundary_reminder']!r}"
        )
