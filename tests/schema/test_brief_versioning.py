"""Tests for ``review_briefs`` versioning uniqueness.

Schema plan section 5.10 requires unique ``(voucher_id, version)``. A second
insert with the same pair is rejected; a fresh version increment is accepted.

``pytest.raises(Exception)`` is intentional: psycopg's UniqueViolation is
the expected DB-side error.
"""

# ruff: noqa: B017

from __future__ import annotations

from typing import Any

import pytest

from ao_radar_mcp.safety.authority_boundary import HUMAN_AUTHORITY_BOUNDARY_TEXT
from tests.schema.conftest import insert_traveler, insert_voucher


def _insert_brief(
    conn: Any,
    *,
    brief_id: str,
    voucher_id: str,
    version: int,
    boundary_text: str = HUMAN_AUTHORITY_BOUNDARY_TEXT,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO review_briefs (
                brief_id, voucher_id, version, priority_score, priority_rationale,
                suggested_focus, evidence_gap_summary, story_coherence_summary,
                draft_clarification_note, brief_uncertainty,
                human_authority_boundary_text, is_partial
            ) VALUES (
                %s, %s, %s, 0.5, 'demo rationale',
                'demo focus', 'demo gap', 'demo coherence',
                'demo clarification', 'medium', %s, FALSE
            )
            """,
            (brief_id, voucher_id, version, boundary_text),
        )


@pytest.mark.db
class TestReviewBriefVersioning:
    def test_version_one_accepted(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        brief_id = synthetic_ids["brief_id"]
        insert_traveler(postgres, traveler_id)
        insert_voucher(postgres, voucher_id, traveler_id)
        _insert_brief(postgres, brief_id=brief_id, voucher_id=voucher_id, version=1)

    def test_duplicate_version_rejected(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        brief_id_a = synthetic_ids["brief_id"] + "-A"
        brief_id_b = synthetic_ids["brief_id"] + "-B"
        insert_traveler(postgres, traveler_id)
        insert_voucher(postgres, voucher_id, traveler_id)
        _insert_brief(postgres, brief_id=brief_id_a, voucher_id=voucher_id, version=1)
        with pytest.raises(Exception):
            _insert_brief(
                postgres,
                brief_id=brief_id_b,
                voucher_id=voucher_id,
                version=1,
            )

    def test_incremented_version_accepted(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        brief_id_a = synthetic_ids["brief_id"] + "-A"
        brief_id_b = synthetic_ids["brief_id"] + "-B"
        insert_traveler(postgres, traveler_id)
        insert_voucher(postgres, voucher_id, traveler_id)
        _insert_brief(postgres, brief_id=brief_id_a, voucher_id=voucher_id, version=1)
        _insert_brief(postgres, brief_id=brief_id_b, voucher_id=voucher_id, version=2)

    def test_same_version_for_different_voucher_accepted(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id_a = synthetic_ids["voucher_id"] + "-A"
        voucher_id_b = synthetic_ids["voucher_id"] + "-B"
        brief_id_a = synthetic_ids["brief_id"] + "-A"
        brief_id_b = synthetic_ids["brief_id"] + "-B"
        insert_traveler(postgres, traveler_id)
        insert_voucher(postgres, voucher_id_a, traveler_id)
        insert_voucher(postgres, voucher_id_b, traveler_id)
        _insert_brief(postgres, brief_id=brief_id_a, voucher_id=voucher_id_a, version=1)
        _insert_brief(postgres, brief_id=brief_id_b, voucher_id=voucher_id_b, version=1)
