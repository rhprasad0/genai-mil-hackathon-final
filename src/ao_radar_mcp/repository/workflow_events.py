"""Scoped repository module for the ``workflow_events`` table.

Sources of truth:
  - docs/schema-implementation-plan.md sections 5.12 and 8.

Append-only.  Writes are routed through other repository modules so the
domain row and the audit event commit in the same transaction.  This module
is the only one that exposes a direct ``insert`` for paired audit rows; it
never offers an ``execute`` / ``query`` escape hatch to upstream code.
"""

from __future__ import annotations

import json
from typing import Any

from ._models import WorkflowEventRow

_COLUMNS = (
    "event_id",
    "voucher_id",
    "actor_label",
    "occurred_at",
    "event_type",
    "tool_name",
    "target_kind",
    "target_id",
    "resulting_status",
    "rationale_metadata",
    "human_authority_boundary_reminder",
)


def _row_to_model(row: tuple[Any, ...]) -> WorkflowEventRow:
    mapping = dict(zip(_COLUMNS, row, strict=False))
    rationale = mapping["rationale_metadata"] or {}
    return WorkflowEventRow(
        event_id=mapping["event_id"],
        voucher_id=mapping["voucher_id"],
        actor_label=mapping["actor_label"],
        occurred_at=mapping["occurred_at"],
        event_type=mapping["event_type"],
        tool_name=mapping["tool_name"],
        target_kind=mapping["target_kind"],
        target_id=mapping["target_id"],
        resulting_status=mapping["resulting_status"],
        rationale_metadata=dict(rationale),
        human_authority_boundary_reminder=mapping["human_authority_boundary_reminder"],
    )


def insert(transaction: Any, *, event: dict[str, Any]) -> None:
    """Insert one workflow_events row inside the caller's transaction."""

    rationale = event.get("rationale_metadata") or {}
    if not isinstance(rationale, dict):
        raise ValueError("rationale_metadata must be a JSON object")
    sql = (
        "INSERT INTO workflow_events ("
        "event_id, voucher_id, actor_label, occurred_at, event_type, "
        "tool_name, target_kind, target_id, resulting_status, "
        "rationale_metadata, human_authority_boundary_reminder"
        ") VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)"
    )
    with transaction.cursor() as cursor:
        cursor.execute(
            sql,
            (
                event["event_id"],
                event.get("voucher_id"),
                event["actor_label"],
                event["occurred_at"],
                event["event_type"],
                event.get("tool_name"),
                event["target_kind"],
                event.get("target_id"),
                event.get("resulting_status"),
                json.dumps(rationale),
                event["human_authority_boundary_reminder"],
            ),
        )


def list_for_voucher(
    transaction: Any,
    voucher_id: str,
    *,
    limit: int | None = None,
) -> tuple[WorkflowEventRow, ...]:
    sql = (
        f"SELECT {', '.join(_COLUMNS)} FROM workflow_events "
        "WHERE voucher_id = %s ORDER BY occurred_at ASC, event_id ASC"
    )
    params: tuple[Any, ...] = (voucher_id,)
    if limit is not None:
        sql += " LIMIT %s"
        params = (voucher_id, int(limit))
    with transaction.cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()
    return tuple(_row_to_model(row) for row in rows)


__all__ = ["insert", "list_for_voucher"]
