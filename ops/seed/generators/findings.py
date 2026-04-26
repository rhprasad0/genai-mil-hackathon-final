"""Story-finding, missing-information, and finding-signal-link row builders."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ops.seed.generators.cards import StoryCard
from ops.seed.generators.determinism import derive_timestamp
from ops.seed.generators.signals import signal_id_for_finding_link
from ops.seed.generators.vouchers import build_packet_evidence_pointer_json


def finding_id_for(voucher_id: str, ordinal: int) -> str:
    return f"{voucher_id}-FND-{ordinal:02d}"


def missing_item_id_for(voucher_id: str, ordinal: int) -> str:
    return f"{voucher_id}-MI-{ordinal:02d}"


def build_finding_rows(card: StoryCard) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    base = card.voucher.demo_packet_submitted_at
    if isinstance(base, datetime) and base.tzinfo is None:
        base = base.replace(tzinfo=timezone.utc)
    for idx, finding in enumerate(card.findings, start=1):
        finding_id = finding_id_for(card.voucher_id, idx)
        rows.append(
            {
                "finding_id": finding_id,
                "voucher_id": card.voucher_id,
                "category": finding.category,
                "severity": finding.severity,
                "summary": finding.summary,
                "explanation": finding.explanation,
                "suggested_question": finding.suggested_question,
                "packet_evidence_pointer": build_packet_evidence_pointer_json(card, idx - 1),
                "primary_citation_id": finding.primary_citation_id,
                "confidence": finding.confidence,
                "needs_human_review": finding.needs_human_review,
                "review_state": "open",
                "created_at": derive_timestamp(base, offset_minutes=20 + idx),
            }
        )
    return rows


def build_missing_item_rows(card: StoryCard) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    base = card.voucher.demo_packet_submitted_at
    if isinstance(base, datetime) and base.tzinfo is None:
        base = base.replace(tzinfo=timezone.utc)
    for idx, mi in enumerate(card.missing_information_items, start=1):
        linked_line_item_id = (
            f"{card.voucher_id}-LI-{mi.linked_line_index}"
            if mi.linked_line_index is not None
            else None
        )
        rows.append(
            {
                "missing_item_id": missing_item_id_for(card.voucher_id, idx),
                "voucher_id": card.voucher_id,
                "description": mi.description,
                "why_it_matters": mi.why_it_matters,
                "expected_location_hint": mi.expected_location_hint,
                "linked_line_item_id": linked_line_item_id,
                "created_at": derive_timestamp(base, offset_minutes=40 + idx),
            }
        )
    return rows


def build_finding_signal_link_rows(
    card: StoryCard,
    finding_rows: list[dict[str, Any]],
    signal_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    base = card.voucher.demo_packet_submitted_at
    if isinstance(base, datetime) and base.tzinfo is None:
        base = base.replace(tzinfo=timezone.utc)
    finding_ids_by_index = {idx: finding_rows[idx]["finding_id"] for idx in range(len(finding_rows))}
    seen: set[tuple[str, str]] = set()
    for idx, finding in enumerate(card.findings):
        for signal_type in finding.signal_links:
            signal_id = signal_id_for_finding_link(card, signal_type, signal_rows)
            if signal_id is None:
                raise ValueError(
                    f"{card.voucher_id} finding[{idx}] references signal_type={signal_type} "
                    f"with no matching signal row"
                )
            pair = (finding_ids_by_index[idx], signal_id)
            if pair in seen:
                continue
            seen.add(pair)
            rows.append(
                {
                    "finding_id": pair[0],
                    "signal_id": pair[1],
                    "created_at": derive_timestamp(base, offset_minutes=60 + len(rows)),
                }
            )
    return rows


__all__ = [
    "finding_id_for",
    "missing_item_id_for",
    "build_finding_rows",
    "build_missing_item_rows",
    "build_finding_signal_link_rows",
]
