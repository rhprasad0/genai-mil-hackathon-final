"""Controlled review-status enums and the blocked-value list.

Sources of truth:
  - docs/spec.md section 4.5.3 (allowed voucher review statuses)
  - docs/spec.md section 4.5.2 (allowed finding review states)
  - docs/schema-implementation-plan.md section 6.4 (blocked-status list)

The schema enforces the same constraints with CHECKs on
``vouchers.review_status``, ``story_findings.review_state``, and
``workflow_events.resulting_status``. This module mirrors them so the
application can return a refusal with an actionable reason before the
database round-trip.
"""

from __future__ import annotations

from typing import Final

ALLOWED_VOUCHER_REVIEW_STATUSES: Final[frozenset[str]] = frozenset(
    {
        "needs_review",
        "in_review",
        "awaiting_traveler_clarification",
        "ready_for_human_decision",
        "closed_in_demo",
    }
)

ALLOWED_FINDING_REVIEW_STATES: Final[frozenset[str]] = frozenset(
    {
        "open",
        "reviewed_explained",
        "reviewed_unresolved",
        "needs_followup",
    }
)

BLOCKED_STATUS_VALUES: Final[frozenset[str]] = frozenset(
    {
        "approved",
        "approve",
        "denied",
        "deny",
        "rejected",
        "reject",
        "certified",
        "certify",
        "submitted",
        "submit",
        "submitted_to_dts",
        "returned",
        "return",
        "return_voucher",
        "officially_returned",
        "cancelled",
        "canceled",
        "cancel",
        "amended",
        "amend",
        "paid",
        "payable",
        "nonpayable",
        "ready_for_payment",
        "payment_ready",
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
)


def normalize(value: str | None) -> str:
    """Lowercase and strip whitespace; treat ``None`` as empty."""

    if value is None:
        return ""
    return value.strip().lower()


def is_blocked_status(value: str | None) -> bool:
    """Return ``True`` if ``value`` matches any blocked-status token."""

    return normalize(value) in BLOCKED_STATUS_VALUES


def is_allowed_voucher_review_status(value: str | None) -> bool:
    return normalize(value) in ALLOWED_VOUCHER_REVIEW_STATUSES


def is_allowed_finding_review_state(value: str | None) -> bool:
    return normalize(value) in ALLOWED_FINDING_REVIEW_STATES


__all__ = [
    "ALLOWED_VOUCHER_REVIEW_STATUSES",
    "ALLOWED_FINDING_REVIEW_STATES",
    "BLOCKED_STATUS_VALUES",
    "normalize",
    "is_blocked_status",
    "is_allowed_voucher_review_status",
    "is_allowed_finding_review_state",
]
