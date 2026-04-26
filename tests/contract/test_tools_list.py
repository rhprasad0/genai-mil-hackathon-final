"""Contract tests for ``tools/list``.

Source of truth: docs/spec.md section 4.5 and docs/testing-plan.md section 5.3.
"""

from __future__ import annotations

import pytest

from ao_radar_mcp.server import TOOL_NAMES_IN_SPEC_ORDER, build_server


SPEC_CATALOG = (
    "list_vouchers_awaiting_action",
    "get_voucher_packet",
    "get_traveler_profile",
    "list_prior_voucher_summaries",
    "get_external_anomaly_signals",
    "analyze_voucher_story",
    "get_policy_citation",
    "get_policy_citations",
    "prepare_ao_review_brief",
    "export_review_brief",
    "record_ao_note",
    "mark_finding_reviewed",
    "record_ao_feedback",
    "draft_return_comment",
    "request_traveler_clarification",
    "set_voucher_review_status",
    "get_audit_trail",
)


_GENERIC_DATA_ACCESS_NEEDLES = (
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


@pytest.fixture
def server_listing():
    server = build_server(server_name="ao-radar-mcp", server_version="0.1.0")
    return server.list_tools()["tools"]


def test_tools_list_matches_spec_catalog_exactly(server_listing) -> None:
    names = tuple(tool["name"] for tool in server_listing)
    assert names == SPEC_CATALOG


def test_tools_list_matches_canonical_order_constant() -> None:
    assert TOOL_NAMES_IN_SPEC_ORDER == SPEC_CATALOG


def test_tools_list_excludes_generic_data_access_names(server_listing) -> None:
    for tool in server_listing:
        lowered = tool["name"].lower()
        for needle in _GENERIC_DATA_ACCESS_NEEDLES:
            assert needle not in lowered, f"forbidden needle {needle} in {tool['name']}"


def test_each_tool_has_input_schema_and_description(server_listing) -> None:
    for tool in server_listing:
        assert isinstance(tool["description"], str) and tool["description"]
        assert isinstance(tool["inputSchema"], dict)
        assert tool["inputSchema"].get("type") == "object"


def test_each_description_mentions_the_authority_boundary(server_listing) -> None:
    for tool in server_listing:
        description = tool["description"].lower()
        # The shared phrase from tools/_common.py mentions the human Approving
        # Official remaining accountable.  This is the boundary clue every
        # cockpit needs to surface.
        assert "approving official" in description, tool["name"]
