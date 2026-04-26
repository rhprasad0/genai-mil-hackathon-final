"""Pure domain helpers for story coherence reasoning.

Sources of truth:
  - docs/spec.md FR-2 (Story Reconstruction), FR-4 (Coherence and Anomaly
    Checks).
  - docs/schema-implementation-plan.md sections 5.3 (line items), 5.4
    (evidence_refs), 5.8 (story_findings categories).

These helpers operate on plain dataclass-shaped inputs (line items + evidence
references + the declared trip window) and produce structured findings the
``analyze_voucher_story`` and ``prepare_ao_review_brief`` tools persist.
They contain no IO and no database calls so they are unit-testable without
Postgres.  They never produce official-disposition language; the brief
assembly layer wraps them with the canonical boundary reminder.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass(frozen=True)
class TripWindow:
    """Declared trip window for a synthetic voucher."""

    voucher_id: str
    trip_start: date
    trip_end: date

    def contains(self, expense_date: date | None) -> bool:
        if expense_date is None:
            return False
        return self.trip_start <= expense_date <= self.trip_end


@dataclass(frozen=True)
class LineItemSnapshot:
    """Subset of ``voucher_line_items`` columns the analyzer needs."""

    line_item_id: str
    line_index: int
    expense_date: date | None
    amount_minor_units: int
    currency_code: str
    category: str
    vendor_label: str


@dataclass(frozen=True)
class EvidenceSnapshot:
    """Subset of ``evidence_refs`` columns the analyzer needs."""

    evidence_ref_id: str
    line_item_id: str | None
    content_type_indicator: str
    legibility_cue: str
    itemization_cue: str
    payment_evidence_cue: str
    vendor_label_on_evidence: str | None
    evidence_date_on_face: date | None
    amount_on_face_minor_units: int | None
    currency_code_on_face: str | None


@dataclass(frozen=True)
class StoryFindingDraft:
    """Domain-shaped finding draft (no IDs, no audit fields).

    The repository assigns IDs and audit metadata when persisting.
    """

    category: str
    severity: str
    summary: str
    explanation: str
    suggested_question: str
    packet_evidence_pointer: dict[str, Any]
    confidence: str
    needs_human_review: bool
    contributing_evidence_ids: tuple[str, ...] = field(default_factory=tuple)
    review_prompt_only: bool = True


@dataclass(frozen=True)
class StoryAnalysisResult:
    """Aggregated output of the analyzer."""

    voucher_id: str
    findings: tuple[StoryFindingDraft, ...]
    review_prompt_only: bool = True


def detect_out_of_window_expenses(
    window: TripWindow,
    line_items: tuple[LineItemSnapshot, ...],
) -> tuple[StoryFindingDraft, ...]:
    """Flag line items whose ``expense_date`` falls outside the trip window."""

    findings: list[StoryFindingDraft] = []
    for item in line_items:
        if item.expense_date is None:
            continue
        if window.contains(item.expense_date):
            continue
        findings.append(
            StoryFindingDraft(
                category="date_window_mismatch",
                severity="medium",
                summary=(
                    f"Line {item.line_index} expense_date {item.expense_date.isoformat()} "
                    f"is outside the declared trip window "
                    f"{window.trip_start.isoformat()}–{window.trip_end.isoformat()}."
                ),
                explanation=(
                    "The expense date does not fall inside the declared trip "
                    "window. This is a review prompt only; reviewer should "
                    "verify the date or the trip window with the traveler."
                ),
                suggested_question=(
                    "Could the traveler clarify why this expense date sits "
                    "outside the declared trip window?"
                ),
                packet_evidence_pointer={
                    "line_item_id": item.line_item_id,
                    "excerpt_hint": "expense_date outside trip_window",
                },
                confidence="medium",
                needs_human_review=False,
            )
        )
    return tuple(findings)


def detect_amount_mismatches(
    line_items: tuple[LineItemSnapshot, ...],
    evidence: tuple[EvidenceSnapshot, ...],
) -> tuple[StoryFindingDraft, ...]:
    """Flag amount mismatches between line items and their evidence."""

    by_line: dict[str, list[EvidenceSnapshot]] = {}
    for ev in evidence:
        if ev.line_item_id is None:
            continue
        by_line.setdefault(ev.line_item_id, []).append(ev)

    findings: list[StoryFindingDraft] = []
    for item in line_items:
        rows = by_line.get(item.line_item_id, [])
        for ev in rows:
            if ev.amount_on_face_minor_units is None:
                continue
            if ev.amount_on_face_minor_units == item.amount_minor_units:
                continue
            findings.append(
                StoryFindingDraft(
                    category="amount_mismatch",
                    severity="medium",
                    summary=(
                        f"Line {item.line_index} claimed amount "
                        f"{item.amount_minor_units} {item.currency_code} differs "
                        f"from evidence amount "
                        f"{ev.amount_on_face_minor_units} "
                        f"{ev.currency_code_on_face or item.currency_code}."
                    ),
                    explanation=(
                        "The amount on the line item does not match the amount "
                        "shown on the attached evidence. Review prompt only; "
                        "reviewer should reconcile with the traveler."
                    ),
                    suggested_question=(
                        "Could the traveler clarify why the line item amount "
                        "and the receipt amount do not match?"
                    ),
                    packet_evidence_pointer={
                        "line_item_id": item.line_item_id,
                        "evidence_ref_id": ev.evidence_ref_id,
                        "excerpt_hint": "amount_on_face vs amount_minor_units",
                    },
                    confidence="medium",
                    needs_human_review=False,
                    contributing_evidence_ids=(ev.evidence_ref_id,),
                )
            )
    return tuple(findings)


def detect_evidence_quality_concerns(
    evidence: tuple[EvidenceSnapshot, ...],
) -> tuple[StoryFindingDraft, ...]:
    """Flag rows whose cue columns suggest weak/unreadable evidence."""

    findings: list[StoryFindingDraft] = []
    for ev in evidence:
        if ev.content_type_indicator == "none_attached_demo":
            findings.append(
                StoryFindingDraft(
                    category="missing_receipt",
                    severity="high",
                    summary=(
                        "No receipt is attached for the related line item or "
                        "packet-level expectation."
                    ),
                    explanation=(
                        "The evidence row is marked none_attached_demo. Review "
                        "prompt only; reviewer should ask the traveler to "
                        "supply the missing receipt."
                    ),
                    suggested_question=(
                        "Could the traveler provide the receipt for this expense?"
                    ),
                    packet_evidence_pointer={
                        "evidence_ref_id": ev.evidence_ref_id,
                        "line_item_id": ev.line_item_id,
                        "excerpt_hint": "none_attached_demo",
                    },
                    confidence="high",
                    needs_human_review=False,
                )
            )
            continue
        if ev.legibility_cue == "poor" or ev.itemization_cue == "not_itemized":
            findings.append(
                StoryFindingDraft(
                    category="evidence_quality_concern",
                    severity="medium",
                    summary=(
                        "Attached evidence has weak legibility / itemization cues; "
                        "a reviewer should confirm the line item before "
                        "taking any official action."
                    ),
                    explanation=(
                        "The legibility and/or itemization cue indicate the "
                        "attached evidence is hard to read or not itemized. "
                        "Review prompt only."
                    ),
                    suggested_question=(
                        "Could the traveler provide a clearer / itemized receipt "
                        "for this expense?"
                    ),
                    packet_evidence_pointer={
                        "evidence_ref_id": ev.evidence_ref_id,
                        "line_item_id": ev.line_item_id,
                        "excerpt_hint": "weak legibility or itemization",
                    },
                    confidence="medium",
                    needs_human_review=False,
                )
            )
    return tuple(findings)


def analyze(
    voucher_id: str,
    window: TripWindow,
    line_items: tuple[LineItemSnapshot, ...],
    evidence: tuple[EvidenceSnapshot, ...],
) -> StoryAnalysisResult:
    """Compose the helpers above into a single analysis result."""

    findings: list[StoryFindingDraft] = []
    findings.extend(detect_out_of_window_expenses(window, line_items))
    findings.extend(detect_amount_mismatches(line_items, evidence))
    findings.extend(detect_evidence_quality_concerns(evidence))
    return StoryAnalysisResult(
        voucher_id=voucher_id,
        findings=tuple(findings),
        review_prompt_only=True,
    )


__all__ = [
    "EvidenceSnapshot",
    "LineItemSnapshot",
    "StoryAnalysisResult",
    "StoryFindingDraft",
    "TripWindow",
    "analyze",
    "detect_amount_mismatches",
    "detect_evidence_quality_concerns",
    "detect_out_of_window_expenses",
]
