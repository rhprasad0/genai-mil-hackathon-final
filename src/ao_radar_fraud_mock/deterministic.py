"""Deterministic helpers for the fraud-mock Lambda.

Sources of truth:
  - docs/application-implementation-plan.md section 9.
  - docs/schema-implementation-plan.md section 5.7 (signal shape).

Synthetic signal generation is deterministic given the inputs and a fixed
seed string ``FRAUD_DETERMINISTIC_SEED``.  Same input → same output across
cold starts so demos and tests are reproducible.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Final, Iterable

from ao_radar_mcp.fraud_client.contract import (
    FraudSignal,
    SIGNAL_TYPES,
    derive_signal_id,
)


_SCENARIO_SLUGS: Final[tuple[str, ...]] = (
    "lodging_overlap_1",
    "fy26_meals_outlier",
    "atm_split_demo",
    "out_of_window_transport",
    "ambiguous_loa_demo",
    "first_submission_review",
    "vendor_edge_demo",
)

_RATIONALE_TEMPLATES: Final[dict[str, str]] = {
    "duplicate_payment_risk": (
        "Two synthetic lodging lines overlap by one demo night. Review prompt "
        "only; reviewer should reconcile the lodging schedule."
    ),
    "high_risk_mcc_demo": (
        "Synthetic merchant category indicator deviates from the declared "
        "category. Review prompt only; reviewer should verify the line "
        "category."
    ),
    "unusual_amount": (
        "Claimed amount is unusually round and well above the synthetic "
        "baseline. Review prompt only; reviewer should ask the traveler to "
        "reconstruct the amount."
    ),
    "date_location_mismatch": (
        "Declared destination differs from synthetic vendor city on the "
        "evidence row. Review prompt only; reviewer should verify."
    ),
    "split_disbursement_oddity": (
        "Cash withdrawal sequence on synthetic ATM lines is unusual relative "
        "to baseline. Review prompt only; reviewer should reconstruct the "
        "amounts."
    ),
    "repeated_correction_pattern": (
        "Traveler's prior synthetic vouchers show a recurring evidence-"
        "attachment correction. Review prompt only; reviewer should confirm "
        "the current packet is complete."
    ),
    "peer_baseline_outlier": (
        "Spend on the line is above the synthetic peer baseline. Review "
        "prompt only; reviewer should verify the line is consistent with "
        "the trip purpose."
    ),
    "traveler_baseline_outlier": (
        "Spend pattern differs from the traveler's own synthetic baseline. "
        "Review prompt only; reviewer should verify the line is consistent "
        "with the trip purpose."
    ),
}


def _digest_int(*parts: str) -> int:
    h = hashlib.sha256()
    for part in parts:
        h.update(part.encode("utf-8"))
        h.update(b"|")
    return int.from_bytes(h.digest()[:8], byteorder="big")


def signal_count_for(voucher_id: str, seed: str) -> int:
    """Determine how many synthetic signals to emit for a voucher (0..3)."""

    return _digest_int(voucher_id, seed, "count") % 4


def pick_signal_type(voucher_id: str, ordinal: int, seed: str) -> str:
    idx = _digest_int(voucher_id, seed, str(ordinal), "type") % len(SIGNAL_TYPES)
    return SIGNAL_TYPES[idx]


def pick_scenario_slug(voucher_id: str, ordinal: int, seed: str) -> str:
    idx = _digest_int(voucher_id, seed, str(ordinal), "scenario") % len(_SCENARIO_SLUGS)
    return _SCENARIO_SLUGS[idx]


def pick_confidence(voucher_id: str, ordinal: int, seed: str) -> str:
    idx = _digest_int(voucher_id, seed, str(ordinal), "confidence") % 3
    return ("low", "medium", "high")[idx]


def make_signal_key(signal_type: str, scenario_slug: str, ordinal: int) -> str:
    return f"{signal_type}:{scenario_slug}:{ordinal}"


def deterministic_timestamp(voucher_id: str, signal_key: str, seed: str) -> datetime:
    """Return a deterministic but plausible timestamp for ``received_at``."""

    digest = _digest_int(voucher_id, signal_key, seed, "ts")
    minute_offset = digest % (60 * 24 * 365)
    base = datetime(2026, 1, 1, tzinfo=UTC)
    return base.replace(minute=0, second=0, microsecond=0) + _minute_offset(minute_offset)


def _minute_offset(minutes: int):  # type: ignore[no-untyped-def]
    from datetime import timedelta

    return timedelta(minutes=minutes)


def generate_signals(
    voucher_id: str,
    *,
    seed: str,
    source_label: str,
    requested_types: Iterable[str] = (),
) -> tuple[FraudSignal, ...]:
    """Produce a deterministic synthetic signal set for ``voucher_id``."""

    requested = {t for t in requested_types if t}
    out: list[FraudSignal] = []
    count = signal_count_for(voucher_id, seed)
    for ordinal in range(1, count + 1):
        signal_type = pick_signal_type(voucher_id, ordinal, seed)
        if requested and signal_type not in requested:
            continue
        scenario_slug = pick_scenario_slug(voucher_id, ordinal, seed)
        signal_key = make_signal_key(signal_type, scenario_slug, ordinal)
        confidence = pick_confidence(voucher_id, ordinal, seed)
        rationale = _RATIONALE_TEMPLATES.get(
            signal_type,
            "Synthetic compliance prompt; reviewer should verify on the packet.",
        )
        out.append(
            FraudSignal(
                voucher_id=voucher_id,
                signal_key=signal_key,
                signal_id=derive_signal_id(voucher_id, signal_key),
                signal_type=signal_type,  # type: ignore[arg-type]
                synthetic_source_label=source_label,
                rationale_text=rationale,
                confidence=confidence,  # type: ignore[arg-type]
                is_official_finding=False,
                not_sufficient_for_adverse_action=True,
                received_at=deterministic_timestamp(voucher_id, signal_key, seed),
            )
        )
    return tuple(out)


__all__ = [
    "deterministic_timestamp",
    "generate_signals",
    "make_signal_key",
    "pick_confidence",
    "pick_scenario_slug",
    "pick_signal_type",
    "signal_count_for",
]
