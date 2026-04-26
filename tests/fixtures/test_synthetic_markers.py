"""Run the synthetic-marker validator on the in-memory generator output."""

from __future__ import annotations

from ops.seed.generators.corpus import build_corpus
from ops.seed.validators.synthetic_markers import (
    SyntheticMarkerError,
    validate_corpus,
)


def test_synthetic_markers_pass_on_seed() -> None:
    corpus = build_corpus()
    validate_corpus(corpus)


def test_synthetic_markers_reject_missing_marker() -> None:
    corpus = build_corpus()
    bad = dict(corpus.travelers[0])
    bad["display_name"] = "Real Name Without Marker"
    corpus.travelers[0] = bad
    try:
        validate_corpus(corpus)
    except SyntheticMarkerError:
        return
    raise AssertionError("validator should reject missing synthetic marker")


def test_synthetic_markers_reject_loa_format() -> None:
    corpus = build_corpus()
    bad = dict(corpus.vouchers[0])
    bad["funding_reference_label"] = "LOA-PROD-FY26-9999"
    corpus.vouchers[0] = bad
    try:
        validate_corpus(corpus)
    except SyntheticMarkerError:
        return
    raise AssertionError("validator should reject non-DEMO LOA")
