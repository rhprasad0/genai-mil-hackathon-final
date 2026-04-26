"""``get_traveler_profile`` tool module.

Spec reference: docs/spec.md section 4.5.1. Returns a synthetic traveler
profile (no real PII; ``(Synthetic Demo)`` markers required by schema).
"""

from __future__ import annotations

from typing import Any

from ._common import _description, not_implemented_response

TOOL_NAME = "get_traveler_profile"

description = _description(
    "Return the synthetic traveler profile (role, typical trip pattern, "
    "prior-correction summary). No real PII."
)

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "traveler_id": {
            "type": "string",
            "description": "Synthetic traveler identifier (e.g. T-101).",
        },
    },
    "required": ["traveler_id"],
    "additionalProperties": False,
}


def handler(payload: dict[str, Any]) -> dict[str, Any]:
    # TODO Phase 2: fetch from repository.travelers.
    return not_implemented_response(TOOL_NAME)


__all__ = ["TOOL_NAME", "description", "INPUT_SCHEMA", "handler"]
