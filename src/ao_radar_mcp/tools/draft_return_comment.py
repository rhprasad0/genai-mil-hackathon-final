"""``draft_return_comment`` tool module.

Spec reference: docs/spec.md section 4.5.2. Stores non-official draft
clarification text the reviewer can adapt; nothing is sent anywhere.
Persisted as ``ao_notes(kind=draft_clarification)``.
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

TOOL_NAME = "draft_return_comment"

description = _description(
    "Store non-official draft clarification text for the reviewer to adapt. "
    "Draft only; nothing is sent anywhere. The system never recommends an "
    "official disposition."
)

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "voucher_id": {
            "type": "string",
            "description": "Synthetic voucher identifier.",
        },
        "text": {
            "type": "string",
            "minLength": 1,
            "description": "Draft clarification text (validated against unsafe wording).",
        },
        "actor_label": {
            "type": "string",
            "description": "Demo identity (e.g. demo_ao_user_1).",
        },
    },
    "required": ["voucher_id", "text"],
    "additionalProperties": False,
}

_DEFAULT_ACTOR = "demo_ao_user_1"


def handler(payload: dict[str, Any]) -> dict[str, Any]:
    voucher_id = (payload.get("voucher_id") or "").strip()
    text_body = (payload.get("text") or "").strip()
    actor_label = (payload.get("actor_label") or _DEFAULT_ACTOR).strip() or _DEFAULT_ACTOR

    if not runtime.is_db_available():
        return not_implemented_response(TOOL_NAME)

    if not voucher_id:
        return build(
            reason=REASON_MISSING_REQUIRED_INPUT,
            message="draft_return_comment requires a synthetic voucher_id input.",
            tool_name=TOOL_NAME,
            target_kind="note",
            target_id=None,
            voucher_id=None,
            rejected_request=payload,
        ).response.to_dict()

    if not text_body:
        return build(
            reason=REASON_MISSING_REQUIRED_INPUT,
            message="draft_return_comment requires non-empty draft text.",
            tool_name=TOOL_NAME,
            target_kind="note",
            target_id=None,
            voucher_id=voucher_id,
            rejected_request=payload,
        ).response.to_dict()

    wording = check_wording(text_body)
    if not wording.is_safe:
        return build(
            reason=REASON_UNSAFE_WORDING_IN_INPUT,
            message=(
                "Draft text contains a phrase that implies an official "
                "disposition, fraud allegation, payability/entitlement claim, "
                "or external contact. Rephrase as a neutral clarification."
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
        audit_template = AuditEventTemplate(
            event_type="scoped_write",
            tool_name=TOOL_NAME,
            target_kind="note",
            target_id=None,
            voucher_id=voucher_id,
            actor_label=actor_label,
            rationale_metadata={
                "reason": "draft_clarification_recorded",
                "kind": "draft_clarification",
            },
        )
        audit_record = materialize(audit_template)
        persisted = ao_notes_repo.append(
            conn,
            voucher_id=voucher_id,
            finding_id=None,
            kind="draft_clarification",
            body=text_body,
            actor_label=actor_label,
            audit_event=audit_record.to_dict(),
        )

    return with_boundary(
        {
            "status": "ok",
            "tool": TOOL_NAME,
            "voucher_id": voucher_id,
            "draft": {
                "note_id": persisted.note_id,
                "voucher_id": persisted.voucher_id,
                "kind": persisted.kind,
                "body": persisted.body,
                "actor_label": persisted.actor_label,
                "created_at": persisted.created_at.isoformat(),
            },
            "audit_event_type": "scoped_write",
            "audit_event_id": audit_record.event_id,
            "advisory": (
                "Draft only. Nothing was sent. The reviewer adapts and "
                "delivers any clarification through the official travel system."
            ),
        }
    )


__all__ = ["TOOL_NAME", "description", "INPUT_SCHEMA", "handler"]
