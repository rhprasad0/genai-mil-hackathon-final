"""External-anomaly signal row builder."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ops.seed.constants import SYNTHETIC_SOURCE_LABEL
from ops.seed.generators.cards import SignalCard, StoryCard
from ops.seed.generators.determinism import derive_timestamp, slugify


def build_signal_key(signal: SignalCard, ordinal: int) -> str:
    return f"{signal.signal_type}:{signal.scenario_slug}:{ordinal:02d}"


def build_signal_id(voucher_id: str, signal_key: str) -> str:
    return f"SIG-{voucher_id}-{slugify(signal_key)}"


def build_signal_rows(card: StoryCard) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    # Track ordinal per (signal_type, scenario_slug) so duplicates resolve.
    ordinals: dict[tuple[str, str], int] = {}
    base_date = card.voucher.demo_packet_submitted_at
    if isinstance(base_date, datetime):
        base = base_date if base_date.tzinfo else base_date.replace(tzinfo=timezone.utc)
    else:
        base = derive_timestamp(card.voucher.trip_start_date)
    for offset_idx, signal in enumerate(card.external_anomaly_signals):
        key = (signal.signal_type, signal.scenario_slug)
        ordinals[key] = ordinals.get(key, 0) + 1
        signal_key = build_signal_key(signal, ordinals[key])
        signal_id = build_signal_id(card.voucher_id, signal_key)
        received = derive_timestamp(base, offset_minutes=10 + offset_idx)
        rows.append(
            {
                "signal_id": signal_id,
                "voucher_id": card.voucher_id,
                "signal_key": signal_key,
                "signal_type": signal.signal_type,
                "synthetic_source_label": SYNTHETIC_SOURCE_LABEL,
                "rationale_text": signal.rationale_text,
                "confidence": signal.confidence,
                "is_official_finding": False,
                "not_sufficient_for_adverse_action": True,
                "received_at": received,
            }
        )
    return rows


def signal_id_for_finding_link(
    card: StoryCard, signal_type: str, signal_rows: list[dict[str, Any]]
) -> str | None:
    """Return the first signal_id whose signal_type matches.

    Findings reference signals by ``signal_type`` in the card schema; the
    generator resolves that to the deterministic ``signal_id``.
    """

    for row in signal_rows:
        if row["voucher_id"] == card.voucher_id and row["signal_type"] == signal_type:
            return row["signal_id"]
    return None


__all__ = [
    "build_signal_key",
    "build_signal_id",
    "build_signal_rows",
    "signal_id_for_finding_link",
]
