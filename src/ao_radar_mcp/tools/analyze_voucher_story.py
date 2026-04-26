"""``analyze_voucher_story`` tool module.

Spec reference: docs/spec.md section 4.5.1.  Composes pure functions in
``ao_radar_mcp.domain.story_analysis`` + ``missing_information`` over the
repository read shapes.  Carries a ``review_prompt_only`` marker.
"""

from __future__ import annotations

from typing import Any

from ._common import _description, not_implemented_response

TOOL_NAME = "analyze_voucher_story"

description = _description(
    "Return story-coherence findings for a voucher: reconstructed trip-and-"
    "expense narrative, evidence/story gaps, why each gap matters, suggested "
    "AO question, plus a review_prompt_only marker."
)

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "voucher_id": {
            "type": "string",
            "description": "Synthetic voucher identifier (e.g. V-1003).",
        },
    },
    "required": ["voucher_id"],
    "additionalProperties": False,
}


def handler(payload: dict[str, Any]) -> dict[str, Any]:
    # TODO Phase 4: compose domain.story_analysis + repository reads.
    return not_implemented_response(TOOL_NAME)


__all__ = ["TOOL_NAME", "description", "INPUT_SCHEMA", "handler"]
