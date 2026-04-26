"""Scoped repository module for the ``story_findings`` table.

Sources of truth:
  - docs/schema-implementation-plan.md sections 5.8 and 8.
"""

from __future__ import annotations

from typing import Any

from ._models import StoryFindingRow

_FINDING_COLUMNS = (
    "finding_id",
    "voucher_id",
    "category",
    "severity",
    "summary",
    "explanation",
    "suggested_question",
    "packet_evidence_pointer",
    "primary_citation_id",
    "confidence",
    "needs_human_review",
    "review_state",
    "created_at",
)


def _row_to_model(row: tuple[Any, ...]) -> StoryFindingRow:
    mapping = dict(zip(_FINDING_COLUMNS, row, strict=False))
    pointer = mapping["packet_evidence_pointer"] or {}
    return StoryFindingRow(
        finding_id=mapping["finding_id"],
        voucher_id=mapping["voucher_id"],
        category=mapping["category"],
        severity=mapping["severity"],
        summary=mapping["summary"],
        explanation=mapping["explanation"],
        suggested_question=mapping["suggested_question"],
        packet_evidence_pointer=dict(pointer),
        primary_citation_id=mapping["primary_citation_id"],
        confidence=mapping["confidence"],
        needs_human_review=bool(mapping["needs_human_review"]),
        review_state=mapping["review_state"],
        created_at=mapping["created_at"],
    )


def list_for_voucher(transaction: Any, voucher_id: str) -> tuple[StoryFindingRow, ...]:
    sql = (
        f"SELECT {', '.join(_FINDING_COLUMNS)} FROM story_findings "
        "WHERE voucher_id = %s ORDER BY severity DESC, created_at ASC, finding_id ASC"
    )
    with transaction.cursor() as cursor:
        cursor.execute(sql, (voucher_id,))
        rows = cursor.fetchall()
    return tuple(_row_to_model(row) for row in rows)


def get_by_id(transaction: Any, finding_id: str) -> StoryFindingRow | None:
    sql = (
        f"SELECT {', '.join(_FINDING_COLUMNS)} FROM story_findings WHERE finding_id = %s"
    )
    with transaction.cursor() as cursor:
        cursor.execute(sql, (finding_id,))
        row = cursor.fetchone()
    if row is None:
        return None
    return _row_to_model(row)


def update_review_state(
    transaction: Any,
    *,
    finding_id: str,
    new_state: str,
    audit_event: dict[str, Any],
) -> StoryFindingRow | None:
    sql = (
        "UPDATE story_findings SET review_state = %s WHERE finding_id = %s "
        f"RETURNING {', '.join(_FINDING_COLUMNS)}"
    )
    with transaction.cursor() as cursor:
        cursor.execute(sql, (new_state, finding_id))
        row = cursor.fetchone()
    if row is None:
        return None
    from . import workflow_events as _wf

    _wf.insert(transaction, event=audit_event)
    return _row_to_model(row)


__all__ = ["get_by_id", "list_for_voucher", "update_review_state"]
