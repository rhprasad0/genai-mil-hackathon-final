"""Pure brief assembly helpers.

Sources of truth:
  - docs/spec.md FR-14, FR-7, AC-1, AC-4, AC-5, AC-12.
  - docs/schema-implementation-plan.md section 5.10 (review_briefs columns).

The helpers fuse repository-shaped inputs into the ``review_briefs`` shape.
They are pure: no IO, no database calls.  The application layer persists
the resulting draft and writes the paired ``event_type=generation`` audit
row in the same transaction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..safety.refusal import get_boundary_reminder


@dataclass(frozen=True)
class BriefInputs:
    """Bounded set of inputs the brief assembler consumes."""

    voucher_id: str
    finding_ids: tuple[str, ...]
    missing_information_ids: tuple[str, ...]
    signal_ids: tuple[str, ...]
    citation_ids: tuple[str, ...]
    priority_score: float
    priority_rationale: str
    suggested_focus: str
    evidence_gap_summary: str
    story_coherence_summary: str
    draft_clarification_note: str
    brief_uncertainty: str
    is_partial: bool = False
    partial_reason: str | None = None


@dataclass(frozen=True)
class ReviewBriefDraft:
    """Domain-shaped review brief (no brief_id, no version)."""

    voucher_id: str
    priority_score: float
    priority_rationale: str
    suggested_focus: str
    evidence_gap_summary: str
    story_coherence_summary: str
    draft_clarification_note: str
    policy_hooks: tuple[str, ...]
    signal_hooks: tuple[str, ...]
    finding_hooks: tuple[str, ...]
    missing_information_hooks: tuple[str, ...]
    brief_uncertainty: str
    human_authority_boundary_text: str
    is_partial: bool
    partial_reason: str | None
    boundary_reminder: str = field(default_factory=get_boundary_reminder)


def assemble(inputs: BriefInputs) -> ReviewBriefDraft:
    """Fuse the inputs into the canonical brief shape."""

    if inputs.brief_uncertainty not in {"low", "medium", "high"}:
        raise ValueError(
            f"brief_uncertainty must be low|medium|high; got {inputs.brief_uncertainty!r}"
        )
    return ReviewBriefDraft(
        voucher_id=inputs.voucher_id,
        priority_score=float(inputs.priority_score),
        priority_rationale=inputs.priority_rationale,
        suggested_focus=inputs.suggested_focus,
        evidence_gap_summary=inputs.evidence_gap_summary,
        story_coherence_summary=inputs.story_coherence_summary,
        draft_clarification_note=inputs.draft_clarification_note,
        policy_hooks=tuple(inputs.citation_ids),
        signal_hooks=tuple(inputs.signal_ids),
        finding_hooks=tuple(inputs.finding_ids),
        missing_information_hooks=tuple(inputs.missing_information_ids),
        brief_uncertainty=inputs.brief_uncertainty,
        human_authority_boundary_text=get_boundary_reminder(),
        is_partial=inputs.is_partial,
        partial_reason=inputs.partial_reason,
    )


def render_markdown(draft: ReviewBriefDraft) -> str:
    """Produce a stable markdown export for ``export_review_brief``."""

    lines: list[str] = [
        f"# AO Radar Review Brief — {draft.voucher_id}",
        "",
        f"**Priority (workload-only):** {draft.priority_score:.4f}",
        "",
        f"**Suggested focus:** {draft.suggested_focus}",
        "",
        "## Evidence and story coherence",
        "",
        f"- Evidence gap summary: {draft.evidence_gap_summary}",
        f"- Story coherence summary: {draft.story_coherence_summary}",
        "",
        "## Draft clarification note (non-official)",
        "",
        draft.draft_clarification_note,
        "",
        "## Hooks",
        "",
        f"- policy_hooks: {list(draft.policy_hooks)}",
        f"- signal_hooks: {list(draft.signal_hooks)}",
        f"- finding_hooks: {list(draft.finding_hooks)}",
        f"- missing_information_hooks: {list(draft.missing_information_hooks)}",
        "",
        f"**Brief uncertainty:** {draft.brief_uncertainty}",
        "",
        "## Human-authority boundary",
        "",
        draft.human_authority_boundary_text,
    ]
    if draft.is_partial:
        lines += [
            "",
            f"**Partial brief:** {draft.partial_reason or 'unspecified'}",
        ]
    return "\n".join(lines)


def render_json(draft: ReviewBriefDraft) -> dict[str, Any]:
    """Produce a JSON export for ``export_review_brief``."""

    return {
        "voucher_id": draft.voucher_id,
        "priority_score": draft.priority_score,
        "priority_rationale": draft.priority_rationale,
        "suggested_focus": draft.suggested_focus,
        "evidence_gap_summary": draft.evidence_gap_summary,
        "story_coherence_summary": draft.story_coherence_summary,
        "draft_clarification_note": draft.draft_clarification_note,
        "policy_hooks": list(draft.policy_hooks),
        "signal_hooks": list(draft.signal_hooks),
        "finding_hooks": list(draft.finding_hooks),
        "missing_information_hooks": list(draft.missing_information_hooks),
        "brief_uncertainty": draft.brief_uncertainty,
        "human_authority_boundary_text": draft.human_authority_boundary_text,
        "is_partial": draft.is_partial,
        "partial_reason": draft.partial_reason,
    }


__all__ = [
    "BriefInputs",
    "ReviewBriefDraft",
    "assemble",
    "render_json",
    "render_markdown",
]
