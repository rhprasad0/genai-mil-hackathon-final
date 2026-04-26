"""``record_ao_note`` tool module.

Spec reference: docs/spec.md section 4.5.2. Stores an AO note tied to a
voucher (and optional finding).  Append-only.  Audit invariant matrix
requires ``event_type=scoped_write`` in the same transaction.
"""

from __future__ import annotations

from typing import Any

from ._common import _description, not_implemented_response

TOOL_NAME = "record_ao_note"

description = _description(
    "Store an AO note tied to a voucher (and optional finding). The note "
    "is internal to AO Radar; no external party is contacted and no DTS "
    "state is changed."
)

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "voucher_id": {
            "type": "string",
            "description": "Synthetic voucher identifier.",
        },
        "note": {
            "type": "string",
            "minLength": 1,
            "description": "Free-text reviewer note (validated against unsafe wording).",
        },
        "finding_id": {
            "type": "string",
            "description": "Optional synthetic finding identifier.",
        },
        "actor_label": {
            "type": "string",
            "description": "Demo identity (e.g. demo_ao_user_1).",
        },
    },
    "required": ["voucher_id", "note"],
    "additionalProperties": False,
}


def handler(payload: dict[str, Any]) -> dict[str, Any]:
    # TODO Phase 5: validate unsafe wording, append ao_notes(kind=ao_note),
    # write paired ``scoped_write`` event in same transaction.
    return not_implemented_response(TOOL_NAME)


__all__ = ["TOOL_NAME", "description", "INPUT_SCHEMA", "handler"]
