"""Signal-key validator.

Every external_anomaly_signals row must carry a deterministic signal_key of
shape ``<signal_type>:<scenario_slug>:<ordinal>``; ``(voucher_id, signal_key)``
must be unique; and ``signal_id == 'SIG-' + voucher_id + '-' + slugified_signal_key``.
"""

from __future__ import annotations

import re
from typing import Any

from ops.seed.generators.determinism import slugify


class SignalKeyError(ValueError):
    pass


_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*:[a-z0-9_]+:\d{2}$")


def validate_corpus(corpus: Any) -> None:
    seen: set[tuple[str, str]] = set()
    for row in corpus.external_anomaly_signals:
        signal_key = row["signal_key"]
        if not _KEY_RE.match(signal_key):
            raise SignalKeyError(
                f"signal_key={signal_key!r} does not match <signal_type>:<scenario_slug>:<NN>"
            )
        # signal_type prefix sanity.
        prefix = signal_key.split(":")[0]
        if row["signal_type"] != prefix:
            raise SignalKeyError(
                f"signal_key prefix {prefix!r} does not match signal_type {row['signal_type']!r}"
            )
        pair = (row["voucher_id"], signal_key)
        if pair in seen:
            raise SignalKeyError(
                f"duplicate (voucher_id, signal_key) pair: {pair}"
            )
        seen.add(pair)
        expected_id = f"SIG-{row['voucher_id']}-{slugify(signal_key)}"
        if row["signal_id"] != expected_id:
            raise SignalKeyError(
                f"signal_id {row['signal_id']!r} does not match derived {expected_id!r}"
            )


__all__ = ["SignalKeyError", "validate_corpus"]
