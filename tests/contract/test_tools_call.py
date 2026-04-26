"""Contract tests for ``tools/call`` dispatch coverage.

Source of truth: docs/testing-plan.md section 5.3.
"""

from __future__ import annotations

import pytest

from ao_radar_mcp.server import TOOL_NAMES_IN_SPEC_ORDER, build_server


@pytest.fixture
def server():
    return build_server(server_name="ao-radar-mcp", server_version="0.1.0")


def test_every_advertised_tool_dispatches_without_error(server) -> None:
    """Phase 1 dispatch returns a not_implemented stub for every spec tool.

    The catalog must remain dispatchable so cockpits can list and call every
    tool without surprises.
    """

    for name in TOOL_NAMES_IN_SPEC_ORDER:
        result = server.call_tool(name, {})
        assert isinstance(result, dict)
        assert "content" in result


def test_unknown_tool_raises() -> None:
    server = build_server(server_name="ao-radar-mcp", server_version="0.1.0")
    with pytest.raises(LookupError):
        server.call_tool("query_database", {"sql": "SELECT 1"})


def test_set_voucher_review_status_refuses_blocked_value(server) -> None:
    result = server.call_tool(
        "set_voucher_review_status",
        {"voucher_id": "V-TEST-1003", "status": "approved"},
    )
    payload = result["structuredContent"]
    assert payload["refused"] is True
    assert payload["reason"] == "prohibited_action"


def test_mark_finding_reviewed_refuses_blocked_value(server) -> None:
    result = server.call_tool(
        "mark_finding_reviewed",
        {"finding_id": "FIND-TEST-1", "status": "fraud"},
    )
    payload = result["structuredContent"]
    assert payload["refused"] is True
    assert payload["reason"] == "prohibited_action"
