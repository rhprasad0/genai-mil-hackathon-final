"""E2E scenario S2: ambiguous LOA / mis-click / forced-audit (V-1004).

Source of truth: docs/testing-plan.md section 8 S2.

The seeded V-1004 brief surfaces the ambiguous funding-reference label,
the miscategorized lodging-vs-meals line, and a forced audit-receipt-review
finding. We exercise ``prepare_ao_review_brief`` to confirm those findings
flow through the deployed pipeline, then ``record_ao_note`` to assert the
audit invariant (one ``scoped_write`` event per note write).
"""

from __future__ import annotations

import pytest

from .._jsonrpc import call_tool

pytestmark = pytest.mark.e2e

_VOUCHER_ID = "V-1004"
_REQUIRED_CATEGORIES = {
    "ambiguous_loa_or_funding_reference",
    "miscategorized_line_item",
    "forced_audit_receipt_review",
}


def test_e2e_ambiguous_loa_misclick_math(mcp_base_url: str) -> None:
    brief_response = call_tool(
        mcp_base_url,
        "prepare_ao_review_brief",
        {"voucher_id": _VOUCHER_ID, "actor_label": "ao-radar-e2e"},
    )
    assert brief_response["status"] == "ok", brief_response
    finding_categories = {finding["category"] for finding in brief_response["findings"]}
    missing = _REQUIRED_CATEGORIES - finding_categories
    assert not missing, f"missing categories: {missing}; got {finding_categories}"

    note_text = (
        "Synthetic AO note: holding for clarification on the ambiguous LOA "
        "label and the miscategorized lodging line; review prompt only."
    )
    note_response = call_tool(
        mcp_base_url,
        "record_ao_note",
        {
            "voucher_id": _VOUCHER_ID,
            "note": note_text,
            "actor_label": "ao-radar-e2e",
        },
    )
    assert note_response["status"] == "ok", note_response
    assert note_response["audit_event_type"] == "scoped_write"
    note_id = note_response["note"]["note_id"]
    assert note_id, note_response

    audit = call_tool(
        mcp_base_url,
        "get_audit_trail",
        {"voucher_id": _VOUCHER_ID},
    )
    assert audit["status"] == "ok", audit
    matched = [
        event
        for event in audit["events"]
        if event["target_id"] == note_id and event["event_type"] == "scoped_write"
    ]
    assert len(matched) == 1, audit
    assert matched[0]["tool_name"] == "record_ao_note"
    assert "approving official" in matched[0]["human_authority_boundary_reminder"].lower()
