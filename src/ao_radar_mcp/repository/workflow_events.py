"""Scoped repository module for the ``workflow_events`` table.

Sources of truth:
  - docs/schema-implementation-plan.md sections 5.12 and 8.

Append-only.  Writes are routed through other repository modules so the
domain row and the audit event commit in the same transaction.  This module
is the only one that exposes a direct ``insert`` for paired audit rows; it
never offers an ``execute`` / ``query`` escape hatch to upstream code.
"""

from __future__ import annotations

from typing import Any

from ._models import WorkflowEventRow


def insert(
    transaction: Any,
    *,
    event: dict[str, Any],
) -> None:
    raise NotImplementedError(  # TODO Phase 2
        "workflow_events.insert will run a parameterized INSERT in Phase 2; "
        "callers always invoke this from inside an existing transaction."
    )


def list_for_voucher(
    transaction: Any,
    voucher_id: str,
    *,
    limit: int | None = None,
) -> tuple[WorkflowEventRow, ...]:
    raise NotImplementedError(  # TODO Phase 5
        "workflow_events.list_for_voucher will SELECT ordered by occurred_at in Phase 5"
    )


__all__ = ["insert", "list_for_voucher"]
