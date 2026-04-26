"""Deployed E2E test for ``tools/list`` over the wire.

Source of truth: docs/spec.md section 4.5, docs/testing-plan.md section 5.6 (G1, G2).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

import pytest


pytestmark = pytest.mark.e2e

_TIMEOUT_S = 15.0

_SPEC_CATALOG = (
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


def test_deployed_tools_list_returns_full_catalog(mcp_base_url: str) -> None:
    """``tools/list`` returns the spec catalog in canonical order with safe descriptions."""

    payload = {
        "jsonrpc": "2.0",
        "id": "tools-list-e2e-1",
        "method": "tools/list",
        "params": {},
    }
    response = _post_jsonrpc(f"{mcp_base_url}/mcp", payload)

    assert response.get("jsonrpc") == "2.0", response
    assert response.get("id") == "tools-list-e2e-1", response
    assert "error" not in response, response

    tools = response["result"]["tools"]
    names = tuple(tool["name"] for tool in tools)
    assert names == _SPEC_CATALOG, (
        f"deployed tools/list does not match spec catalog.\n"
        f"  expected: {_SPEC_CATALOG}\n"
        f"  got:      {names}"
    )

    for tool in tools:
        lowered = tool["name"].lower()
        for needle in _GENERIC_DATA_ACCESS_NEEDLES:
            assert needle not in lowered, (
                f"forbidden generic-data-access needle {needle!r} in deployed tool {tool['name']!r}"
            )
        assert isinstance(tool["description"], str) and tool["description"], tool
        assert "approving official" in tool["description"].lower(), (
            f"description for {tool['name']!r} omits human authority boundary clue"
        )
        schema = tool["inputSchema"]
        assert isinstance(schema, dict) and schema.get("type") == "object", tool
