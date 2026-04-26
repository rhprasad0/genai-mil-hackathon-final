"""Deployed E2E test for ``tools/call`` over the wire.

Source of truth: docs/spec.md section 4.5 and docs/testing-plan.md section 5.6.

This test exercises one representative tool through the deployed ``/mcp``
endpoint and asserts on the JSON-RPC envelope plus the human-authority
boundary clauses that every tool response must surface (including the
Phase 1 ``not_implemented`` stub shape from
``ao_radar_mcp.tools._common.not_implemented_response``).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

import pytest


pytestmark = pytest.mark.e2e

_TIMEOUT_S = 30.0
_REPRESENTATIVE_TOOL = "list_vouchers_awaiting_action"
_REQUIRED_BOUNDARY_NEEDLES = (
    "approving official",
    "official travel system",
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


def test_deployed_tools_call_returns_envelope_with_boundary(mcp_base_url: str) -> None:
    """A representative ``tools/call`` returns a valid envelope and the boundary reminder."""

    payload = {
        "jsonrpc": "2.0",
        "id": "tools-call-e2e-1",
        "method": "tools/call",
        "params": {"name": _REPRESENTATIVE_TOOL, "arguments": {}},
    }
    response = _post_jsonrpc(f"{mcp_base_url}/mcp", payload)

    assert response.get("jsonrpc") == "2.0", response
    assert response.get("id") == "tools-call-e2e-1", response
    assert "error" not in response, response

    result = response["result"]
    content = result.get("content")
    assert isinstance(content, list) and content, result
    assert all(isinstance(item, dict) for item in content), result

    structured = result.get("structuredContent")
    if structured is None:
        # Some tool responses may stream JSON inside ``content`` only.  In that
        # case, locate the JSON content block and use it for the boundary check.
        json_blocks = [item for item in content if item.get("type") == "json"]
        assert json_blocks, f"no JSON content block found: {content!r}"
        structured = json_blocks[0]["json"]

    assert isinstance(structured, dict), result
    serialized = json.dumps(structured).lower()
    for needle in _REQUIRED_BOUNDARY_NEEDLES:
        assert needle in serialized, (
            f"expected boundary clause {needle!r} in tools/call structuredContent, got {structured!r}"
        )
