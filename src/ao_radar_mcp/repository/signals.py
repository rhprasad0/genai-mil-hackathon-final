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

_COLUMNS = (
    "signal_id",
    "voucher_id",
    "signal_key",
    "signal_type",
    "synthetic_source_label",
    "rationale_text",
    "confidence",
    "is_official_finding",
    "not_sufficient_for_adverse_action",
    "received_at",
)


def _row_to_model(row: tuple[Any, ...]) -> ExternalAnomalySignalRow:
    mapping = dict(zip(_COLUMNS, row, strict=False))
    return ExternalAnomalySignalRow(
        signal_id=mapping["signal_id"],
        voucher_id=mapping["voucher_id"],
        signal_key=mapping["signal_key"],
        signal_type=mapping["signal_type"],
        synthetic_source_label=mapping["synthetic_source_label"],
        rationale_text=mapping["rationale_text"],
        confidence=mapping["confidence"],
        is_official_finding=bool(mapping["is_official_finding"]),
        not_sufficient_for_adverse_action=bool(mapping["not_sufficient_for_adverse_action"]),
        received_at=mapping["received_at"],
    )


def list_for_voucher(transaction: Any, voucher_id: str) -> tuple[ExternalAnomalySignalRow, ...]:
    sql = (
        f"SELECT {', '.join(_COLUMNS)} FROM external_anomaly_signals "
        "WHERE voucher_id = %s ORDER BY received_at ASC, signal_id ASC"
    )
    with transaction.cursor() as cursor:
        cursor.execute(sql, (voucher_id,))
        rows = cursor.fetchall()
    return tuple(_row_to_model(row) for row in rows)


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
