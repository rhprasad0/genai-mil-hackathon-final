"""``export_review_brief`` tool module.

Spec reference: docs/spec.md section 4.5.1, FR-12, AC-9. Resolves the
latest brief for a voucher, or a specific ``brief_id``, and emits a
portable ``markdown`` or ``json`` payload with the canonical boundary
reminder.  Writes ``workflow_events.event_type = export``.
"""

from __future__ import annotations

from typing import Any

from ._common import _description, not_implemented_response

TOOL_NAME = "export_review_brief"

description = _description(
    "Export the latest review brief for a voucher, or a specific brief_id, "
    "in a portable markdown or json payload. The export carries the "
    "canonical human-authority boundary reminder and writes one export "
    "audit event."
)

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "voucher_id": {
            "type": "string",
            "description": "Synthetic voucher identifier; resolves the latest brief.",
        },
        "brief_id": {
            "type": "string",
            "description": "Specific synthetic brief identifier (e.g. BRIEF-V-1003-1).",
        },
        "format": {
            "type": "string",
            "enum": ["markdown", "json"],
            "default": "markdown",
            "description": "Controlled export format.",
        },
    },
    "anyOf": [
        {"required": ["voucher_id"]},
        {"required": ["brief_id"]},
    ],
    "additionalProperties": False,
}


def handler(payload: dict[str, Any]) -> dict[str, Any]:
    # TODO Phase 4: resolve brief, render markdown/json, write export event.
    return not_implemented_response(TOOL_NAME)


__all__ = ["TOOL_NAME", "description", "INPUT_SCHEMA", "handler"]
