"""Scoped repository module for the ``review_briefs`` table.

Sources of truth:
  - docs/schema-implementation-plan.md sections 5.10 and 8.
"""

from __future__ import annotations

from typing import Any

from ._models import ReviewBriefRow


def get_latest_for_voucher(transaction: Any, voucher_id: str) -> ReviewBriefRow | None:
    raise NotImplementedError(  # TODO Phase 4
        "briefs.get_latest_for_voucher will SELECT MAX(version) row in Phase 4"
    )


def get_by_id(transaction: Any, brief_id: str) -> ReviewBriefRow | None:
    raise NotImplementedError(  # TODO Phase 4
        "briefs.get_by_id will SELECT by brief_id in Phase 4"
    )


def append_version(
    transaction: Any,
    *,
    voucher_id: str,
    draft: dict[str, Any],
    audit_event: dict[str, Any],
) -> ReviewBriefRow:
    raise NotImplementedError(  # TODO Phase 4
        "briefs.append_version will INSERT a new versioned row plus the paired "
        "generation workflow_event in a single transaction in Phase 4"
    )


__all__ = ["append_version", "get_by_id", "get_latest_for_voucher"]
