"""Scoped repository module for the ``external_anomaly_signals`` table.

Sources of truth:
  - docs/schema-implementation-plan.md section 5.7.

Append-only writes.  ``upsert_synthetic_signal`` treats unique-key conflicts
on ``(voucher_id, signal_key)`` as successful idempotent replays per the
fraud-mock contract.
"""

from __future__ import annotations

from typing import Any

from ._models import ExternalAnomalySignalRow


def list_for_voucher(transaction: Any, voucher_id: str) -> tuple[ExternalAnomalySignalRow, ...]:
    raise NotImplementedError(  # TODO Phase 3
        "signals.list_for_voucher will SELECT by voucher_id in Phase 3"
    )


def upsert_synthetic_signal(
    transaction: Any,
    *,
    row: ExternalAnomalySignalRow,
    audit_event: dict[str, Any],
) -> ExternalAnomalySignalRow:
    raise NotImplementedError(  # TODO Phase 3
        "signals.upsert_synthetic_signal will INSERT … ON CONFLICT DO NOTHING "
        "and write the paired retrieval workflow_event in Phase 3"
    )


__all__ = ["list_for_voucher", "upsert_synthetic_signal"]
