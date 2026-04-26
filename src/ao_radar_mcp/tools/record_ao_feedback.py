"""``record_ao_feedback`` tool module.

Spec reference: docs/spec.md section 4.5.2. Captures AO feedback so the
system can improve future triage.  Append-only on ``ao_notes(kind =
ao_feedback)`` plus a paired ``scoped_write`` audit event.
"""

from __future__ import annotations

from typing import Any

from ._common import _description, not_implemented_response

TOOL_NAME = "record_ao_feedback"

description = _description(
    "Capture AO feedback on triage quality. Stored as an internal "
    "ao_notes row of kind=ao_feedback; never used to take official action."
)

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "voucher_id": {
            "type": "string",
            "description": "Synthetic voucher identifier.",
        },
        "finding_id": {
            "type": "string",
            "description": "Optional synthetic finding identifier.",
        },
        "feedback": {
            "type": "string",
            "minLength": 1,
            "description": "Free-text feedback (validated against unsafe wording).",
        },
        "actor_label": {
            "type": "string",
            "description": "Demo identity (e.g. demo_ao_user_1).",
        },
    },
    "required": ["voucher_id", "feedback"],
    "additionalProperties": False,
}


def handler(payload: dict[str, Any]) -> dict[str, Any]:
    # TODO Phase 5: validate unsafe wording, append
    # ao_notes(kind=ao_feedback) and write paired scoped_write audit row.
    return not_implemented_response(TOOL_NAME)


__all__ = ["TOOL_NAME", "description", "INPUT_SCHEMA", "handler"]
