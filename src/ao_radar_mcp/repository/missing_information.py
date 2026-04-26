"""Scoped repository module for the ``missing_information_items`` table.

Sources of truth:
  - docs/schema-implementation-plan.md section 5.9.
"""

from __future__ import annotations

from typing import Any

from ._models import MissingInformationItemRow

_COLUMNS = (
    "missing_item_id",
    "voucher_id",
    "description",
    "why_it_matters",
    "expected_location_hint",
    "linked_line_item_id",
    "created_at",
)


def _row_to_model(row: tuple[Any, ...]) -> MissingInformationItemRow:
    mapping = dict(zip(_COLUMNS, row, strict=False))
    return MissingInformationItemRow(
        missing_item_id=mapping["missing_item_id"],
        voucher_id=mapping["voucher_id"],
        description=mapping["description"],
        why_it_matters=mapping["why_it_matters"],
        expected_location_hint=mapping["expected_location_hint"],
        linked_line_item_id=mapping["linked_line_item_id"],
        created_at=mapping["created_at"],
    )


def list_for_voucher(transaction: Any, voucher_id: str) -> tuple[MissingInformationItemRow, ...]:
    sql = (
        f"SELECT {', '.join(_COLUMNS)} FROM missing_information_items "
        "WHERE voucher_id = %s ORDER BY created_at ASC, missing_item_id ASC"
    )
    with transaction.cursor() as cursor:
        cursor.execute(sql, (voucher_id,))
        rows = cursor.fetchall()
    return tuple(_row_to_model(row) for row in rows)


__all__ = ["list_for_voucher"]
