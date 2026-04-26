"""``get_voucher_packet`` tool module.

Spec reference: docs/spec.md section 4.5.1.  Returns the synthetic voucher
packet shape (declared trip, line items, evidence references, justification,
funding label, pre-existing flags, current internal review status).
"""

from __future__ import annotations

from typing import Any

from .. import runtime
from ..repository import (
    evidence as evidence_repo,
)
from ..repository import (
    line_items as line_items_repo,
)
from ..repository import (
    missing_information as missing_repo,
)
from ..repository import (
    vouchers as vouchers_repo,
)
from ..safety.refusal import REASON_MISSING_REQUIRED_INPUT, build
from ._common import _description, not_implemented_response, with_boundary

TOOL_NAME = "get_voucher_packet"

description = _description(
    "Return the synthetic voucher packet for a voucher_id (declared trip, "
    "line items, evidence references, justification, funding/LOA label, "
    "pre-existing flags, internal review status)."
)

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "voucher_id": {
            "type": "string",
            "description": "Synthetic voucher identifier (e.g. V-1003).",
        },
    },
    "required": ["voucher_id"],
    "additionalProperties": False,
}


def _line_item_payload(row: Any) -> dict[str, Any]:
    return {
        "line_item_id": row.line_item_id,
        "line_index": row.line_index,
        "expense_date": row.expense_date.isoformat(),
        "amount_minor_units": row.amount_minor_units,
        "currency_code": row.currency_code,
        "exchange_rate_to_usd": row.exchange_rate_to_usd,
        "category": row.category,
        "vendor_label": row.vendor_label,
        "payment_instrument_indicator": row.payment_instrument_indicator,
        "free_text_notes": row.free_text_notes,
    }


def _evidence_payload(row: Any) -> dict[str, Any]:
    return {
        "evidence_ref_id": row.evidence_ref_id,
        "line_item_id": row.line_item_id,
        "packet_level_role": row.packet_level_role,
        "content_type_indicator": row.content_type_indicator,
        "legibility_cue": row.legibility_cue,
        "itemization_cue": row.itemization_cue,
        "payment_evidence_cue": row.payment_evidence_cue,
        "vendor_label_on_evidence": row.vendor_label_on_evidence,
        "evidence_date_on_face": (
            row.evidence_date_on_face.isoformat() if row.evidence_date_on_face else None
        ),
        "amount_on_face_minor_units": row.amount_on_face_minor_units,
        "currency_code_on_face": row.currency_code_on_face,
        "notes": row.notes,
    }


def _missing_payload(row: Any) -> dict[str, Any]:
    return {
        "missing_item_id": row.missing_item_id,
        "description": row.description,
        "why_it_matters": row.why_it_matters,
        "expected_location_hint": row.expected_location_hint,
        "linked_line_item_id": row.linked_line_item_id,
    }


def handler(payload: dict[str, Any]) -> dict[str, Any]:
    voucher_id = (payload.get("voucher_id") or "").strip()

    if not runtime.is_db_available():
        return not_implemented_response(TOOL_NAME)

    if not voucher_id:
        return build(
            reason=REASON_MISSING_REQUIRED_INPUT,
            message="get_voucher_packet requires a synthetic voucher_id input.",
            tool_name=TOOL_NAME,
            target_kind="voucher",
            target_id=None,
            voucher_id=None,
            rejected_request=payload,
        ).response.to_dict()

    with runtime.transaction() as conn:
        voucher = vouchers_repo.get_by_id(conn, voucher_id)
        if voucher is None:
            return with_boundary(
                {
                    "status": "not_found",
                    "tool": TOOL_NAME,
                    "voucher_id": voucher_id,
                    "message": "No synthetic voucher with this id is present in demo data.",
                }
            )
        line_items = line_items_repo.list_for_voucher(conn, voucher_id)
        evidence = evidence_repo.list_for_voucher(conn, voucher_id)
        missing = missing_repo.list_for_voucher(conn, voucher_id)

    return with_boundary(
        {
            "status": "ok",
            "tool": TOOL_NAME,
            "voucher": {
                "voucher_id": voucher.voucher_id,
                "traveler_id": voucher.traveler_id,
                "trip_purpose_category": voucher.trip_purpose_category,
                "trip_start_date": voucher.trip_start_date.isoformat(),
                "trip_end_date": voucher.trip_end_date.isoformat(),
                "declared_origin": voucher.declared_origin,
                "declared_destinations": list(voucher.declared_destinations),
                "funding_reference_label": voucher.funding_reference_label,
                "funding_reference_quality": voucher.funding_reference_quality,
                "justification_text": voucher.justification_text,
                "pre_existing_flags": list(voucher.pre_existing_flags),
                "demo_packet_submitted_at": voucher.demo_packet_submitted_at.isoformat(),
                "review_status": voucher.review_status,
                "data_environment": voucher.data_environment,
            },
            "line_items": [_line_item_payload(row) for row in line_items],
            "evidence_refs": [_evidence_payload(row) for row in evidence],
            "missing_information_items": [_missing_payload(row) for row in missing],
            "review_prompt_only": True,
        }
    )


__all__ = ["TOOL_NAME", "description", "INPUT_SCHEMA", "handler"]
