"""Review-brief and AO-note row builders."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ops.seed.constants import (
    DEMO_AO_ACTOR_LABEL,
    HUMAN_AUTHORITY_BOUNDARY_TEXT,
)
from ops.seed.generators.cards import StoryCard
from ops.seed.generators.determinism import derive_id, derive_timestamp


def brief_id_for(voucher_id: str, version: int) -> str:
    return f"BRIEF-{voucher_id}-v{version:02d}-{derive_id('brief', voucher_id, str(version))[:8]}"


def note_id_for(voucher_id: str, ordinal: int, kind: str) -> str:
    return f"NOTE-{voucher_id}-{ordinal:02d}-{kind[:6]}"


def build_brief_row(card: StoryCard) -> dict[str, Any]:
    base = card.voucher.demo_packet_submitted_at
    if isinstance(base, datetime) and base.tzinfo is None:
        base = base.replace(tzinfo=timezone.utc)
    generated_at = derive_timestamp(base, offset_minutes=120)
    finding_hooks = [
        f"{card.voucher_id}-FND-{idx:02d}" for idx in range(1, len(card.findings) + 1)
    ]
    missing_hooks = [
        f"{card.voucher_id}-MI-{idx:02d}"
        for idx in range(1, len(card.missing_information_items) + 1)
    ]
    # Resolve policy + signal hooks deterministically from the card's required
    # citations and the actual signal rows for the voucher.
    policy_hooks = sorted(
        {
            f.primary_citation_id
            for f in card.findings
            if f.primary_citation_id is not None
        }
    )
    signal_hooks: list[str] = []
    for signal in card.external_anomaly_signals:
        from ops.seed.generators.signals import build_signal_id, build_signal_key

        signal_hooks.append(
            build_signal_id(card.voucher_id, build_signal_key(signal, _signal_ordinal(card, signal)))
        )
    return {
        "brief_id": brief_id_for(card.voucher_id, 1),
        "voucher_id": card.voucher_id,
        "version": 1,
        "generated_at": generated_at,
        "priority_score": float(card.brief.priority_score),
        "priority_rationale": card.brief.priority_rationale,
        "suggested_focus": card.brief.suggested_focus,
        "evidence_gap_summary": card.brief.evidence_gap_summary,
        "story_coherence_summary": card.brief.story_coherence_summary,
        "draft_clarification_note": card.brief.draft_clarification_note,
        "policy_hooks": policy_hooks,
        "signal_hooks": signal_hooks,
        "finding_hooks": finding_hooks,
        "missing_information_hooks": missing_hooks,
        "brief_uncertainty": card.brief.brief_uncertainty,
        "human_authority_boundary_text": HUMAN_AUTHORITY_BOUNDARY_TEXT,
        "is_partial": card.brief.is_partial,
        "partial_reason": card.brief.partial_reason,
    }


def _signal_ordinal(card: StoryCard, signal_target: Any) -> int:
    """Recompute the ordinal so build_brief_row can derive signal_ids without
    re-walking ``signals.py``.
    """

    counter: dict[tuple[str, str], int] = {}
    for s in card.external_anomaly_signals:
        key = (s.signal_type, s.scenario_slug)
        counter[key] = counter.get(key, 0) + 1
        if s is signal_target:
            return counter[key]
    return 1


def build_ao_note_rows(card: StoryCard) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    base = card.voucher.demo_packet_submitted_at
    if isinstance(base, datetime) and base.tzinfo is None:
        base = base.replace(tzinfo=timezone.utc)
    for idx, note in enumerate(card.ao_notes, start=1):
        finding_id = None
        if note.finding_index is not None:
            finding_id = f"{card.voucher_id}-FND-{note.finding_index:02d}"
        rows.append(
            {
                "note_id": note_id_for(card.voucher_id, idx, note.kind),
                "voucher_id": card.voucher_id,
                "finding_id": finding_id,
                "kind": note.kind,
                "body": note.body,
                "actor_label": DEMO_AO_ACTOR_LABEL,
                "created_at": derive_timestamp(base, offset_minutes=140 + idx),
                "superseded_by_note_id": None,
            }
        )
    return rows


__all__ = [
    "brief_id_for",
    "note_id_for",
    "build_brief_row",
    "build_ao_note_rows",
]
