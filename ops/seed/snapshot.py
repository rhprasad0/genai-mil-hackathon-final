"""Deterministic JSON snapshot CLI.

``python -m ops.seed.snapshot --out <dir>`` writes one JSON file per table
under ``<dir>``. The CLI is used to verify generator determinism without a DB
connection. Two consecutive runs against the same seed sources must produce
byte-identical files.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

from ops.seed.generators.corpus import build_corpus, seed_root


def _default(o: Any) -> Any:
    if isinstance(o, datetime):
        if o.tzinfo is None:
            return o.isoformat() + "Z"
        return o.isoformat()
    if isinstance(o, date):
        return o.isoformat()
    raise TypeError(f"cannot serialize {type(o).__name__}: {o!r}")


def write_snapshot(out_dir: Path, seed_dir: Path | None = None) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    corpus = build_corpus(seed_dir)
    bundles: dict[str, list[dict[str, Any]]] = {
        "policy_citations": corpus.policy_citations,
        "travelers": corpus.travelers,
        "prior_voucher_summaries": corpus.prior_voucher_summaries,
        "vouchers": corpus.vouchers,
        "voucher_line_items": corpus.voucher_line_items,
        "evidence_refs": corpus.evidence_refs,
        "external_anomaly_signals": corpus.external_anomaly_signals,
        "story_findings": corpus.story_findings,
        "finding_signal_links": corpus.finding_signal_links,
        "missing_information_items": corpus.missing_information_items,
        "review_briefs": corpus.review_briefs,
        "ao_notes": corpus.ao_notes,
        "workflow_events": corpus.workflow_events,
    }
    for name, rows in bundles.items():
        path = out_dir / f"{name}.json"
        with path.open("w", encoding="utf-8") as fh:
            json.dump(
                rows,
                fh,
                sort_keys=True,
                indent=2,
                default=_default,
            )
            fh.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ops.seed.snapshot")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    seed_dir = args.seed_dir or seed_root()
    try:
        write_snapshot(args.out, seed_dir)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"wrote snapshot to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
