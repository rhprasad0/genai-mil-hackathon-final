"""``request_traveler_clarification`` tool module.

Spec reference: docs/spec.md section 4.5.2. Demo-only: sets internal state
to ``awaiting_traveler_clarification`` and writes a synthetic clarification
note (``ao_notes(kind=synthetic_clarification_request)``).  No real
traveler is contacted.
"""

from __future__ import annotations

from typing import Any

from .. import runtime
from ..audit import AuditEventTemplate, materialize
from ..repository import ao_notes as ao_notes_repo
from ..repository import vouchers as vouchers_repo
from ..safety.refusal import (
    REASON_MISSING_REQUIRED_INPUT,
    REASON_UNSAFE_WORDING_IN_INPUT,
    build,
)
from ..safety.unsafe_wording import check as check_wording
from ._common import _description, not_implemented_response, with_boundary

TOOL_NAME = "request_traveler_clarification"

description = _description(
    "Set the voucher's internal state to awaiting_traveler_clarification "
    "and store a synthetic clarification request body. Demo-only; no "
    "real traveler is contacted and no external system is called."
)

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "voucher_id": {
            "type": "string",
            "description": "Synthetic voucher identifier.",
        },
        "message": {
            "type": "string",
            "minLength": 1,
            "description": "Synthetic clarification message body (validated against unsafe wording).",
        },
        "actor_label": {
            "type": "string",
            "description": "Demo identity (e.g. demo_ao_user_1).",
        },
    },
    "required": ["voucher_id", "message"],
    "additionalProperties": False,
}

_DEFAULT_ACTOR = "demo_ao_user_1"
_NEW_STATUS = "awaiting_traveler_clarification"


def handler(payload: dict[str, Any]) -> dict[str, Any]:
    voucher_id = (payload.get("voucher_id") or "").strip()
    message_body = (payload.get("message") or "").strip()
    actor_label = (payload.get("actor_label") or _DEFAULT_ACTOR).strip() or _DEFAULT_ACTOR

    if not runtime.is_db_available():
        return not_implemented_response(TOOL_NAME)

    if not voucher_id:
        return build(
            reason=REASON_MISSING_REQUIRED_INPUT,
            message="request_traveler_clarification requires a synthetic voucher_id input.",
            tool_name=TOOL_NAME,
            target_kind="note",
            target_id=None,
            voucher_id=None,
            rejected_request=payload,
        ).response.to_dict()

    if not message_body:
        return build(
            reason=REASON_MISSING_REQUIRED_INPUT,
            message="request_traveler_clarification requires a non-empty synthetic message body.",
            tool_name=TOOL_NAME,
            target_kind="note",
            target_id=None,
            voucher_id=voucher_id,
            rejected_request=payload,
        ).response.to_dict()

    wording = check_wording(message_body)
    if not wording.is_safe:
        return build(
            reason=REASON_UNSAFE_WORDING_IN_INPUT,
            message=(
                "Clarification message contains a phrase that implies an "
                "official disposition, fraud allegation, payability/entitlement "
                "claim, or external contact. Rephrase as a neutral question."
            ),
            tool_name=TOOL_NAME,
            target_kind="note",
            target_id=None,
            voucher_id=voucher_id,
            rejected_request={"voucher_id": voucher_id},
            extra_metadata={
                "violation_reason": wording.reason,
                "matched_phrase": wording.matched_phrase,
            },
        ).response.to_dict()

    with runtime.transaction() as conn:
        note_audit = materialize(
            AuditEventTemplate(
                event_type="scoped_write",
                tool_name=TOOL_NAME,
                target_kind="note",
                target_id=None,
                voucher_id=voucher_id,
                actor_label=actor_label,
                rationale_metadata={
                    "reason": "synthetic_clarification_recorded",
                    "kind": "synthetic_clarification_request",
                },
            )
        )
        note = ao_notes_repo.append(
            conn,
            voucher_id=voucher_id,
            finding_id=None,
            kind="synthetic_clarification_request",
            body=message_body,
            actor_label=actor_label,
            audit_event=note_audit.to_dict(),
        )

        status_audit = materialize(
            AuditEventTemplate(
                event_type="scoped_write",
                tool_name=TOOL_NAME,
                target_kind="voucher",
                target_id=voucher_id,
                voucher_id=voucher_id,
                actor_label=actor_label,
                rationale_metadata={"reason": "internal_review_status_update"},
                resulting_status=_NEW_STATUS,
            )
        )
        updated = vouchers_repo.update_review_status(
            conn,
            voucher_id=voucher_id,
            new_status=_NEW_STATUS,
            audit_event=status_audit.to_dict(),
        )
        if updated is None:
            return with_boundary(
                {
                    "status": "not_found",
                    "tool": TOOL_NAME,
                    "voucher_id": voucher_id,
                    "message": "No synthetic voucher with this id was present at status-update time.",
                }
            )

    return with_boundary(
        {
            "status": "ok",
            "tool": TOOL_NAME,
            "voucher_id": voucher_id,
            "review_status": updated.review_status,
            "note": {
                "note_id": note.note_id,
                "kind": note.kind,
                "body": note.body,
                "actor_label": note.actor_label,
                "created_at": note.created_at.isoformat(),
            },
            "audit_events": [
                {
                    "event_id": note_audit.event_id,
                    "event_type": "scoped_write",
                    "target_kind": "note",
                },
                {
                    "event_id": status_audit.event_id,
                    "event_type": "scoped_write",
                    "target_kind": "voucher",
                },
            ],
            "advisory": (
                "Synthetic clarification recorded; no real traveler was contacted. "
                "The official travel system is unchanged."
            ),
        }
    )


__all__ = ["TOOL_NAME", "description", "INPUT_SCHEMA", "handler"]
