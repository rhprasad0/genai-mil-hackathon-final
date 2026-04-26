"""``set_voucher_review_status`` tool module.

Spec reference: docs/spec.md sections 4.5.2 and 4.5.3.  Updates the
voucher's internal review status.  Allowed values are exactly the spec
4.5.3 enumeration; blocked values (approved, denied, certified, submitted,
paid, fraud, returned, cancelled, amended, etc.) are refused with a
``prohibited_action`` reason.
"""

from __future__ import annotations

from typing import Any

from ..safety.controlled_status import (
    ALLOWED_VOUCHER_REVIEW_STATUSES,
    is_allowed_voucher_review_status,
    is_blocked_status,
)
from ..safety.refusal import (
    REASON_PROHIBITED_ACTION,
    REASON_UNSUPPORTED_STATUS_VALUE,
    build,
)
from ._common import _description, not_implemented_response

TOOL_NAME = "set_voucher_review_status"

description = _description(
    "Update the voucher's internal review status. Allowed values: "
    "needs_review, in_review, awaiting_traveler_clarification, "
    "ready_for_human_decision, closed_in_demo. Values that imply official "
    "action (approved, denied, certified, submitted, paid, fraud) are "
    "refused. The status never represents an official DTS state."
)

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "voucher_id": {
            "type": "string",
            "description": "Synthetic voucher identifier.",
        },
        "status": {
            "type": "string",
            "enum": sorted(ALLOWED_VOUCHER_REVIEW_STATUSES),
            "description": "Controlled internal review status.",
        },
        "actor_label": {
            "type": "string",
            "description": "Demo identity (e.g. demo_ao_user_1).",
        },
    },
    "required": ["voucher_id", "status"],
    "additionalProperties": False,
}


def handler(payload: dict[str, Any]) -> dict[str, Any]:
    voucher_id = payload.get("voucher_id")
    status = (payload.get("status") or "").strip()
    if is_blocked_status(status):
        return build(
            reason=REASON_PROHIBITED_ACTION,
            message=(
                "Voucher review status cannot be set to a blocked value. "
                "AO Radar does not approve, deny, certify, return, cancel, "
                "amend, submit, or otherwise take official action."
            ),
            tool_name=TOOL_NAME,
            target_kind="voucher",
            target_id=voucher_id,
            voucher_id=voucher_id,
            rejected_request={"voucher_id": voucher_id, "status": status},
        ).response.to_dict()
    if status and not is_allowed_voucher_review_status(status):
        return build(
            reason=REASON_UNSUPPORTED_STATUS_VALUE,
            message=(
                "Voucher review status must be one of "
                f"{sorted(ALLOWED_VOUCHER_REVIEW_STATUSES)}."
            ),
            tool_name=TOOL_NAME,
            target_kind="voucher",
            target_id=voucher_id,
            voucher_id=voucher_id,
            rejected_request={"voucher_id": voucher_id, "status": status},
        ).response.to_dict()
    # TODO Phase 5: update vouchers.review_status, write the paired
    # scoped_write audit row inside the same transaction.
    return not_implemented_response(TOOL_NAME)


__all__ = ["TOOL_NAME", "description", "INPUT_SCHEMA", "handler"]
