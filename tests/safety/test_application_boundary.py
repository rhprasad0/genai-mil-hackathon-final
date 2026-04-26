"""Application-level boundary regression tests.

Source of truth: docs/testing-plan.md section 6 (G2 / G4) and
docs/application-implementation-plan.md sections 10-11.
"""

from __future__ import annotations

from ao_radar_mcp.safety.controlled_status import BLOCKED_STATUS_VALUES
from ao_radar_mcp.server import build_server
from ao_radar_mcp.tools import (
    mark_finding_reviewed,
    set_voucher_review_status,
)


def test_set_voucher_review_status_refuses_every_blocked_value() -> None:
    for blocked in sorted(BLOCKED_STATUS_VALUES):
        result = set_voucher_review_status.handler(
            {"voucher_id": "V-TEST-1003", "status": blocked}
        )
        assert result["refused"] is True, blocked
        assert result["reason"] == "prohibited_action"


def test_mark_finding_reviewed_refuses_every_blocked_value() -> None:
    for blocked in sorted(BLOCKED_STATUS_VALUES):
        result = mark_finding_reviewed.handler(
            {"finding_id": "FIND-TEST-1", "status": blocked}
        )
        assert result["refused"] is True, blocked
        assert result["reason"] == "prohibited_action"


def test_no_tool_name_matches_generic_data_access_pattern() -> None:
    server = build_server(server_name="ao-radar-mcp", server_version="0.1.0")
    needles = (
        "query_database",
        "execute_sql",
        "run_query",
        "read_file",
        "list_dir",
        "download_file",
        "fetch_url",
        "http_get",
        "eval",
        "shell",
        "admin_",
    )
    for name in server.tools:
        lowered = name.lower()
        for needle in needles:
            assert needle not in lowered, f"{name} contains forbidden pattern {needle}"


def test_refusal_payload_carries_canonical_boundary_reminder() -> None:
    result = set_voucher_review_status.handler(
        {"voucher_id": "V-TEST-1003", "status": "approved"}
    )
    assert result["boundary_reminder"].startswith(
        "AO Radar is a synthetic pre-decision review aid"
    )
    assert "external parties" in result["boundary_reminder"]
