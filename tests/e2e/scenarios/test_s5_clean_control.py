"""E2E scenario S5: clean control packet (V-1001).

Source of truth: docs/testing-plan.md section 8 S5.

The brief for V-1001 is the synthetic clean-control case: zero story
findings, zero missing-information items, low brief uncertainty, and the
canonical human-authority boundary text on the persisted brief.
"""

from __future__ import annotations

import pytest

from .._jsonrpc import call_tool

pytestmark = pytest.mark.e2e


def test_e2e_clean_control_packet(mcp_base_url: str) -> None:
    structured = call_tool(
        mcp_base_url,
        "prepare_ao_review_brief",
        {"voucher_id": "V-1001", "actor_label": "ao-radar-e2e"},
    )

    assert structured["status"] == "ok", structured
    assert structured["voucher_id"] == "V-1001"
    assert structured["audit_event_type"] in {"retrieval", "generation"}
    assert structured["review_prompt_only"] is True

    findings = structured["findings"]
    missing = structured["missing_information_items"]
    assert findings == [], f"clean control should have no findings, got {findings}"
    assert missing == [], f"clean control should have no missing-info items, got {missing}"

    brief = structured["brief"]
    assert brief["brief_uncertainty"] == "low", brief
    assert brief["is_partial"] is False, brief
    boundary_text = brief["human_authority_boundary_text"].lower()
    for clause in ("approve", "deny", "certify", "entitlement", "payability", "fraud"):
        assert clause in boundary_text, brief
    assert "approving official" in structured["boundary_reminder"].lower()
