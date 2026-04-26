"""Scoped repository module for the ``vouchers`` table.

Sources of truth:
  - docs/schema-implementation-plan.md sections 5.2 and 8.
  - docs/application-implementation-plan.md section 8.

Read methods: by id, list ordered by status and demo_packet_submitted_at.
Write methods: ``review_status`` updates only — every successful update
emits a ``scoped_write`` workflow_event in the same transaction, and every
blocked-status attempt emits a ``refusal`` event before returning.

Phase 1 placeholder: methods raise ``NotImplementedError`` until the schema
plan's Phase 4 (repository) lands.  Tools in this phase remain on
``not_implemented`` responses.
"""

from __future__ import annotations

from typing import Any

from ._models import VoucherRow


def get_by_id(transaction: Any, voucher_id: str) -> VoucherRow | None:
    """Return a single voucher row or ``None`` if not found."""

    raise NotImplementedError(  # TODO Phase 2
        "vouchers.get_by_id will use a parameterized SELECT in Phase 2"
    )


def list_for_queue(
    transaction: Any,
    *,
    limit: int | None = None,
) -> tuple[VoucherRow, ...]:
    """Return vouchers ordered for queue listing (workload guidance only)."""

    raise NotImplementedError(  # TODO Phase 2
        "vouchers.list_for_queue will return rows ordered by review_status / "
        "demo_packet_submitted_at in Phase 2"
    )


def update_review_status(
    transaction: Any,
    *,
    voucher_id: str,
    new_status: str,
    audit_event: dict[str, Any],
) -> None:
    """Update ``review_status`` and emit the paired audit row in one txn."""

    raise NotImplementedError(  # TODO Phase 5
        "vouchers.update_review_status will run domain UPDATE plus the "
        "scoped_write workflow_event insert in a single transaction in Phase 5"
    )


__all__ = ["get_by_id", "list_for_queue", "update_review_status"]
