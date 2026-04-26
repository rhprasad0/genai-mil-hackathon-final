"""Scoped repository module for the ``evidence_refs`` table.

Sources of truth:
  - docs/schema-implementation-plan.md section 5.4.
"""

from __future__ import annotations

from typing import Any

from ._models import EvidenceRefRow

_COLUMNS = (
    "evidence_ref_id",
    "voucher_id",
    "line_item_id",
    "packet_level_role",
    "content_type_indicator",
    "legibility_cue",
    "itemization_cue",
    "payment_evidence_cue",
    "vendor_label_on_evidence",
    "evidence_date_on_face",
    "amount_on_face_minor_units",
    "currency_code_on_face",
    "notes",
)


def _row_to_model(row: tuple[Any, ...]) -> EvidenceRefRow:
    mapping = dict(zip(_COLUMNS, row, strict=False))
    return EvidenceRefRow(
        evidence_ref_id=mapping["evidence_ref_id"],
        voucher_id=mapping["voucher_id"],
        line_item_id=mapping["line_item_id"],
        packet_level_role=mapping["packet_level_role"],
        content_type_indicator=mapping["content_type_indicator"],
        legibility_cue=mapping["legibility_cue"],
        itemization_cue=mapping["itemization_cue"],
        payment_evidence_cue=mapping["payment_evidence_cue"],
        vendor_label_on_evidence=mapping["vendor_label_on_evidence"],
        evidence_date_on_face=mapping["evidence_date_on_face"],
        amount_on_face_minor_units=(
            int(mapping["amount_on_face_minor_units"])
            if mapping["amount_on_face_minor_units"] is not None
            else None
        ),
        currency_code_on_face=mapping["currency_code_on_face"],
        notes=mapping["notes"] or "",
    )


def list_for_voucher(transaction: Any, voucher_id: str) -> tuple[EvidenceRefRow, ...]:
    sql = (
        f"SELECT {', '.join(_COLUMNS)} FROM evidence_refs "
        "WHERE voucher_id = %s ORDER BY line_item_id NULLS LAST, evidence_ref_id ASC"
    )
    with transaction.cursor() as cursor:
        cursor.execute(sql, (voucher_id,))
        rows = cursor.fetchall()
    return tuple(_row_to_model(row) for row in rows)


def list_for_line_item(transaction: Any, line_item_id: str) -> tuple[EvidenceRefRow, ...]:
    sql = (
        f"SELECT {', '.join(_COLUMNS)} FROM evidence_refs "
        "WHERE line_item_id = %s ORDER BY evidence_ref_id ASC"
    )
    with transaction.cursor() as cursor:
        cursor.execute(sql, (line_item_id,))
        rows = cursor.fetchall()
    return tuple(_row_to_model(row) for row in rows)


__all__ = ["list_for_voucher", "list_for_line_item"]
