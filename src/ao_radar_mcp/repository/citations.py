"""Scoped repository module for the ``policy_citations`` table.

Sources of truth:
  - docs/schema-implementation-plan.md section 5.6.

Reads only at runtime.  No application path may insert citations; the
synthetic demo reference corpus is loaded by the seed routine.
"""

from __future__ import annotations

from typing import Any

from ._models import PolicyCitationRow


def get_by_id(transaction: Any, citation_id: str) -> PolicyCitationRow | None:
    raise NotImplementedError(  # TODO Phase 2
        "citations.get_by_id will SELECT by citation_id in Phase 2"
    )


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
