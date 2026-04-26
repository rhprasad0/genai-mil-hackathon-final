"""Counts within schema plan section 7.5 ranges."""

from __future__ import annotations

from ops.seed.generators.corpus import build_corpus
from ops.seed.validators.fk_and_volume import VOLUME_RANGES, validate_corpus


def test_volume_ranges() -> None:
    corpus = build_corpus()
    validate_corpus(corpus)
    counts = {
        "travelers": len(corpus.travelers),
        "vouchers": len(corpus.vouchers),
        "voucher_line_items": len(corpus.voucher_line_items),
        "evidence_refs": len(corpus.evidence_refs),
        "external_anomaly_signals": len(corpus.external_anomaly_signals),
        "story_findings": len(corpus.story_findings),
        "missing_information_items": len(corpus.missing_information_items),
        "review_briefs": len(corpus.review_briefs),
        "workflow_events": len(corpus.workflow_events),
    }
    for name, (lo, hi) in VOLUME_RANGES.items():
        actual = counts[name]
        assert lo <= actual <= hi, f"{name}={actual} not in [{lo}, {hi}]"


def test_every_ao_note_kind_seeded() -> None:
    corpus = build_corpus()
    kinds = {n["kind"] for n in corpus.ao_notes}
    assert kinds == {
        "ao_note",
        "draft_clarification",
        "synthetic_clarification_request",
        "ao_feedback",
    }
