"""V-1011 brief has is_partial=True."""

from __future__ import annotations

from ops.seed.generators.corpus import build_corpus


def test_v_1011_brief_is_partial() -> None:
    corpus = build_corpus()
    target = next(b for b in corpus.review_briefs if b["voucher_id"] == "V-1011")
    assert target["is_partial"] is True
    assert target["partial_reason"]


def test_only_v_1011_is_partial_at_seed() -> None:
    corpus = build_corpus()
    partial_voucher_ids = {b["voucher_id"] for b in corpus.review_briefs if b["is_partial"]}
    assert partial_voucher_ids == {"V-1011"}
