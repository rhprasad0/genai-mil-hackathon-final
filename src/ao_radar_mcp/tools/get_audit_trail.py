"""``get_audit_trail`` tool module.

Spec reference: docs/spec.md section 4.5.2. Returns the ordered list of
audit events for a voucher (read of ``workflow_events`` ordered by
``occurred_at``).
"""

from __future__ import annotations

from typing import Any

from .. import runtime
from ..repository import workflow_events as wf_repo
from ..safety.refusal import REASON_MISSING_REQUIRED_INPUT, build
from ._common import _description, not_implemented_response, to_jsonable, with_boundary

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


def _event_payload(row: Any) -> dict[str, Any]:
    return {
        "event_id": row.event_id,
        "voucher_id": row.voucher_id,
        "actor_label": row.actor_label,
        "occurred_at": row.occurred_at.isoformat(),
        "event_type": row.event_type,
        "tool_name": row.tool_name,
        "target_kind": row.target_kind,
        "target_id": row.target_id,
        "resulting_status": row.resulting_status,
        "rationale_metadata": to_jsonable(row.rationale_metadata),
        "human_authority_boundary_reminder": row.human_authority_boundary_reminder,
    }


def handler(payload: dict[str, Any]) -> dict[str, Any]:
    voucher_id = (payload.get("voucher_id") or "").strip()
    limit = payload.get("limit")
    if limit is not None:
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = None

    if not runtime.is_db_available():
        return not_implemented_response(TOOL_NAME)

    if not voucher_id:
        return build(
            reason=REASON_MISSING_REQUIRED_INPUT,
            message="get_audit_trail requires a synthetic voucher_id input.",
            tool_name=TOOL_NAME,
            target_kind="voucher",
            target_id=None,
            voucher_id=None,
            rejected_request=payload,
        ).response.to_dict()

    with runtime.transaction() as conn:
        events = wf_repo.list_for_voucher(conn, voucher_id, limit=limit)

    return with_boundary(
        {
            "status": "ok",
            "tool": TOOL_NAME,
            "voucher_id": voucher_id,
            "events": [_event_payload(event) for event in events],
            "count": len(events),
        }
    )


__all__ = ["TOOL_NAME", "description", "INPUT_SCHEMA", "handler"]
