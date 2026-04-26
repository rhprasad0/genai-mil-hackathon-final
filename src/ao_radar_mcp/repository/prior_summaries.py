"""Scoped repository module for the ``prior_voucher_summaries`` table.

Sources of truth:
  - docs/schema-implementation-plan.md section 5.5.
"""

from __future__ import annotations

from typing import Any

from ._models import PriorVoucherSummaryRow


def list_for_traveler(transaction: Any, traveler_id: str) -> tuple[PriorVoucherSummaryRow, ...]:
    raise NotImplementedError(  # TODO Phase 2
        "prior_summaries.list_for_traveler will SELECT by traveler_id in Phase 2"
    )


__all__ = ["list_for_traveler"]
