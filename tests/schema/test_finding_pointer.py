"""Tests for ``story_findings.packet_evidence_pointer`` shape.

Schema plan section 5.8 / TR-5: every finding must point to at least one
piece of in-packet evidence by id (line_item_id and/or evidence_ref_id).
A bare ``excerpt_hint`` without an id is rejected.

``pytest.raises(Exception)`` is intentional; the CHECK on the JSON pointer
shape is the only CHECK exercised here.
"""

# ruff: noqa: B017

from __future__ import annotations

import json
from typing import Any

import pytest

from tests.schema.conftest import insert_line_item, insert_traveler, insert_voucher


def _insert_finding(
    conn: Any,
    *,
    finding_id: str,
    voucher_id: str,
    pointer: dict[str, Any],
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO story_findings (
                finding_id, voucher_id, category, severity, summary,
                explanation, suggested_question, packet_evidence_pointer,
                primary_citation_id, confidence, needs_human_review,
                review_state
            ) VALUES (
                %s, %s, 'evidence_quality_concern', 'low', 'demo summary',
                'demo explanation', 'demo question', %s::jsonb,
                NULL, 'low', FALSE, 'open'
            )
            """,
            (finding_id, voucher_id, json.dumps(pointer)),
        )


@pytest.mark.db
class TestFindingPacketEvidencePointer:
    def test_pointer_with_line_item_id_accepted(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        line_item_id = synthetic_ids["line_item_id"]
        finding_id = synthetic_ids["finding_id"]
        insert_traveler(postgres, traveler_id)
        insert_voucher(postgres, voucher_id, traveler_id)
        insert_line_item(postgres, line_item_id, voucher_id)
        _insert_finding(
            postgres,
            finding_id=finding_id,
            voucher_id=voucher_id,
            pointer={"line_item_id": line_item_id, "excerpt_hint": "demo"},
        )

    def test_pointer_with_evidence_ref_id_accepted(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        finding_id = synthetic_ids["finding_id"]
        insert_traveler(postgres, traveler_id)
        insert_voucher(postgres, voucher_id, traveler_id)
        # Pointer references an id; the CHECK only validates JSON shape, not FK.
        _insert_finding(
            postgres,
            finding_id=finding_id,
            voucher_id=voucher_id,
            pointer={"evidence_ref_id": "ER-DEMO-1", "excerpt_hint": "demo"},
        )

    def test_pointer_with_both_ids_accepted(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        line_item_id = synthetic_ids["line_item_id"]
        finding_id = synthetic_ids["finding_id"]
        insert_traveler(postgres, traveler_id)
        insert_voucher(postgres, voucher_id, traveler_id)
        insert_line_item(postgres, line_item_id, voucher_id)
        _insert_finding(
            postgres,
            finding_id=finding_id,
            voucher_id=voucher_id,
            pointer={
                "line_item_id": line_item_id,
                "evidence_ref_id": "ER-DEMO-1",
                "excerpt_hint": "demo",
            },
        )

    def test_pointer_with_only_excerpt_hint_rejected(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        finding_id = synthetic_ids["finding_id"]
        insert_traveler(postgres, traveler_id)
        insert_voucher(postgres, voucher_id, traveler_id)
        with pytest.raises(Exception):
            _insert_finding(
                postgres,
                finding_id=finding_id,
                voucher_id=voucher_id,
                pointer={"excerpt_hint": "demo only"},
            )

    def test_pointer_empty_object_rejected(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        finding_id = synthetic_ids["finding_id"]
        insert_traveler(postgres, traveler_id)
        insert_voucher(postgres, voucher_id, traveler_id)
        with pytest.raises(Exception):
            _insert_finding(
                postgres,
                finding_id=finding_id,
                voucher_id=voucher_id,
                pointer={},
            )

    def test_pointer_with_null_id_rejected(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
    ) -> None:
        """A pointer carrying the keys but with null values must still fail."""

        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        finding_id = synthetic_ids["finding_id"]
        insert_traveler(postgres, traveler_id)
        insert_voucher(postgres, voucher_id, traveler_id)
        with pytest.raises(Exception):
            _insert_finding(
                postgres,
                finding_id=finding_id,
                voucher_id=voucher_id,
                pointer={"line_item_id": None, "evidence_ref_id": None},
            )
