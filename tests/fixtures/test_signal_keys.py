"""Signal-key uniqueness + signal_id derivation."""

from __future__ import annotations

import re

from ops.seed.generators.corpus import build_corpus
from ops.seed.validators.signal_keys import SignalKeyError, validate_corpus


def test_signal_keys_unique_per_voucher() -> None:
    corpus = build_corpus()
    seen: set[tuple[str, str]] = set()
    for s in corpus.external_anomaly_signals:
        pair = (s["voucher_id"], s["signal_key"])
        assert pair not in seen, f"duplicate {pair}"
        seen.add(pair)


def test_signal_id_derivation() -> None:
    corpus = build_corpus()
    for s in corpus.external_anomaly_signals:
        assert s["signal_id"].startswith(f"SIG-{s['voucher_id']}-")
        # signal_key format
        assert re.match(r"^[a-z][a-z0-9_]*:[a-z0-9_]+:\d{2}$", s["signal_key"])


def test_signal_keys_validator_runs() -> None:
    corpus = build_corpus()
    validate_corpus(corpus)


def test_signal_keys_validator_rejects_duplicate() -> None:
    corpus = build_corpus()
    if not corpus.external_anomaly_signals:
        return
    dup = dict(corpus.external_anomaly_signals[0])
    corpus.external_anomaly_signals.append(dup)
    try:
        validate_corpus(corpus)
    except SignalKeyError:
        return
    raise AssertionError("validator should reject duplicate (voucher_id, signal_key)")
