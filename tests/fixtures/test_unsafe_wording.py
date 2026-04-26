"""Fixture validator on generated narrative."""

from __future__ import annotations

from ops.seed.generators.corpus import build_corpus
from ops.seed.validators.unsafe_wording import (
    UnsafeWordingError,
    validate_corpus,
)


def test_unsafe_wording_pass_on_seed() -> None:
    corpus = build_corpus()
    validate_corpus(corpus)


def test_unsafe_wording_reject_official_disposition() -> None:
    corpus = build_corpus()
    target = dict(corpus.review_briefs[0])
    target["draft_clarification_note"] = "This voucher is approved for payment."
    corpus.review_briefs[0] = target
    try:
        validate_corpus(corpus)
    except UnsafeWordingError:
        return
    raise AssertionError("validator should reject affirmative approval wording")


def test_unsafe_wording_reject_fraud_allegation() -> None:
    corpus = build_corpus()
    target = dict(corpus.story_findings[0])
    target["explanation"] = "This line is fraudulent and the traveler committed fraud."
    corpus.story_findings[0] = target
    try:
        validate_corpus(corpus)
    except UnsafeWordingError:
        return
    raise AssertionError("validator should reject fraud allegation wording")


def test_unsafe_wording_allows_negative_boundary_text() -> None:
    """Sanity: the canonical boundary text inside review_briefs must pass."""
    corpus = build_corpus()
    # The brief's draft_clarification_note must already use neutral vocabulary.
    validate_corpus(corpus)
