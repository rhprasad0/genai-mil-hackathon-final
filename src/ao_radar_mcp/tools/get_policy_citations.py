"""``get_policy_citations`` tool module.

Spec reference: docs/spec.md section 4.5.1.  Searches the synthetic demo
reference corpus by topic / retrieval anchor and returns matching verbatim
excerpts.
"""

from __future__ import annotations

from typing import Any

from ._common import _description, not_implemented_response

TOOL_NAME = "get_policy_citations"

description = _description(
    "Search the synthetic demo reference corpus and return verbatim "
    "matching excerpts with source identifiers. Refuses rather than "
    "fabricate when no excerpts match."
)

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "Free-form retrieval query.",
        },
        "topic": {
            "type": "string",
            "description": "Optional topic filter from the schema enum.",
        },
        "limit": {
            "type": "integer",
            "minimum": 1,
            "maximum": 25,
            "description": "Optional cap on returned rows.",
        },
    },
    "required": ["query"],
    "additionalProperties": False,
}


def handler(payload: dict[str, Any]) -> dict[str, Any]:
    # TODO Phase 2: fetch via repository.citations.search.
    return not_implemented_response(TOOL_NAME)


__all__ = ["TOOL_NAME", "description", "INPUT_SCHEMA", "handler"]
