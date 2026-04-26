"""Scoped repository module for the ``evidence_refs`` table.

Sources of truth:
  - docs/schema-implementation-plan.md section 5.4.
"""

from __future__ import annotations

from typing import Any

from ._models import EvidenceRefRow


def list_for_voucher(transaction: Any, voucher_id: str) -> tuple[EvidenceRefRow, ...]:
    raise NotImplementedError(  # TODO Phase 2
        "evidence.list_for_voucher will SELECT ordered by line_item_id in Phase 2"
    )


def list_for_line_item(transaction: Any, line_item_id: str) -> tuple[EvidenceRefRow, ...]:
    raise NotImplementedError(  # TODO Phase 2
        "evidence.list_for_line_item will SELECT by line_item_id in Phase 2"
    )


__all__ = ["list_for_voucher", "list_for_line_item"]
