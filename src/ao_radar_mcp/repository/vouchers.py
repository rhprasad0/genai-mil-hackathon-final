"""Scoped repository module for the ``vouchers`` table.

Sources of truth:
  - docs/schema-implementation-plan.md sections 5.2 and 8.
  - docs/application-implementation-plan.md section 8.

Read methods: by id, list ordered by status and demo_packet_submitted_at.
Write methods: ``review_status`` updates only — every successful update
emits a ``scoped_write`` workflow_event in the same transaction, and every
blocked-status attempt emits a ``refusal`` event before returning.
"""

from __future__ import annotations

from typing import Any

from ._models import VoucherRow

_VOUCHER_COLUMNS = (
    "voucher_id",
    "traveler_id",
    "trip_purpose_category",
    "trip_start_date",
    "trip_end_date",
    "declared_origin",
    "declared_destinations",
    "funding_reference_label",
    "funding_reference_quality",
    "justification_text",
    "pre_existing_flags",
    "demo_packet_submitted_at",
    "review_status",
    "data_environment",
    "created_at",
    "updated_at",
)


def _row_to_model(row: tuple[Any, ...]) -> VoucherRow:
    mapping = dict(zip(_VOUCHER_COLUMNS, row, strict=False))
    declared = mapping["declared_destinations"] or []
    flags = mapping["pre_existing_flags"] or []
    return VoucherRow(
        voucher_id=mapping["voucher_id"],
        traveler_id=mapping["traveler_id"],
        trip_purpose_category=mapping["trip_purpose_category"],
        trip_start_date=mapping["trip_start_date"],
        trip_end_date=mapping["trip_end_date"],
        declared_origin=mapping["declared_origin"],
        declared_destinations=list(declared),
        funding_reference_label=mapping["funding_reference_label"],
        funding_reference_quality=mapping["funding_reference_quality"],
        justification_text=mapping["justification_text"],
        pre_existing_flags=list(flags),
        demo_packet_submitted_at=mapping["demo_packet_submitted_at"],
        review_status=mapping["review_status"],
        data_environment=mapping["data_environment"],
        created_at=mapping["created_at"],
        updated_at=mapping["updated_at"],
    )


def get_by_id(transaction: Any, voucher_id: str) -> VoucherRow | None:
    """Return a single voucher row or ``None`` if not found."""

    with transaction.cursor() as cursor:
        cursor.execute(
            f"SELECT {', '.join(_VOUCHER_COLUMNS)} FROM vouchers WHERE voucher_id = %s",
            (voucher_id,),
        )
        row = cursor.fetchone()
    if row is None:
        return None
    return _row_to_model(row)


def list_for_queue(
    transaction: Any,
    *,
    limit: int | None = None,
) -> tuple[VoucherRow, ...]:
    """Return vouchers ordered for queue listing (workload guidance only)."""

    sql = (
        f"SELECT {', '.join(_VOUCHER_COLUMNS)} FROM vouchers "
        "ORDER BY review_status ASC, demo_packet_submitted_at DESC, voucher_id ASC"
    )
    params: tuple[Any, ...] = ()
    if limit is not None:
        sql += " LIMIT %s"
        params = (int(limit),)
    with transaction.cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()
    return tuple(_row_to_model(row) for row in rows)


def update_review_status(
    transaction: Any,
    *,
    voucher_id: str,
    new_status: str,
    audit_event: dict[str, Any],
) -> VoucherRow | None:
    """Update ``review_status`` and emit the paired audit row in one txn."""

    with transaction.cursor() as cursor:
        cursor.execute(
            "UPDATE vouchers SET review_status = %s, updated_at = NOW() "
            "WHERE voucher_id = %s "
            f"RETURNING {', '.join(_VOUCHER_COLUMNS)}",
            (new_status, voucher_id),
        )
        row = cursor.fetchone()
    if row is None:
        return None
    # Audit insert lives in the workflow_events repository; the caller is
    # responsible for executing it inside the same transaction so the domain
    # update and the workflow_events row commit together.
    from . import workflow_events as _wf

    _wf.insert(transaction, event=audit_event)
    return _row_to_model(row)


__all__ = ["get_by_id", "list_for_queue", "update_review_status"]
