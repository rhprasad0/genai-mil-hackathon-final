"""``set_voucher_review_status`` tool module.

Spec reference: docs/spec.md sections 4.5.2 and 4.5.3.  Updates the
voucher's internal review status.  Allowed values are exactly the spec
4.5.3 enumeration; blocked values (approved, denied, certified, submitted,
paid, fraud, returned, cancelled, amended, etc.) are refused with a
``prohibited_action`` reason and a paired ``event_type=refusal`` workflow
event.
"""

from __future__ import annotations

from typing import Any

from .. import runtime
from ..audit import AuditEventTemplate, materialize, materialize_refusal
from ..repository import vouchers as vouchers_repo
from ..safety.controlled_status import (
    ALLOWED_VOUCHER_REVIEW_STATUSES,
    is_allowed_voucher_review_status,
    is_blocked_status,
    normalize,
)
from ..safety.refusal import (
    REASON_MISSING_REQUIRED_INPUT,
    REASON_PROHIBITED_ACTION,
    REASON_UNSUPPORTED_STATUS_VALUE,
    build,
)
from ._common import _description, not_implemented_response, with_boundary

TOOL_NAME = "set_voucher_review_status"

description = _description(
    "Update the voucher's internal review status. Allowed values: "
    "needs_review, in_review, awaiting_traveler_clarification, "
    "ready_for_human_decision, closed_in_demo. Values that imply official "
    "action (approved, denied, certified, submitted, paid, fraud) are "
    "refused. The status never represents an official DTS state."
)

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "voucher_id": {
            "type": "string",
            "description": "Synthetic voucher identifier.",
        },
        "status": {
            "type": "string",
            "enum": sorted(ALLOWED_VOUCHER_REVIEW_STATUSES),
            "description": "Controlled internal review status.",
        },
        "actor_label": {
            "type": "string",
            "description": "Demo identity (e.g. demo_ao_user_1).",
        },
    },
    "required": ["voucher_id", "status"],
    "additionalProperties": False,
}

_DEFAULT_ACTOR = "demo_ao_user_1"


def _persist_refusal(*, voucher_id: str | None, status: str, actor_label: str) -> dict[str, Any]:
    bundle = build(
        reason=REASON_PROHIBITED_ACTION,
        message=(
            "Voucher review status cannot be set to a blocked value. "
            "AO Radar does not approve, deny, certify, return, cancel, "
            "amend, submit, or otherwise take official action."
        ),
        tool_name=TOOL_NAME,
        target_kind="voucher",
        target_id=voucher_id,
        voucher_id=voucher_id,
        rejected_request={"voucher_id": voucher_id, "status": status},
    )
    response = bundle.response.to_dict()
    response.setdefault("tool", TOOL_NAME)

    if not runtime.is_db_available():
        return response

    try:
        with runtime.transaction() as conn:
            from ..repository import workflow_events as _wf

            audit_record = materialize_refusal(bundle.audit_template, actor_label=actor_label)
            _wf.insert(conn, event=audit_record.to_dict())
        response["audit_event_type"] = "refusal"
        response["audit_event_id"] = audit_record.event_id
    except Exception as exc:  # noqa: BLE001 - never let audit failure swallow refusal
        response["audit_event_error"] = exc.__class__.__name__
    return response


def handler(payload: dict[str, Any]) -> dict[str, Any]:
    voucher_id_raw = payload.get("voucher_id")
    voucher_id = (voucher_id_raw or "").strip() or None
    status_raw = (payload.get("status") or "").strip()
    actor_label = (payload.get("actor_label") or _DEFAULT_ACTOR).strip() or _DEFAULT_ACTOR

    if is_blocked_status(status_raw):
        return _persist_refusal(
            voucher_id=voucher_id,
            status=status_raw,
            actor_label=actor_label,
        )

    if status_raw and not is_allowed_voucher_review_status(status_raw):
        return build(
            reason=REASON_UNSUPPORTED_STATUS_VALUE,
            message=(
                "Voucher review status must be one of "
                f"{sorted(ALLOWED_VOUCHER_REVIEW_STATUSES)}."
            ),
            tool_name=TOOL_NAME,
            target_kind="voucher",
            target_id=voucher_id,
            voucher_id=voucher_id,
            rejected_request={"voucher_id": voucher_id, "status": status_raw},
        ).response.to_dict()

    if not runtime.is_db_available():
        return not_implemented_response(TOOL_NAME)

    if voucher_id is None:
        return build(
            reason=REASON_MISSING_REQUIRED_INPUT,
            message="set_voucher_review_status requires a synthetic voucher_id input.",
            tool_name=TOOL_NAME,
            target_kind="voucher",
            target_id=None,
            voucher_id=None,
            rejected_request=payload,
        ).response.to_dict()

    if not status_raw:
        return build(
            reason=REASON_MISSING_REQUIRED_INPUT,
            message="set_voucher_review_status requires a status input.",
            tool_name=TOOL_NAME,
            target_kind="voucher",
            target_id=voucher_id,
            voucher_id=voucher_id,
            rejected_request=payload,
        ).response.to_dict()

    new_status = normalize(status_raw)

    with runtime.transaction() as conn:
        audit_template = AuditEventTemplate(
            event_type="scoped_write",
            tool_name=TOOL_NAME,
            target_kind="voucher",
            target_id=voucher_id,
            voucher_id=voucher_id,
            actor_label=actor_label,
            rationale_metadata={"reason": "internal_review_status_update"},
            resulting_status=new_status,
        )
        audit_record = materialize(audit_template)
        updated = vouchers_repo.update_review_status(
            conn,
            voucher_id=voucher_id,
            new_status=new_status,
            audit_event=audit_record.to_dict(),
        )
        if updated is None:
            return with_boundary(
                {
                    "status": "not_found",
                    "tool": TOOL_NAME,
                    "voucher_id": voucher_id,
                    "message": "No synthetic voucher with this id is present in demo data.",
                }
            )

    return with_boundary(
        {
            "status": "ok",
            "tool": TOOL_NAME,
            "voucher_id": voucher_id,
            "review_status": updated.review_status,
            "audit_event_type": "scoped_write",
            "audit_event_id": audit_record.event_id,
        }
    )


__all__ = ["TOOL_NAME", "description", "INPUT_SCHEMA", "handler"]
