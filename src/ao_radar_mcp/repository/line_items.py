"""Scoped repository module for the ``voucher_line_items`` table.

Sources of truth:
  - docs/schema-implementation-plan.md section 5.3.
"""

from __future__ import annotations

from typing import Any

from ._models import LineItemRow

_COLUMNS = (
    "line_item_id",
    "voucher_id",
    "line_index",
    "expense_date",
    "amount_minor_units",
    "currency_code",
    "exchange_rate_to_usd",
    "category",
    "vendor_label",
    "payment_instrument_indicator",
    "free_text_notes",
    "claimed_by_traveler_at",
)


def _row_to_model(row: tuple[Any, ...]) -> LineItemRow:
    mapping = dict(zip(_COLUMNS, row, strict=False))
    return LineItemRow(
        line_item_id=mapping["line_item_id"],
        voucher_id=mapping["voucher_id"],
        line_index=int(mapping["line_index"]),
        expense_date=mapping["expense_date"],
        amount_minor_units=int(mapping["amount_minor_units"]),
        currency_code=mapping["currency_code"],
        exchange_rate_to_usd=(
            float(mapping["exchange_rate_to_usd"])
            if mapping["exchange_rate_to_usd"] is not None
            else None
        ),
        category=mapping["category"],
        vendor_label=mapping["vendor_label"],
        payment_instrument_indicator=mapping["payment_instrument_indicator"],
        free_text_notes=mapping["free_text_notes"] or "",
        claimed_by_traveler_at=mapping["claimed_by_traveler_at"],
    )


def list_for_voucher(transaction: Any, voucher_id: str) -> tuple[LineItemRow, ...]:
    sql = (
        f"SELECT {', '.join(_COLUMNS)} FROM voucher_line_items "
        "WHERE voucher_id = %s ORDER BY line_index ASC"
    )
    with transaction.cursor() as cursor:
        cursor.execute(sql, (voucher_id,))
        rows = cursor.fetchall()
    return tuple(_row_to_model(row) for row in rows)


__all__ = ["list_for_voucher"]
