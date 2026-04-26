"""Distribution matches schema plan section 7.3."""

from __future__ import annotations

from collections import defaultdict

from ops.seed.generators.corpus import build_corpus
from ops.seed.validators.fk_and_volume import REVIEW_STATUS_SPREAD


def test_review_status_spread() -> None:
    corpus = build_corpus()
    actual: dict[str, set[str]] = defaultdict(set)
    for v in corpus.vouchers:
        actual[v["review_status"]].add(v["voucher_id"])
    for status, expected in REVIEW_STATUS_SPREAD.items():
        assert actual[status] == expected, (
            f"review_status={status!r} expected {sorted(expected)}, "
            f"got {sorted(actual[status])}"
        )


def test_no_seeded_status_is_blocked() -> None:
    """Sanity: no seeded review_status is in the blocklist."""
    from ao_radar_mcp.safety.controlled_status import (
        ALLOWED_VOUCHER_REVIEW_STATUSES,
        BLOCKED_STATUS_VALUES,
    )

    corpus = build_corpus()
    for v in corpus.vouchers:
        assert v["review_status"] in ALLOWED_VOUCHER_REVIEW_STATUSES
        assert v["review_status"] not in BLOCKED_STATUS_VALUES
