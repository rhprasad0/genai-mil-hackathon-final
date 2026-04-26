"""Unit tests for ``ao_radar_mcp.safety.refusal``.

Source of truth: docs/application-implementation-plan.md sections 10 and 11.
"""

from __future__ import annotations

import pytest

from ao_radar_mcp.safety.authority_boundary import HUMAN_AUTHORITY_BOUNDARY_TEXT
from ao_radar_mcp.safety.refusal import (
    REASON_PROHIBITED_ACTION,
    REASON_UNSAFE_WORDING_IN_INPUT,
    REFUSAL_REASONS,
    build,
)


def test_refusal_response_carries_all_required_fields() -> None:
    bundle = build(
        reason=REASON_PROHIBITED_ACTION,
        message="cannot approve a voucher",
        tool_name="set_voucher_review_status",
        target_kind="voucher",
        target_id="V-TEST-1003",
        voucher_id="V-TEST-1003",
        rejected_request={"voucher_id": "V-TEST-1003", "status": "approved"},
    )
    response = bundle.response.to_dict()
    assert response["refused"] is True
    assert response["reason"] == REASON_PROHIBITED_ACTION
    assert "cannot approve" in response["message"].lower()
    assert response["boundary_reminder"] == HUMAN_AUTHORITY_BOUNDARY_TEXT
    assert response["rejected_request"] == {
        "voucher_id": "V-TEST-1003",
        "status": "approved",
    }


def test_refusal_audit_template_carries_canonical_reminder() -> None:
    bundle = build(reason=REASON_PROHIBITED_ACTION)
    audit = bundle.audit_template.to_dict()
    assert audit["event_type"] == "refusal"
    assert audit["human_authority_boundary_reminder"] == HUMAN_AUTHORITY_BOUNDARY_TEXT
    assert "rejected_request" in audit["rationale_metadata"]


def test_unknown_reason_raises() -> None:
    with pytest.raises(ValueError, match="unknown refusal reason"):
        build(reason="totally_unsupported")


def test_sensitive_keys_are_redacted_before_persistence() -> None:
    bundle = build(
        reason=REASON_UNSAFE_WORDING_IN_INPUT,
        rejected_request={
            "voucher_id": "V-TEST-1003",
            "password": "ignore-me",
            "nested": {"api_key": "abcdef"},
        },
    )
    audit = bundle.audit_template.to_dict()
    sanitized = audit["rationale_metadata"]["rejected_request"]
    assert sanitized["password"] == "[redacted]"
    assert sanitized["nested"]["api_key"] == "[redacted]"
    assert sanitized["voucher_id"] == "V-TEST-1003"


def test_all_documented_reason_codes_round_trip() -> None:
    for reason in REFUSAL_REASONS:
        bundle = build(reason=reason)
        assert bundle.response.reason == reason
        assert bundle.audit_template.event_type == "refusal"
