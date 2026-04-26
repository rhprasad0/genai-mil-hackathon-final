"""Composite review-priority scoring for queue prioritization.

Sources of truth:
  - docs/spec.md FR-9 (Queue Prioritization), AC-8.
  - docs/schema-implementation-plan.md section 5.10 (review_briefs.priority_*).

The score is workload guidance only.  It deliberately excludes any signal
that would imply approval, denial, payment readiness, or entitlement.  Inputs
are integer counts and a string severity bucket; the output is a normalized
0–1 float plus a neutral rationale string the brief assembly layer renders.
"""

from __future__ import annotations

from dataclasses import dataclass


SEVERITY_WEIGHT: dict[str, float] = {
    "info": 0.05,
    "low": 0.1,
    "medium": 0.2,
    "high": 0.35,
}


@dataclass(frozen=True)
class PriorityInputs:
    """Bounded set of inputs the priority helper consumes."""

    finding_counts_by_severity: dict[str, int]
    missing_information_count: int
    signal_count: int
    needs_human_review_count: int
    is_partial: bool = False


@dataclass(frozen=True)
class PriorityScore:
    """Workload-only priority score."""

    score: float
    rationale: str


def compute(inputs: PriorityInputs) -> PriorityScore:
    """Return a workload-only score in [0, 1] plus a neutral rationale."""

    base = 0.0
    for severity, count in inputs.finding_counts_by_severity.items():
        weight = SEVERITY_WEIGHT.get(severity.lower(), 0.0)
        base += weight * max(0, count)
    base += 0.08 * max(0, inputs.missing_information_count)
    base += 0.04 * max(0, inputs.signal_count)
    base += 0.05 * max(0, inputs.needs_human_review_count)
    if inputs.is_partial:
        base += 0.05
    score = max(0.0, min(1.0, base))

    rationale = (
        "Workload-only score. Higher means more reviewer attention is likely "
        "needed because of finding count and severity, missing-information "
        "items, signals to consider, needs-human-review items, and partial "
        "brief state. The score does not represent approval, denial, "
        "payability, or readiness for payment."
    )
    return PriorityScore(score=round(score, 4), rationale=rationale)


__all__ = ["PriorityInputs", "PriorityScore", "SEVERITY_WEIGHT", "compute"]
