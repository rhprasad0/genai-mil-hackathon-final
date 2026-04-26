"""Controlled-status enum and blocked-value tests.

Source of truth: docs/spec.md sections 4.5.2/4.5.3 and
docs/schema-implementation-plan.md section 6.4.
"""

from __future__ import annotations

import pytest

from ao_radar_mcp.safety.controlled_status import (
    ALLOWED_FINDING_REVIEW_STATES,
    ALLOWED_VOUCHER_REVIEW_STATUSES,
    BLOCKED_STATUS_VALUES,
    is_allowed_finding_review_state,
    is_allowed_voucher_review_status,
    is_blocked_status,
    normalize,
)


@pytest.mark.parametrize(
    "value",
    sorted(ALLOWED_VOUCHER_REVIEW_STATUSES),
)
def test_allowed_voucher_review_status_accepted(value: str) -> None:
    assert is_allowed_voucher_review_status(value)
    assert not is_blocked_status(value)


@pytest.mark.parametrize(
    "value",
    sorted(ALLOWED_FINDING_REVIEW_STATES),
)
def test_allowed_finding_review_state_accepted(value: str) -> None:
    assert is_allowed_finding_review_state(value)
    assert not is_blocked_status(value)


@pytest.mark.parametrize(
    "value",
    sorted(BLOCKED_STATUS_VALUES),
)
def test_blocked_status_values_blocked(value: str) -> None:
    assert is_blocked_status(value)
    assert not is_allowed_voucher_review_status(value)
    assert not is_allowed_finding_review_state(value)


def test_blocked_status_normalization_handles_case_and_whitespace() -> None:
    assert is_blocked_status("APPROVED")
    assert is_blocked_status("  approve  ")
    assert is_blocked_status("Fraud")


def test_normalize_handles_none() -> None:
    assert normalize(None) == ""
    assert not is_blocked_status(None)


def test_blocklist_covers_spec_section_6_4() -> None:
    """Spot-check that every category from schema plan section 6.4 is present."""

    must_contain = {
        "approved",
        "denied",
        "rejected",
        "certified",
        "submitted",
        "returned",
        "cancelled",
        "amended",
        "paid",
        "payable",
        "fraud",
        "fraudulent",
        "misuse",
        "abuse",
        "misconduct",
        "entitled",
        "entitlement_determined",
        "escalated_to_investigators",
        "notify_command",
        "contact_traveler",
    }
    assert must_contain.issubset(BLOCKED_STATUS_VALUES)


def test_allowed_voucher_review_statuses_are_exactly_spec_4_5_3() -> None:
    expected = {
        "needs_review",
        "in_review",
        "awaiting_traveler_clarification",
        "ready_for_human_decision",
        "closed_in_demo",
    }
    assert ALLOWED_VOUCHER_REVIEW_STATUSES == expected


def test_allowed_finding_review_states_are_exactly_spec_4_5_2() -> None:
    expected = {
        "open",
        "reviewed_explained",
        "reviewed_unresolved",
        "needs_followup",
    }
    assert ALLOWED_FINDING_REVIEW_STATES == expected
