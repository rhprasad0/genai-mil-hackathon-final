"""Tests for ``evidence_refs`` constraints.

Covers the schema plan section 5.4 rules:

* ``content_type_indicator = none_attached_demo`` forces every cue column to
  ``not_applicable``.
* At least one of ``line_item_id`` or ``packet_level_role`` must be present.
* A line-item-attached row works without ``packet_level_role``.

``pytest.raises(Exception)`` is intentional: any CHECK violation is a valid
rejection of bad evidence_refs rows.
"""

# ruff: noqa: B017

from __future__ import annotations

from typing import Any

import pytest

from tests.schema.conftest import insert_line_item, insert_traveler, insert_voucher


def _insert_evidence(
    conn: Any,
    *,
    evidence_ref_id: str,
    voucher_id: str,
    line_item_id: str | None = None,
    packet_level_role: str | None = None,
    content_type_indicator: str = "receipt_image_demo",
    legibility_cue: str = "clear",
    itemization_cue: str = "itemized",
    payment_evidence_cue: str = "present",
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO evidence_refs (
                evidence_ref_id, voucher_id, line_item_id, packet_level_role,
                content_type_indicator, legibility_cue, itemization_cue,
                payment_evidence_cue
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                evidence_ref_id,
                voucher_id,
                line_item_id,
                packet_level_role,
                content_type_indicator,
                legibility_cue,
                itemization_cue,
                payment_evidence_cue,
            ),
        )


@pytest.mark.db
class TestEvidenceRefsRules:
    def test_neither_line_item_nor_packet_role_rejected(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        evidence_ref_id = synthetic_ids["evidence_ref_id"]
        insert_traveler(postgres, traveler_id)
        insert_voucher(postgres, voucher_id, traveler_id)
        with pytest.raises(Exception):
            _insert_evidence(
                postgres,
                evidence_ref_id=evidence_ref_id,
                voucher_id=voucher_id,
                line_item_id=None,
                packet_level_role=None,
            )

    def test_line_item_attached_without_packet_role_works(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        line_item_id = synthetic_ids["line_item_id"]
        evidence_ref_id = synthetic_ids["evidence_ref_id"]
        insert_traveler(postgres, traveler_id)
        insert_voucher(postgres, voucher_id, traveler_id)
        insert_line_item(postgres, line_item_id, voucher_id)
        _insert_evidence(
            postgres,
            evidence_ref_id=evidence_ref_id,
            voucher_id=voucher_id,
            line_item_id=line_item_id,
            packet_level_role=None,
        )

    def test_packet_level_role_required_when_no_line_item(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        evidence_ref_id = synthetic_ids["evidence_ref_id"]
        insert_traveler(postgres, traveler_id)
        insert_voucher(postgres, voucher_id, traveler_id)
        # Row valid because packet_level_role is set.
        _insert_evidence(
            postgres,
            evidence_ref_id=evidence_ref_id,
            voucher_id=voucher_id,
            line_item_id=None,
            packet_level_role="trip_itinerary",
            content_type_indicator="itinerary_pdf_demo",
        )

    def test_invalid_packet_level_role_rejected(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        evidence_ref_id = synthetic_ids["evidence_ref_id"]
        insert_traveler(postgres, traveler_id)
        insert_voucher(postgres, voucher_id, traveler_id)
        with pytest.raises(Exception):
            _insert_evidence(
                postgres,
                evidence_ref_id=evidence_ref_id,
                voucher_id=voucher_id,
                line_item_id=None,
                packet_level_role="not_a_real_role",
                content_type_indicator="itinerary_pdf_demo",
            )

    def test_none_attached_with_non_na_legibility_rejected(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        line_item_id = synthetic_ids["line_item_id"]
        evidence_ref_id = synthetic_ids["evidence_ref_id"]
        insert_traveler(postgres, traveler_id)
        insert_voucher(postgres, voucher_id, traveler_id)
        insert_line_item(postgres, line_item_id, voucher_id)
        with pytest.raises(Exception):
            _insert_evidence(
                postgres,
                evidence_ref_id=evidence_ref_id,
                voucher_id=voucher_id,
                line_item_id=line_item_id,
                content_type_indicator="none_attached_demo",
                legibility_cue="clear",
                itemization_cue="not_applicable",
                payment_evidence_cue="not_applicable",
            )

    def test_none_attached_with_non_na_itemization_rejected(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        line_item_id = synthetic_ids["line_item_id"]
        evidence_ref_id = synthetic_ids["evidence_ref_id"]
        insert_traveler(postgres, traveler_id)
        insert_voucher(postgres, voucher_id, traveler_id)
        insert_line_item(postgres, line_item_id, voucher_id)
        with pytest.raises(Exception):
            _insert_evidence(
                postgres,
                evidence_ref_id=evidence_ref_id,
                voucher_id=voucher_id,
                line_item_id=line_item_id,
                content_type_indicator="none_attached_demo",
                legibility_cue="not_applicable",
                itemization_cue="itemized",
                payment_evidence_cue="not_applicable",
            )

    def test_none_attached_with_non_na_payment_rejected(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        line_item_id = synthetic_ids["line_item_id"]
        evidence_ref_id = synthetic_ids["evidence_ref_id"]
        insert_traveler(postgres, traveler_id)
        insert_voucher(postgres, voucher_id, traveler_id)
        insert_line_item(postgres, line_item_id, voucher_id)
        with pytest.raises(Exception):
            _insert_evidence(
                postgres,
                evidence_ref_id=evidence_ref_id,
                voucher_id=voucher_id,
                line_item_id=line_item_id,
                content_type_indicator="none_attached_demo",
                legibility_cue="not_applicable",
                itemization_cue="not_applicable",
                payment_evidence_cue="present",
            )

    def test_none_attached_all_na_accepted(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        line_item_id = synthetic_ids["line_item_id"]
        evidence_ref_id = synthetic_ids["evidence_ref_id"]
        insert_traveler(postgres, traveler_id)
        insert_voucher(postgres, voucher_id, traveler_id)
        insert_line_item(postgres, line_item_id, voucher_id)
        _insert_evidence(
            postgres,
            evidence_ref_id=evidence_ref_id,
            voucher_id=voucher_id,
            line_item_id=line_item_id,
            content_type_indicator="none_attached_demo",
            legibility_cue="not_applicable",
            itemization_cue="not_applicable",
            payment_evidence_cue="not_applicable",
        )
