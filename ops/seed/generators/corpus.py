"""Top-level corpus assembler.

Reads every YAML source under ``ops/seed/`` and returns a single
``Corpus`` mapping that contains the in-memory rows for every table the seed
touches. Pure (no DB) — the loader is the only path that talks to Postgres.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ops.seed.generators.briefs import build_ao_note_rows, build_brief_row
from ops.seed.generators.cards import StoryCard, load_all_cards
from ops.seed.generators.citations import load_citations
from ops.seed.generators.events import (
    build_card_workflow_events,
    build_refusal_events,
)
from ops.seed.generators.findings import (
    build_finding_rows,
    build_finding_signal_link_rows,
    build_missing_item_rows,
)
from ops.seed.generators.signals import build_signal_rows
from ops.seed.generators.travelers import load_prior_summaries, load_travelers
from ops.seed.generators.vouchers import (
    build_evidence_rows,
    build_line_item_rows,
    build_voucher_row,
)


@dataclass
class Corpus:
    cards: list[StoryCard] = field(default_factory=list)
    travelers: list[dict[str, Any]] = field(default_factory=list)
    prior_voucher_summaries: list[dict[str, Any]] = field(default_factory=list)
    policy_citations: list[dict[str, Any]] = field(default_factory=list)
    vouchers: list[dict[str, Any]] = field(default_factory=list)
    voucher_line_items: list[dict[str, Any]] = field(default_factory=list)
    evidence_refs: list[dict[str, Any]] = field(default_factory=list)
    external_anomaly_signals: list[dict[str, Any]] = field(default_factory=list)
    story_findings: list[dict[str, Any]] = field(default_factory=list)
    finding_signal_links: list[dict[str, Any]] = field(default_factory=list)
    missing_information_items: list[dict[str, Any]] = field(default_factory=list)
    review_briefs: list[dict[str, Any]] = field(default_factory=list)
    ao_notes: list[dict[str, Any]] = field(default_factory=list)
    workflow_events: list[dict[str, Any]] = field(default_factory=list)


def seed_root(repo_root: Path | None = None) -> Path:
    """Locate ``ops/seed/`` based on this file's location."""

    if repo_root is not None:
        return repo_root / "ops" / "seed"
    return Path(__file__).resolve().parent.parent


def build_corpus(seed_dir: Path | None = None) -> Corpus:
    """Walk every YAML under ``seed_dir`` and return an in-memory corpus."""

    if seed_dir is None:
        seed_dir = seed_root()
    cards = load_all_cards(seed_dir / "cards")
    travelers = load_travelers(seed_dir / "travelers.yaml")
    prior_summaries = load_prior_summaries(seed_dir / "prior_summaries.yaml")
    citations = load_citations(seed_dir / "citations.yaml")

    corpus = Corpus(
        cards=cards,
        travelers=travelers,
        prior_voucher_summaries=prior_summaries,
        policy_citations=citations,
    )

    # Per-card derivations.
    for card in cards:
        voucher_row = build_voucher_row(card)
        line_rows = build_line_item_rows(card)
        evidence_rows = build_evidence_rows(card)
        signal_rows = build_signal_rows(card)
        finding_rows = build_finding_rows(card)
        missing_rows = build_missing_item_rows(card)
        link_rows = build_finding_signal_link_rows(card, finding_rows, signal_rows)
        brief_row = build_brief_row(card)
        note_rows = build_ao_note_rows(card)
        events_rows = build_card_workflow_events(card, brief_row, finding_rows, note_rows)

        corpus.vouchers.append(voucher_row)
        corpus.voucher_line_items.extend(line_rows)
        corpus.evidence_refs.extend(evidence_rows)
        corpus.external_anomaly_signals.extend(signal_rows)
        corpus.story_findings.extend(finding_rows)
        corpus.missing_information_items.extend(missing_rows)
        corpus.finding_signal_links.extend(link_rows)
        corpus.review_briefs.append(brief_row)
        corpus.ao_notes.extend(note_rows)
        corpus.workflow_events.extend(events_rows)

    # Refusal seeds (schema plan section 7.4).
    refusal_rows = build_refusal_events(seed_dir / "refusal_seeds.yaml")
    corpus.workflow_events.extend(refusal_rows)

    # Stable sort the workflow_events for deterministic output.
    corpus.workflow_events.sort(
        key=lambda r: (r["voucher_id"] or "", r["occurred_at"], r["event_id"])
    )

    return corpus


__all__ = ["Corpus", "build_corpus", "seed_root"]
