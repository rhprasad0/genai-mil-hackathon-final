"""Scoped repository module for the ``ao_notes`` table.

Sources of truth:
  - docs/schema-implementation-plan.md sections 5.11 and 8.
"""

from __future__ import annotations

import uuid
from typing import Any

from ._models import AONoteRow

_COLUMNS = (
    "note_id",
    "voucher_id",
    "finding_id",
    "kind",
    "body",
    "actor_label",
    "created_at",
    "superseded_by_note_id",
)


def _row_to_model(row: tuple[Any, ...]) -> AONoteRow:
    mapping = dict(zip(_COLUMNS, row, strict=False))
    return AONoteRow(
        note_id=mapping["note_id"],
        voucher_id=mapping["voucher_id"],
        finding_id=mapping["finding_id"],
        kind=mapping["kind"],
        body=mapping["body"],
        actor_label=mapping["actor_label"],
        created_at=mapping["created_at"],
        superseded_by_note_id=mapping["superseded_by_note_id"],
    )


def append(
    transaction: Any,
    *,
    voucher_id: str,
    finding_id: str | None,
    kind: str,
    body: str,
    actor_label: str,
    audit_event: dict[str, Any],
) -> AONoteRow:
    note_id = f"NOTE-{uuid.uuid4().hex[:12]}"
    sql = (
        "INSERT INTO ao_notes ("
        "note_id, voucher_id, finding_id, kind, body, actor_label, created_at"
        ") VALUES (%s, %s, %s, %s, %s, %s, NOW()) "
        f"RETURNING {', '.join(_COLUMNS)}"
    )
    with transaction.cursor() as cursor:
        cursor.execute(
            sql,
            (note_id, voucher_id, finding_id, kind, body, actor_label),
        )
        row = cursor.fetchone()

    persisted = _row_to_model(row)
    enriched_event = dict(audit_event)
    enriched_event["target_id"] = persisted.note_id

    from . import workflow_events as _wf

    _wf.insert(transaction, event=enriched_event)
    return persisted


def list_for_voucher(
    transaction: Any,
    voucher_id: str,
    *,
    kind: str | None = None,
) -> tuple[AONoteRow, ...]:
    sql = (
        f"SELECT {', '.join(_COLUMNS)} FROM ao_notes WHERE voucher_id = %s"
    )
    params: tuple[Any, ...] = (voucher_id,)
    if kind is not None:
        sql += " AND kind = %s"
        params = (voucher_id, kind)
    sql += " ORDER BY created_at ASC, note_id ASC"
    with transaction.cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()
    return tuple(_row_to_model(row) for row in rows)


__all__ = ["append", "list_for_voucher"]
