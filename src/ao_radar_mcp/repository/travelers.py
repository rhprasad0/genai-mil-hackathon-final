"""Scoped repository module for the ``travelers`` table.

Sources of truth:
  - docs/schema-implementation-plan.md section 5.1.
"""

from __future__ import annotations

from typing import Any

from ._models import TravelerRow


def get_by_id(transaction: Any, traveler_id: str) -> TravelerRow | None:
    raise NotImplementedError(  # TODO Phase 2
        "travelers.get_by_id will SELECT by traveler_id in Phase 2"
    )


__all__ = ["get_by_id"]
