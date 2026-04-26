"""``get_audit_trail`` tool module.

Spec reference: docs/spec.md section 4.5.2. Returns the ordered list of
audit events for a voucher (read of ``workflow_events`` ordered by
``occurred_at``).
"""

from __future__ import annotations

from typing import Any

from ._common import _description, not_implemented_response

TOOL_NAME = "get_audit_trail"

description = _description(
    "Return the ordered list of audit events for a synthetic voucher. "
    "Each event carries the canonical human-authority boundary reminder."
)

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "voucher_id": {
            "type": "string",
            "description": "Synthetic voucher identifier.",
        },
        "limit": {
            "type": "integer",
            "minimum": 1,
            "maximum": 500,
            "description": "Optional cap on returned rows.",
        },
    },
    "required": ["voucher_id"],
    "additionalProperties": False,
}


def handler(payload: dict[str, Any]) -> dict[str, Any]:
    # TODO Phase 5: read workflow_events ordered by occurred_at via
    # repository.workflow_events.
    return not_implemented_response(TOOL_NAME)


__all__ = ["TOOL_NAME", "description", "INPUT_SCHEMA", "handler"]
