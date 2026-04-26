"""Pure validator CLI for the AO Radar seed package.

``python -m ops.seed.validate --cards-only`` runs the YAML + Pydantic +
text validators on raw cards. ``python -m ops.seed.validate`` additionally
runs the in-memory generators and the row-level validators. Neither command
touches Postgres.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ops.seed.generators.cards import load_all_cards
from ops.seed.generators.corpus import build_corpus, seed_root
from ops.seed.validators import (
    audit_invariants,
    authority_boundary,
    blocked_status,
    coverage,
    fk_and_volume,
    signal_keys,
    synthetic_markers,
    unsafe_wording,
)


def _validate_cards_only(seed_dir: Path) -> None:
    cards = load_all_cards(seed_dir / "cards")
    if not cards:
        raise SystemExit("no cards found")
    print(f"[cards-only] parsed {len(cards)} story cards from {seed_dir / 'cards'}")


def _validate_full(seed_dir: Path) -> None:
    corpus = build_corpus(seed_dir)
    print(f"[full] generated corpus: {len(corpus.cards)} cards, "
          f"{len(corpus.vouchers)} vouchers, "
          f"{len(corpus.voucher_line_items)} line items, "
          f"{len(corpus.evidence_refs)} evidence refs, "
          f"{len(corpus.external_anomaly_signals)} signals, "
          f"{len(corpus.story_findings)} findings, "
          f"{len(corpus.missing_information_items)} missing items, "
          f"{len(corpus.review_briefs)} briefs, "
          f"{len(corpus.ao_notes)} ao_notes, "
          f"{len(corpus.workflow_events)} workflow_events")
    synthetic_markers.validate_corpus(corpus)
    print("[full] synthetic_markers: ok")
    blocked_status.validate_corpus(corpus)
    print("[full] blocked_status: ok")
    unsafe_wording.validate_corpus(corpus)
    print("[full] unsafe_wording: ok")
    authority_boundary.validate_corpus(corpus)
    print("[full] authority_boundary: ok")
    signal_keys.validate_corpus(corpus)
    print("[full] signal_keys: ok")
    fk_and_volume.validate_corpus(corpus)
    print("[full] fk_and_volume: ok")
    coverage.validate_corpus(corpus, seed_dir / "coverage_map.yaml")
    print("[full] coverage: ok")
    audit_invariants.validate_corpus(corpus)
    print("[full] audit_invariants: ok")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ops.seed.validate")
    parser.add_argument(
        "--cards-only",
        action="store_true",
        help="parse cards + run text validators only; do not run generators or row checks",
    )
    parser.add_argument("--seed-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    seed_dir = args.seed_dir or seed_root()
    try:
        _validate_cards_only(seed_dir)
        if not args.cards_only:
            _validate_full(seed_dir)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
