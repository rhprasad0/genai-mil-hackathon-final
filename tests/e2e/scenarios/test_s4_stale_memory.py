"""E2E scenario S4: stale-memory old transaction (V-1006).

Source of truth: docs/testing-plan.md section 8 S4.

The seeded V-1006 brief carries a ``stale_memory_old_transaction`` finding
that the deployed ``prepare_ao_review_brief`` must surface.
"""

from __future__ import annotations

import pytest

from .._jsonrpc import call_tool

pytestmark = pytest.mark.e2e

_VOUCHER_ID = "V-1006"


def test_e2e_stale_memory_old_transaction(mcp_base_url: str) -> None:
    brief_response = call_tool(
        mcp_base_url,
        "prepare_ao_review_brief",
        {"voucher_id": _VOUCHER_ID, "actor_label": "ao-radar-e2e"},
    )
    assert brief_response["status"] == "ok", brief_response
    assert brief_response["voucher"]["voucher_id"] == _VOUCHER_ID
    finding_categories = {f["category"] for f in brief_response["findings"]}
    assert "stale_memory_old_transaction" in finding_categories, finding_categories
    assert "approving official" in brief_response["boundary_reminder"].lower()
