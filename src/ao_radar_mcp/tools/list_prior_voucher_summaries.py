"""``list_prior_voucher_summaries`` tool module.

Spec reference: docs/spec.md section 4.5.1. Returns short synthetic prior
voucher summaries for the same traveler (baseline comparison only; no
intent inference).
"""

from __future__ import annotations

from typing import Any

from ._common import _description, not_implemented_response

TOOL_NAME = "list_prior_voucher_summaries"

description = _description(
    "Return synthetic prior voucher summaries for the same traveler "
    "(baseline comparison only; no intent inference)."
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
    # TODO Phase 2: fetch from repository.prior_summaries.
    return not_implemented_response(TOOL_NAME)


__all__ = ["TOOL_NAME", "description", "INPUT_SCHEMA", "handler"]
