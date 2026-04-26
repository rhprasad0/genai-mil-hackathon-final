"""``get_policy_citation`` tool module.

Spec reference: docs/spec.md section 4.5.1.  Returns a verbatim synthetic
demo reference-corpus excerpt by ``citation_id``.  Refuses rather than
fabricate when the corpus does not support the request.
"""

from __future__ import annotations

from typing import Any

from ._common import _description, not_implemented_response

TOOL_NAME = "get_policy_citation"

description = _description(
    "Return a verbatim synthetic demo reference-corpus excerpt by "
    "citation_id. Refuses rather than fabricate when no excerpt supports "
    "the request."
)

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "citation_id": {
            "type": "string",
            "description": "Synthetic citation identifier (e.g. CITE-RECEIPT-001).",
        },
    },
    "required": ["citation_id"],
    "additionalProperties": False,
}


def handler(payload: dict[str, Any]) -> dict[str, Any]:
    # TODO Phase 2: fetch from repository.citations and refuse with
    # ``ungrounded_claim`` when no row matches.
    return not_implemented_response(TOOL_NAME)


__all__ = ["TOOL_NAME", "description", "INPUT_SCHEMA", "handler"]
