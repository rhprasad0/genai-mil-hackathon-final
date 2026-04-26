"""``get_policy_citation`` tool module.

Spec reference: docs/spec.md section 4.5.1.  Returns a verbatim synthetic
demo reference-corpus excerpt by ``citation_id``.  Refuses rather than
fabricate when the corpus does not support the request.
"""

from __future__ import annotations

from typing import Any

from .. import runtime
from ..repository import citations as citations_repo
from ..safety.refusal import (
    REASON_MISSING_REQUIRED_INPUT,
    REASON_UNGROUNDED_CLAIM,
    build,
)
from ._common import _description, not_implemented_response, with_boundary

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


def _citation_payload(row: Any) -> dict[str, Any]:
    return {
        "citation_id": row.citation_id,
        "source_identifier": row.source_identifier,
        "topic": row.topic,
        "excerpt_text": row.excerpt_text,
        "retrieval_anchor": row.retrieval_anchor,
        "applicability_note": row.applicability_note,
    }


def handler(payload: dict[str, Any]) -> dict[str, Any]:
    citation_id = (payload.get("citation_id") or "").strip()

    if not runtime.is_db_available():
        return not_implemented_response(TOOL_NAME)

    if not citation_id:
        return build(
            reason=REASON_MISSING_REQUIRED_INPUT,
            message="get_policy_citation requires a synthetic citation_id input.",
            tool_name=TOOL_NAME,
            target_kind="citation",
            target_id=None,
            voucher_id=None,
            rejected_request=payload,
        ).response.to_dict()

    with runtime.transaction() as conn:
        citation = citations_repo.get_by_id(conn, citation_id)

    if citation is None:
        return build(
            reason=REASON_UNGROUNDED_CLAIM,
            message=(
                "No synthetic demo reference excerpt matches this citation_id. "
                "AO Radar refuses to fabricate citations."
            ),
            tool_name=TOOL_NAME,
            target_kind="citation",
            target_id=citation_id,
            voucher_id=None,
            rejected_request=payload,
        ).response.to_dict()

    return with_boundary(
        {
            "status": "ok",
            "tool": TOOL_NAME,
            "citation": _citation_payload(citation),
        }
    )


__all__ = ["TOOL_NAME", "description", "INPUT_SCHEMA", "handler"]
