"""Scoped repository module for the ``story_findings`` table.

Sources of truth:
  - docs/schema-implementation-plan.md sections 5.8 and 8.
"""

from __future__ import annotations

from typing import Any

from ._models import StoryFindingRow


def list_for_voucher(transaction: Any, voucher_id: str) -> tuple[StoryFindingRow, ...]:
    raise NotImplementedError(  # TODO Phase 2
        "findings.list_for_voucher will SELECT by voucher_id in Phase 2"
    )


def get_by_id(transaction: Any, finding_id: str) -> StoryFindingRow | None:
    raise NotImplementedError(  # TODO Phase 2
        "findings.get_by_id will SELECT by finding_id in Phase 2"
    )


def update_review_state(
    transaction: Any,
    *,
    finding_id: str,
    new_state: str,
    audit_event: dict[str, Any],
) -> None:
    raise NotImplementedError(  # TODO Phase 5
        "findings.update_review_state will run domain UPDATE + paired "
        "scoped_write workflow_event insert in a single transaction in Phase 5"
    )


__all__ = ["get_by_id", "list_for_voucher", "update_review_state"]
