"""``draft_return_comment`` tool module.

Spec reference: docs/spec.md section 4.5.2. Stores non-official draft
clarification text the reviewer can adapt; nothing is sent anywhere.
Persisted as ``ao_notes(kind=draft_clarification)``.
"""

from __future__ import annotations

from typing import Any

from ._common import _description, not_implemented_response

TOOL_NAME = "draft_return_comment"

description = _description(
    "Store non-official draft clarification text for the reviewer to adapt. "
    "Draft only; nothing is sent anywhere. The system never recommends an "
    "official disposition."
)

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "voucher_id": {
            "type": "string",
            "description": "Synthetic voucher identifier.",
        },
        "text": {
            "type": "string",
            "minLength": 1,
            "description": "Draft clarification text (validated against unsafe wording).",
        },
        "actor_label": {
            "type": "string",
            "description": "Demo identity (e.g. demo_ao_user_1).",
        },
    },
    "required": ["voucher_id", "text"],
    "additionalProperties": False,
}


def handler(payload: dict[str, Any]) -> dict[str, Any]:
    # TODO Phase 5: validate unsafe wording (allow negative boundary text),
    # append ao_notes(kind=draft_clarification), write paired scoped_write
    # audit row.
    return not_implemented_response(TOOL_NAME)


__all__ = ["TOOL_NAME", "description", "INPUT_SCHEMA", "handler"]
