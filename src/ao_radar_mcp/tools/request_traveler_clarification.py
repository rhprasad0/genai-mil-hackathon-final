"""``request_traveler_clarification`` tool module.

Spec reference: docs/spec.md section 4.5.2. Demo-only: sets internal state
to ``awaiting_traveler_clarification`` and writes a synthetic clarification
note (``ao_notes(kind=synthetic_clarification_request)``).  No real
traveler is contacted.
"""

from __future__ import annotations

from typing import Any

from ._common import _description, not_implemented_response

TOOL_NAME = "request_traveler_clarification"

description = _description(
    "Set the voucher's internal state to awaiting_traveler_clarification "
    "and store a synthetic clarification request body. Demo-only; no "
    "real traveler is contacted and no external system is called."
)

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "voucher_id": {
            "type": "string",
            "description": "Synthetic voucher identifier.",
        },
        "message": {
            "type": "string",
            "minLength": 1,
            "description": "Synthetic clarification message body (validated against unsafe wording).",
        },
        "actor_label": {
            "type": "string",
            "description": "Demo identity (e.g. demo_ao_user_1).",
        },
    },
    "required": ["voucher_id", "message"],
    "additionalProperties": False,
}


def handler(payload: dict[str, Any]) -> dict[str, Any]:
    # TODO Phase 5: validate unsafe wording, set
    # vouchers.review_status=awaiting_traveler_clarification, append
    # ao_notes(kind=synthetic_clarification_request), write the paired
    # scoped_write audit row in the SAME transaction.
    return not_implemented_response(TOOL_NAME)


__all__ = ["TOOL_NAME", "description", "INPUT_SCHEMA", "handler"]
