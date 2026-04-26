"""``mark_finding_reviewed`` tool module.

Spec reference: docs/spec.md section 4.5.2. Updates a finding's review
state to one of the controlled enum values; rejects blocked statuses with a
refusal and ``event_type=refusal`` audit row.
"""

from __future__ import annotations

from typing import Any

from ..safety.controlled_status import (
    ALLOWED_FINDING_REVIEW_STATES,
    is_allowed_finding_review_state,
    is_blocked_status,
)
from ..safety.refusal import (
    REASON_PROHIBITED_ACTION,
    REASON_UNSUPPORTED_STATUS_VALUE,
    build,
)
from ._common import _description, not_implemented_response

TOOL_NAME = "mark_finding_reviewed"

description = _description(
    "Update the synthetic finding's review state. Allowed values: "
    "open, reviewed_explained, reviewed_unresolved, needs_followup. "
    "Blocked values (approved, denied, certified, submitted, paid, fraud, "
    "returned, cancelled, amended) are refused."
)

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "finding_id": {
            "type": "string",
            "description": "Synthetic finding identifier.",
        },
        "status": {
            "type": "string",
            "enum": sorted(ALLOWED_FINDING_REVIEW_STATES),
            "description": "Allowed finding review state.",
        },
        "actor_label": {
            "type": "string",
            "description": "Demo identity (e.g. demo_ao_user_1).",
        },
    },
    "required": ["finding_id", "status"],
    "additionalProperties": False,
}


def handler(payload: dict[str, Any]) -> dict[str, Any]:
    status = (payload.get("status") or "").strip()
    finding_id = payload.get("finding_id")
    if is_blocked_status(status):
        return build(
            reason=REASON_PROHIBITED_ACTION,
            message=(
                "Finding review state cannot be set to a blocked value. "
                "AO Radar does not approve, deny, certify, return, cancel, "
                "amend, submit, or otherwise take official action."
            ),
            tool_name=TOOL_NAME,
            target_kind="finding",
            target_id=finding_id,
            rejected_request={"status": status, "finding_id": finding_id},
        ).response.to_dict()
    if status and not is_allowed_finding_review_state(status):
        return build(
            reason=REASON_UNSUPPORTED_STATUS_VALUE,
            message=(
                "Finding review state must be one of "
                f"{sorted(ALLOWED_FINDING_REVIEW_STATES)}."
            ),
            tool_name=TOOL_NAME,
            target_kind="finding",
            target_id=finding_id,
            rejected_request={"status": status, "finding_id": finding_id},
        ).response.to_dict()
    # TODO Phase 5: update ``story_findings.review_state`` and write paired
    # ``scoped_write`` audit row in same transaction.
    return not_implemented_response(TOOL_NAME)


__all__ = ["TOOL_NAME", "description", "INPUT_SCHEMA", "handler"]
