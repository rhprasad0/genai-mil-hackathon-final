"""``record_ao_note`` tool module.

Spec reference: docs/spec.md section 4.5.2. Stores an AO note tied to a
voucher (and optional finding).  Append-only.  Audit invariant matrix
requires ``event_type=scoped_write`` in the same transaction.
"""

from __future__ import annotations

from typing import Any

from .. import runtime
from ..audit import AuditEventTemplate, materialize
from ..repository import ao_notes as ao_notes_repo
from ..safety.refusal import (
    REASON_MISSING_REQUIRED_INPUT,
    REASON_UNSAFE_WORDING_IN_INPUT,
    build,
)
from ..safety.unsafe_wording import check as check_wording
from ._common import _description, not_implemented_response, with_boundary

TOOL_NAME = "record_ao_note"

description = _description(
    "Store an AO note tied to a voucher (and optional finding). The note "
    "is internal to AO Radar; no external party is contacted and no DTS "
    "state is changed."
)

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "voucher_id": {
            "type": "string",
            "description": "Synthetic voucher identifier.",
        },
        "note": {
            "type": "string",
            "minLength": 1,
            "description": "Free-text reviewer note (validated against unsafe wording).",
        },
        "finding_id": {
            "type": "string",
            "description": "Optional synthetic finding identifier.",
        },
        "actor_label": {
            "type": "string",
            "description": "Demo identity (e.g. demo_ao_user_1).",
        },
    },
    "required": ["voucher_id", "note"],
    "additionalProperties": False,
}

_DEFAULT_ACTOR = "demo_ao_user_1"


def handler(payload: dict[str, Any]) -> dict[str, Any]:
    voucher_id = (payload.get("voucher_id") or "").strip()
    note_body = (payload.get("note") or "").strip()
    finding_id_raw = payload.get("finding_id")
    finding_id = (finding_id_raw or "").strip() or None
    actor_label = (payload.get("actor_label") or _DEFAULT_ACTOR).strip() or _DEFAULT_ACTOR

    if not runtime.is_db_available():
        return not_implemented_response(TOOL_NAME)

    if not voucher_id:
        return build(
            reason=REASON_MISSING_REQUIRED_INPUT,
            message="record_ao_note requires a synthetic voucher_id input.",
            tool_name=TOOL_NAME,
            target_kind="note",
            target_id=None,
            voucher_id=None,
            rejected_request=payload,
        ).response.to_dict()

    if not note_body:
        return build(
            reason=REASON_MISSING_REQUIRED_INPUT,
            message="record_ao_note requires a non-empty note body.",
            tool_name=TOOL_NAME,
            target_kind="note",
            target_id=None,
            voucher_id=voucher_id,
            rejected_request=payload,
        ).response.to_dict()

    wording_result = check_wording(note_body)
    if not wording_result.is_safe:
        return build(
            reason=REASON_UNSAFE_WORDING_IN_INPUT,
            message=(
                "AO note text contains a phrase that implies an official "
                "disposition, fraud allegation, payability/entitlement claim, "
                "or external contact. Rephrase as a review observation."
            ),
            tool_name=TOOL_NAME,
            target_kind="note",
            target_id=None,
            voucher_id=voucher_id,
            rejected_request={"voucher_id": voucher_id, "finding_id": finding_id},
            extra_metadata={
                "violation_reason": wording_result.reason,
                "matched_phrase": wording_result.matched_phrase,
            },
        ).response.to_dict()

    with runtime.transaction() as conn:
        audit_template = AuditEventTemplate(
            event_type="scoped_write",
            tool_name=TOOL_NAME,
            target_kind="note",
            target_id=None,
            voucher_id=voucher_id,
            actor_label=actor_label,
            rationale_metadata={
                "reason": "ao_note_recorded",
                "finding_id": finding_id,
            },
        )
        audit_record = materialize(audit_template)
        persisted = ao_notes_repo.append(
            conn,
            voucher_id=voucher_id,
            finding_id=finding_id,
            kind="ao_note",
            body=note_body,
            actor_label=actor_label,
            audit_event=audit_record.to_dict(),
        )

    return with_boundary(
        {
            "status": "ok",
            "tool": TOOL_NAME,
            "voucher_id": voucher_id,
            "note": {
                "note_id": persisted.note_id,
                "voucher_id": persisted.voucher_id,
                "finding_id": persisted.finding_id,
                "kind": persisted.kind,
                "body": persisted.body,
                "actor_label": persisted.actor_label,
                "created_at": persisted.created_at.isoformat(),
            },
            "audit_event_type": "scoped_write",
            "audit_event_id": audit_record.event_id,
        }
    )


__all__ = ["TOOL_NAME", "description", "INPUT_SCHEMA", "handler"]
