"""Tests for the human-authority boundary CHECKs on briefs and events.

The CHECKs require every action verb (approve, deny, certify, return, cancel,
amend, submit) plus entitlement, payability, fraud, and external clauses,
together with a negation marker. The canonical string from
``src/ao_radar_mcp/safety/authority_boundary.py`` passes; weak / empty /
clause-missing strings fail.

These tests intentionally exercise the schema CHECK only. They do not
duplicate the application-side ``validate_boundary_text`` unit test.

``pytest.raises(Exception)`` is used because the CHECK constraint surface
covers multiple distinct violations (missing clause, missing negation marker,
empty string), and we care that the DB rejects rather than which specific
error class fires.
"""

# ruff: noqa: B017

from __future__ import annotations

from typing import Any

import pytest

from ao_radar_mcp.safety.authority_boundary import HUMAN_AUTHORITY_BOUNDARY_TEXT
from tests.schema.conftest import insert_traveler, insert_voucher

WEAK_BOUNDARY_TEXTS = (
    # Empty.
    "",
    "   ",
    # Missing fraud + external clauses.
    (
        "AO Radar does not approve, deny, certify, return, cancel, amend, "
        "submit, determine entitlement, or determine payability."
    ),
    # Missing fraud (only external is present).
    (
        "AO Radar does not approve, deny, certify, return, cancel, amend, "
        "submit, determine entitlement, determine payability, or contact "
        "external parties."
    ),
    # Missing external (only fraud is present).
    (
        "AO Radar does not approve, deny, certify, return, cancel, amend, "
        "submit, determine entitlement, determine payability, or accuse fraud."
    ),
    # No negation: looks affirmative even if every clause is named.
    (
        "AO Radar will approve, deny, certify, return, cancel, amend, submit, "
        "determine entitlement, determine payability, accuse fraud, and "
        "contact external parties."
    ),
)


def _insert_brief(
    conn: Any,
    *,
    brief_id: str,
    voucher_id: str,
    boundary_text: str,
    version: int = 1,
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


def _insert_event(
    conn: Any,
    *,
    event_id: str,
    voucher_id: str,
    boundary_reminder: str,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO workflow_events (
                event_id, voucher_id, actor_label, event_type, tool_name,
                target_kind, target_id, resulting_status,
                rationale_metadata, human_authority_boundary_reminder
            ) VALUES (
                %s, %s, 'demo_ao_user_1', 'generation', 'prepare_ao_review_brief',
                'brief', %s, NULL, '{}'::jsonb, %s
            )
            """,
            (event_id, voucher_id, voucher_id, boundary_reminder),
        )


@pytest.mark.db
class TestReviewBriefBoundaryText:
    def test_canonical_string_accepted(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        brief_id = synthetic_ids["brief_id"]
        insert_traveler(postgres, traveler_id)
        insert_voucher(postgres, voucher_id, traveler_id)
        _insert_brief(
            postgres,
            brief_id=brief_id,
            voucher_id=voucher_id,
            boundary_text=HUMAN_AUTHORITY_BOUNDARY_TEXT,
        )

    @pytest.mark.parametrize("weak_text", WEAK_BOUNDARY_TEXTS)
    def test_weak_text_rejected(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
        weak_text: str,
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        brief_id = synthetic_ids["brief_id"]
        insert_traveler(postgres, traveler_id)
        insert_voucher(postgres, voucher_id, traveler_id)
        with pytest.raises(Exception):
            _insert_brief(
                postgres,
                brief_id=brief_id,
                voucher_id=voucher_id,
                boundary_text=weak_text,
            )


@pytest.mark.db
class TestWorkflowEventBoundaryReminder:
    def test_canonical_string_accepted(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        event_id = synthetic_ids["event_id"]
        insert_traveler(postgres, traveler_id)
        insert_voucher(postgres, voucher_id, traveler_id)
        _insert_event(
            postgres,
            event_id=event_id,
            voucher_id=voucher_id,
            boundary_reminder=HUMAN_AUTHORITY_BOUNDARY_TEXT,
        )

    @pytest.mark.parametrize("weak_text", WEAK_BOUNDARY_TEXTS)
    def test_weak_text_rejected(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
        weak_text: str,
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        event_id = synthetic_ids["event_id"]
        insert_traveler(postgres, traveler_id)
        insert_voucher(postgres, voucher_id, traveler_id)
        with pytest.raises(Exception):
            _insert_event(
                postgres,
                event_id=event_id,
                voucher_id=voucher_id,
                boundary_reminder=weak_text,
            )
