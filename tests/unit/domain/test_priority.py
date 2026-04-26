"""Unit tests for ``ao_radar_mcp.domain.priority``.

Source of truth: docs/application-implementation-plan.md section 7 step D.
"""

from __future__ import annotations

from ao_radar_mcp.domain.priority import PriorityInputs, compute


def test_score_is_zero_for_clean_packet() -> None:
    score = compute(
        PriorityInputs(
            finding_counts_by_severity={},
            missing_information_count=0,
            signal_count=0,
            needs_human_review_count=0,
            is_partial=False,
        )
    )
    assert score.score == 0.0


def test_score_is_clamped_to_unit_interval() -> None:
    score = compute(
        PriorityInputs(
            finding_counts_by_severity={"high": 50, "medium": 50},
            missing_information_count=20,
            signal_count=20,
            needs_human_review_count=20,
            is_partial=True,
        )
    )
    assert 0.0 <= score.score <= 1.0
    assert score.score == 1.0


def test_score_increases_with_severity() -> None:
    low = compute(
        PriorityInputs(
            finding_counts_by_severity={"low": 1},
            missing_information_count=0,
            signal_count=0,
            needs_human_review_count=0,
        )
    )
    high = compute(
        PriorityInputs(
            finding_counts_by_severity={"high": 1},
            missing_information_count=0,
            signal_count=0,
            needs_human_review_count=0,
        )
    )
    assert high.score > low.score


def test_rationale_is_workload_only_language() -> None:
    score = compute(
        PriorityInputs(
            finding_counts_by_severity={"medium": 2},
            missing_information_count=1,
            signal_count=1,
            needs_human_review_count=0,
        )
    )
    rationale = score.rationale.lower()
    for forbidden in (
        "approval",
        "deny",
        "denied",
        "approve",
        "payable",
        "ready for payment",
        "certif",
        "fraud",
    ):
        # Allow only the negation-style sentence at the end.
        if forbidden in rationale:
            assert "not represent" in rationale or "does not" in rationale, (
                f"unexpected forbidden term {forbidden} in rationale: {rationale}"
            )
