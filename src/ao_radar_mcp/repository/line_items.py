"""Scoped repository module for the ``voucher_line_items`` table.

Sources of truth:
  - docs/schema-implementation-plan.md section 5.3.
"""

from __future__ import annotations

from typing import Any

from ._models import LineItemRow


def list_for_voucher(transaction: Any, voucher_id: str) -> tuple[LineItemRow, ...]:
    raise NotImplementedError(  # TODO Phase 2
        "line_items.list_for_voucher will SELECT ordered by line_index in Phase 2"
    )


__all__ = ["list_for_voucher"]
