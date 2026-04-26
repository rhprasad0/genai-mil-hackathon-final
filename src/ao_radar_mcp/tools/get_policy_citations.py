"""``get_policy_citations`` tool module.

Spec reference: docs/spec.md section 4.5.1.  Searches the synthetic demo
reference corpus by topic / retrieval anchor and returns matching verbatim
excerpts.
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
    query = (payload.get("query") or "").strip()
    topic_raw = payload.get("topic")
    topic = (topic_raw or "").strip() or None
    limit_raw = payload.get("limit")
    try:
        limit = int(limit_raw) if limit_raw is not None else None
    except (TypeError, ValueError):
        limit = None

    if not runtime.is_db_available():
        return not_implemented_response(TOOL_NAME)

    if not query:
        return build(
            reason=REASON_MISSING_REQUIRED_INPUT,
            message="get_policy_citations requires a non-empty query.",
            tool_name=TOOL_NAME,
            target_kind="citation",
            target_id=None,
            voucher_id=None,
            rejected_request=payload,
        ).response.to_dict()

    with runtime.transaction() as conn:
        rows = citations_repo.search(conn, query=query, topic=topic, limit=limit)

    if not rows:
        return build(
            reason=REASON_UNGROUNDED_CLAIM,
            message=(
                "No synthetic demo reference excerpts match this query. "
                "AO Radar refuses to fabricate citations."
            ),
            tool_name=TOOL_NAME,
            target_kind="citation",
            target_id=None,
            voucher_id=None,
            rejected_request={"query": query, "topic": topic},
        ).response.to_dict()

    return with_boundary(
        {
            "status": "ok",
            "tool": TOOL_NAME,
            "query": query,
            "topic": topic,
            "citations": [_citation_payload(row) for row in rows],
            "count": len(rows),
        }
    )


__all__ = ["TOOL_NAME", "description", "INPUT_SCHEMA", "handler"]
