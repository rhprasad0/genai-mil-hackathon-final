"""Coverage validator runs cleanly on the seed corpus."""

from __future__ import annotations

from pathlib import Path

from ops.seed.generators.corpus import build_corpus, seed_root
from ops.seed.validators.coverage import CoverageError, validate_corpus


def test_coverage_map_resolves() -> None:
    seed_dir = seed_root()
    corpus = build_corpus(seed_dir)
    validate_corpus(corpus, seed_dir / "coverage_map.yaml")


def test_coverage_map_rejects_unresolved_case(tmp_path: Path) -> None:
    seed_dir = seed_root()
    corpus = build_corpus(seed_dir)
    bogus_map = tmp_path / "coverage_map.yaml"
    bogus_map.write_text(
        "coverage:\n  - case: not_in_corpus\n    vouchers: [V-9999]\n",
        encoding="utf-8",
    )
    try:
        validate_corpus(corpus, bogus_map)
    except CoverageError:
        return
    raise AssertionError("validator should reject an unresolved coverage case")
