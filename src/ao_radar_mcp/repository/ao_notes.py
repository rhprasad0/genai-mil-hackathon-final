"""Scoped repository module for the ``ao_notes`` table.

Sources of truth:
  - docs/schema-implementation-plan.md sections 5.11 and 8.
"""

from __future__ import annotations

from typing import Any

from ._models import AONoteRow


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
    raise NotImplementedError(  # TODO Phase 5
        "ao_notes.append will INSERT one row plus the paired scoped_write "
        "workflow_event in a single transaction in Phase 5"
    )


def list_for_voucher(
    transaction: Any,
    voucher_id: str,
    *,
    kind: str | None = None,
) -> tuple[AONoteRow, ...]:
    raise NotImplementedError(  # TODO Phase 5
        "ao_notes.list_for_voucher will SELECT by voucher_id (and optional kind) in Phase 5"
    )


__all__ = ["append", "list_for_voucher"]
