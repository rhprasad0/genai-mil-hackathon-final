"""Both refusal seeds present in generator output."""

from __future__ import annotations

from ops.seed.generators.corpus import build_corpus


def test_two_refusals_present() -> None:
    corpus = build_corpus()
    refusals = [ev for ev in corpus.workflow_events if ev["event_type"] == "refusal"]
    keys = {(ev["voucher_id"], ev["tool_name"]) for ev in refusals}
    assert ("V-1001", "set_voucher_review_status") in keys
    assert ("V-1010", "prepare_ao_review_brief") in keys


def test_refusal_rationale_metadata_includes_rejected_input() -> None:
    corpus = build_corpus()
    refusals = [ev for ev in corpus.workflow_events if ev["event_type"] == "refusal"]
    for ev in refusals:
        meta = ev["rationale_metadata"]
        assert "rejected_input" in meta
        assert isinstance(meta["rejected_input"], str)
        assert "rationale" in meta
        assert "refusal_reason" in meta


def test_refusal_resulting_status_is_null() -> None:
    """A refusal is not a status update; resulting_status stays None."""
    corpus = build_corpus()
    for ev in corpus.workflow_events:
        if ev["event_type"] == "refusal":
            assert ev["resulting_status"] is None
