"""E2E scenario S1: missing receipt + weak local-paper evidence (V-1002).

Source of truth: docs/testing-plan.md section 8 S1.

The deployed flow walked here:

1. ``prepare_ao_review_brief`` over V-1002 — assert the synthetic packet's
   evidence-gap findings (missing receipt + weak local-paper receipt +
   evidence quality concern) and the missing-information items are
   surfaced.
2. ``set_voucher_review_status`` to a synthetic-allowed status — assert
   the response confirms the new status and emits a paired
   ``scoped_write`` audit event.
3. ``get_audit_trail`` — assert the new ``scoped_write`` event is present
   alongside the seeded events.
"""

from __future__ import annotations

import pytest

from .._jsonrpc import call_tool

pytestmark = pytest.mark.e2e

_VOUCHER_ID = "V-1002"
_REQUIRED_CATEGORIES = {
    "missing_receipt",
    "weak_or_local_paper_receipt",
    "evidence_quality_concern",
}


def test_e2e_missing_receipt_local_paper(mcp_base_url: str) -> None:
    brief_response = call_tool(
        mcp_base_url,
        "prepare_ao_review_brief",
        {"voucher_id": _VOUCHER_ID, "actor_label": "ao-radar-e2e"},
    )
    assert brief_response["status"] == "ok", brief_response
    assert brief_response["audit_event_type"] in {"retrieval", "generation"}
    assert brief_response["voucher"]["voucher_id"] == _VOUCHER_ID

    finding_categories = {finding["category"] for finding in brief_response["findings"]}
    missing_for = _REQUIRED_CATEGORIES - finding_categories
    assert not missing_for, f"missing required categories: {missing_for}; got {finding_categories}"

    missing = brief_response["missing_information_items"]
    assert len(missing) >= 2, f"expected ≥ 2 missing-info items, got {missing}"
    for item in missing:
        assert "linked_line_item_id" in item, item
        assert item["description"], item

    set_response = call_tool(
        mcp_base_url,
        "set_voucher_review_status",
        {
            "voucher_id": _VOUCHER_ID,
            "status": "in_review",
            "actor_label": "ao-radar-e2e",
        },
    )
    assert set_response["status"] == "ok", set_response
    assert set_response["review_status"] == "in_review", set_response
    assert set_response["audit_event_type"] == "scoped_write"
    new_event_id = set_response["audit_event_id"]
    assert new_event_id, set_response

    audit = call_tool(
        mcp_base_url,
        "get_audit_trail",
        {"voucher_id": _VOUCHER_ID},
    )
    assert audit["status"] == "ok", audit
    event_ids = [event["event_id"] for event in audit["events"]]
    assert new_event_id in event_ids, audit

    matched = next(
        event for event in audit["events"] if event["event_id"] == new_event_id
    )
    assert matched["event_type"] == "scoped_write"
    assert matched["tool_name"] == "set_voucher_review_status"
    assert matched["resulting_status"] == "in_review"
    assert "approving official" in matched["human_authority_boundary_reminder"].lower()
