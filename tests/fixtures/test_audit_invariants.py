"""Generator-side: every required workflow_event present."""

from __future__ import annotations

from ops.seed.generators.corpus import build_corpus
from ops.seed.validators.audit_invariants import (
    AuditInvariantError,
    validate_corpus,
)


def test_audit_invariants_pass() -> None:
    corpus = build_corpus()
    validate_corpus(corpus)


def test_every_seeded_brief_has_generation_event() -> None:
    corpus = build_corpus()
    brief_targets = {
        ev["target_id"]
        for ev in corpus.workflow_events
        if ev["event_type"] == "generation"
    }
    for brief in corpus.review_briefs:
        assert brief["brief_id"] in brief_targets


def test_two_seeded_refusals() -> None:
    corpus = build_corpus()
    refusals = [ev for ev in corpus.workflow_events if ev["event_type"] == "refusal"]
    refusal_keys = {(ev["voucher_id"], ev["tool_name"]) for ev in refusals}
    assert ("V-1001", "set_voucher_review_status") in refusal_keys
    assert ("V-1010", "prepare_ao_review_brief") in refusal_keys


def test_audit_invariants_reject_missing_event() -> None:
    corpus = build_corpus()
    # Drop the V-1001 brief generation event; validator must complain.
    corpus.workflow_events = [
        ev
        for ev in corpus.workflow_events
        if not (ev["event_type"] == "generation" and ev["voucher_id"] == "V-1001")
    ]
    try:
        validate_corpus(corpus)
    except AuditInvariantError:
        return
    raise AssertionError("validator should fail when generation event is missing")
