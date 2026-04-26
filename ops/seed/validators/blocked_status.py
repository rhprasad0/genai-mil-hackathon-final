"""Blocked-status validator.

Imports ``BLOCKED_STATUS_VALUES`` from ``ao_radar_mcp.safety.controlled_status``
to avoid drift, and asserts no ``vouchers.review_status``,
``story_findings.review_state``, or ``workflow_events.resulting_status``
matches a blocklist entry.

Refusal events legitimately store the rejected requested-status string under
``rationale_metadata.rejected_input``. That field is allowed to mention a
blocked value because it is typed as user-rejected input, not as a
system-authored status.
"""

from __future__ import annotations

from typing import Any

from ao_radar_mcp.safety.controlled_status import BLOCKED_STATUS_VALUES, normalize


class BlockedStatusError(ValueError):
    pass


def _check_status_value(label: str, value: Any) -> None:
    if value is None:
        return
    if not isinstance(value, str):
        raise BlockedStatusError(f"{label} must be a string, got {type(value).__name__}")
    if normalize(value) in BLOCKED_STATUS_VALUES:
        raise BlockedStatusError(
            f"{label}={value!r} is in BLOCKED_STATUS_VALUES (schema plan section 6.4)"
        )


def validate_corpus(corpus: Any) -> None:
    for v_row in corpus.vouchers:
        _check_status_value(
            f"vouchers.review_status[voucher_id={v_row['voucher_id']}]",
            v_row.get("review_status"),
        )
    for f_row in corpus.story_findings:
        _check_status_value(
            f"story_findings.review_state[finding_id={f_row['finding_id']}]",
            f_row.get("review_state"),
        )
    for ev in corpus.workflow_events:
        _check_status_value(
            f"workflow_events.resulting_status[event_id={ev['event_id']}]",
            ev.get("resulting_status"),
        )


__all__ = ["BlockedStatusError", "validate_corpus"]
