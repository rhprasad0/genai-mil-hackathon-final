"""Build voucher, line-item, and evidence rows from story cards."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from ops.seed.constants import DATA_ENVIRONMENT
from ops.seed.generators.cards import StoryCard
from ops.seed.generators.determinism import derive_timestamp


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def line_item_id_for(card: StoryCard, line_index: int) -> str:
    return f"{card.voucher_id}-LI-{line_index}"


def evidence_ref_id_for(card: StoryCard, line_index: int, evidence_index: int) -> str:
    return f"{card.voucher_id}-LI-{line_index}-EV-{evidence_index}"


def build_voucher_row(card: StoryCard) -> dict[str, Any]:
    v = card.voucher
    submitted = _ensure_utc(v.demo_packet_submitted_at)
    created_at = derive_timestamp(v.trip_start_date, offset_minutes=0)
    updated_at = submitted
    return {
        "voucher_id": card.voucher_id,
        "traveler_id": card.traveler_id,
        "trip_purpose_category": v.trip_purpose_category,
        "trip_start_date": v.trip_start_date,
        "trip_end_date": v.trip_end_date,
        "declared_origin": v.declared_origin,
        "declared_destinations": list(v.declared_destinations),
        "funding_reference_label": v.funding_reference_label,
        "funding_reference_quality": v.funding_reference_quality,
        "justification_text": v.justification_text,
        "pre_existing_flags": list(v.pre_existing_flags),
        "demo_packet_submitted_at": submitted,
        "review_status": v.review_status,
        "data_environment": DATA_ENVIRONMENT,
        "created_at": created_at,
        "updated_at": updated_at,
    }


def build_line_item_rows(card: StoryCard) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for li in card.line_items:
        # Default claimed_by_traveler_at to packet submission unless card overrides.
        claimed_at = (
            _ensure_utc(li.claimed_by_traveler_at)
            if li.claimed_by_traveler_at is not None
            else _ensure_utc(card.voucher.demo_packet_submitted_at)
        )
        rows.append(
            {
                "line_item_id": line_item_id_for(card, li.line_index),
                "voucher_id": card.voucher_id,
                "line_index": li.line_index,
                "expense_date": li.expense_date,
                "amount_minor_units": li.amount_minor_units,
                "currency_code": li.currency_code,
                "exchange_rate_to_usd": li.exchange_rate_to_usd,
                "category": li.category,
                "vendor_label": li.vendor_label,
                "payment_instrument_indicator": li.payment_instrument_indicator,
                "free_text_notes": li.free_text_notes or "",
                "claimed_by_traveler_at": claimed_at,
            }
        )
    return rows


def build_evidence_rows(card: StoryCard) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for li in card.line_items:
        for idx, ev in enumerate(li.evidence_refs, start=1):
            rows.append(
                {
                    "evidence_ref_id": evidence_ref_id_for(card, li.line_index, idx),
                    "voucher_id": card.voucher_id,
                    "line_item_id": line_item_id_for(card, li.line_index),
                    "packet_level_role": ev.packet_level_role,
                    "content_type_indicator": ev.content_type_indicator,
                    "legibility_cue": ev.legibility_cue,
                    "itemization_cue": ev.itemization_cue,
                    "payment_evidence_cue": ev.payment_evidence_cue,
                    "vendor_label_on_evidence": ev.vendor_label_on_evidence,
                    "evidence_date_on_face": ev.evidence_date_on_face,
                    "amount_on_face_minor_units": ev.amount_on_face_minor_units,
                    "currency_code_on_face": ev.currency_code_on_face,
                    "notes": ev.notes or "",
                }
            )
    return rows


def build_packet_evidence_pointer_json(
    card: StoryCard, finding_index: int
) -> dict[str, Any]:
    finding = card.findings[finding_index]
    pointer = finding.packet_evidence_pointer
    out: dict[str, Any] = {"excerpt_hint": pointer.excerpt_hint}
    if pointer.line_item_id:
        out["line_item_id"] = pointer.line_item_id
    if pointer.evidence_ref_id:
        out["evidence_ref_id"] = pointer.evidence_ref_id
    return out


def jsonify(value: Any) -> str:
    """Stable JSON for logging or snapshot use."""

    return json.dumps(value, sort_keys=True, default=str)


__all__ = [
    "line_item_id_for",
    "evidence_ref_id_for",
    "build_voucher_row",
    "build_line_item_rows",
    "build_evidence_rows",
    "build_packet_evidence_pointer_json",
    "jsonify",
]
