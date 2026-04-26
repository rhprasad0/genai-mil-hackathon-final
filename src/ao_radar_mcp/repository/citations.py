"""Scoped repository module for the ``policy_citations`` table.

Sources of truth:
  - docs/schema-implementation-plan.md section 5.6.

Reads only at runtime.  No application path may insert citations; the
synthetic demo reference corpus is loaded by the seed routine.
"""

from __future__ import annotations

from typing import Any

from ._models import PolicyCitationRow

_COLUMNS = (
    "citation_id",
    "source_identifier",
    "topic",
    "excerpt_text",
    "retrieval_anchor",
    "applicability_note",
    "created_at",
)


def _row_to_model(row: tuple[Any, ...]) -> PolicyCitationRow:
    mapping = dict(zip(_COLUMNS, row, strict=False))
    return PolicyCitationRow(
        citation_id=mapping["citation_id"],
        source_identifier=mapping["source_identifier"],
        topic=mapping["topic"],
        excerpt_text=mapping["excerpt_text"],
        retrieval_anchor=mapping["retrieval_anchor"],
        applicability_note=mapping["applicability_note"],
        created_at=mapping["created_at"],
    )


def get_by_id(transaction: Any, citation_id: str) -> PolicyCitationRow | None:
    sql = f"SELECT {', '.join(_COLUMNS)} FROM policy_citations WHERE citation_id = %s"
    with transaction.cursor() as cursor:
        cursor.execute(sql, (citation_id,))
        row = cursor.fetchone()
    if row is None:
        return None
    return _row_to_model(row)


def search(
    transaction: Any,
    *,
    query: str,
    topic: str | None = None,
    limit: int | None = None,
) -> tuple[PolicyCitationRow, ...]:
    raise NotImplementedError(  # TODO Phase 2
        "citations.search will SELECT by topic / retrieval_anchor in Phase 2"
    )


__all__ = ["get_by_id", "search"]
