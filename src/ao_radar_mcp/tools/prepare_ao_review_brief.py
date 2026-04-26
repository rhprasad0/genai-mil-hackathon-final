"""``prepare_ao_review_brief`` tool module.

Spec reference: docs/spec.md section 4.5.1, FR-14, AC-15.  Central fusion
tool: combines packet, traveler profile, prior summaries, signals,
story-coherence findings, and policy citations into a single auditable
pre-decision review brief.  Persists a new ``review_briefs`` row and emits
``event_type=generation`` in the same transaction (audit invariant matrix).
"""

from __future__ import annotations

from typing import Any

from ._common import _description, not_implemented_response

TOOL_NAME = "prepare_ao_review_brief"

description = _description(
    "Assemble a pre-decision review brief that fuses packet evidence, "
    "traveler profile, prior summaries, signals, story-coherence findings, "
    "and synthetic demo reference-corpus citations. The brief packages "
    "evidence for AO review and never recommends an official disposition."
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
    # TODO Phase 4: compose domain.brief_assembly with repository reads,
    # persist a ``review_briefs`` version, and write
    # ``event_type=generation`` in the same transaction.
    return not_implemented_response(TOOL_NAME)


__all__ = ["TOOL_NAME", "description", "INPUT_SCHEMA", "handler"]
