"""Deployed E2E refusal regression for blocked-status round-trip.

Source of truth: docs/testing-plan.md section 6 G5.

Each blocked status value (``approved``, ``denied``, ``certified``,
``submitted``, ``paid``, ``fraud``, ``returned``, ``cancelled``,
``amended``, …) routed through ``set_voucher_review_status`` must produce
a refusal envelope and a paired ``event_type = refusal`` row in
``workflow_events``.  This test exercises a representative subset to
prove the round-trip works without polluting the audit log with one row
per spec value.
"""

from __future__ import annotations

import pytest

from .._jsonrpc import call_tool

pytestmark = pytest.mark.e2e

_VOUCHER_ID = "V-1001"
_BLOCKED_STATUSES = ("approved", "denied", "certified", "fraud")


def test_deployed_blocked_status_values_refused_with_audit(mcp_base_url: str) -> None:
    new_event_ids: list[str] = []
    for status in _BLOCKED_STATUSES:
        response = call_tool(
            mcp_base_url,
            "set_voucher_review_status",
            {
                "voucher_id": _VOUCHER_ID,
                "status": status,
                "actor_label": "ao-radar-e2e",
            },
            request_id=f"blocked-{status}",
        )
        assert response["refused"] is True, (status, response)
        assert response["reason"] == "prohibited_action", (status, response)
        assert "approving official" in response["boundary_reminder"].lower(), response
        assert response.get("audit_event_type") == "refusal", response
        event_id = response.get("audit_event_id")
        assert isinstance(event_id, str) and event_id, response
        new_event_ids.append(event_id)

    audit = call_tool(
        mcp_base_url,
        "get_audit_trail",
        {"voucher_id": _VOUCHER_ID},
    )
    assert audit["status"] == "ok", audit
    audit_event_ids = {event["event_id"] for event in audit["events"]}
    missing = [event_id for event_id in new_event_ids if event_id not in audit_event_ids]
    assert not missing, f"refusal events not present in audit trail: {missing}"

    refusal_events = [
        event
        for event in audit["events"]
        if event["event_id"] in new_event_ids
    ]
    for event in refusal_events:
        assert event["event_type"] == "refusal", event
        assert event["tool_name"] == "set_voucher_review_status"
        assert event["target_kind"] == "voucher"
        assert event["target_id"] == _VOUCHER_ID
        assert "approving official" in event["human_authority_boundary_reminder"].lower()
