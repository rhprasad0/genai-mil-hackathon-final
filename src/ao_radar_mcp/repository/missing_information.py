"""Scoped repository module for the ``missing_information_items`` table.

Sources of truth:
  - docs/schema-implementation-plan.md section 5.9.
"""

from __future__ import annotations

from typing import Any

from ._models import MissingInformationItemRow


def list_for_voucher(transaction: Any, voucher_id: str) -> tuple[MissingInformationItemRow, ...]:
    raise NotImplementedError(  # TODO Phase 2
        "missing_information.list_for_voucher will SELECT by voucher_id in Phase 2"
    )


__all__ = ["list_for_voucher"]
