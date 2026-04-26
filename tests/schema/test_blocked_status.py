"""Tests that the blocklist in schema plan section 6.4 is enforced.

Covers ``vouchers.review_status``, ``story_findings.review_state``, and
``workflow_events.resulting_status`` for both insert and (where applicable)
update paths. Allowed values are also exercised so we are not just testing
the reject side.

The ``pytest.raises(Exception)`` blocks below intentionally catch any DB-side
error: a CHECK violation, the controlled-enum allowed-list violation, or the
explicit blocklist CHECK can each fire first depending on row content, and
all three are valid rejections of the blocked input.
"""

# ruff: noqa: B017

from __future__ import annotations

import json
from typing import Any

import pytest

from ao_radar_mcp.safety.authority_boundary import HUMAN_AUTHORITY_BOUNDARY_TEXT
from tests.schema.conftest import insert_line_item, insert_traveler, insert_voucher

BLOCKED_STATUS_VALUES = (
    "approved", "approve",
    "denied", "deny", "rejected", "reject",
    "certified", "certify",
    "submitted", "submit", "submitted_to_dts",
    "returned", "return", "return_voucher", "officially_returned",
    "cancelled", "canceled", "cancel",
    "amended", "amend",
    "paid", "payable", "nonpayable", "ready_for_payment", "payment_ready",
    "fraud", "fraudulent", "misuse", "abuse", "misconduct",
    "entitled", "entitlement_determined",
    "escalated_to_investigators", "notify_command", "contact_traveler",
)

ALLOWED_VOUCHER_STATUSES = (
    "needs_review",
    "in_review",
    "awaiting_traveler_clarification",
    "ready_for_human_decision",
    "closed_in_demo",
)

ALLOWED_FINDING_REVIEW_STATES = (
    "open",
    "reviewed_explained",
    "reviewed_unresolved",
    "needs_followup",
)


def _insert_finding(
    conn: Any,
    *,
    finding_id: str,
    voucher_id: str,
    line_item_id: str,
    review_state: str = "open",
) -> None:
    pointer = json.dumps({"line_item_id": line_item_id, "excerpt_hint": "test"})
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
                NULL, 'low', FALSE, %s
            )
            """,
            (finding_id, voucher_id, pointer, review_state),
        )


def _insert_event(
    conn: Any,
    *,
    event_id: str,
    voucher_id: str,
    resulting_status: str | None,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO workflow_events (
                event_id, voucher_id, actor_label, event_type, tool_name,
                target_kind, target_id, resulting_status,
                rationale_metadata, human_authority_boundary_reminder
            ) VALUES (
                %s, %s, 'demo_ao_user_1', 'scoped_write', 'set_voucher_review_status',
                'voucher', %s, %s, '{}'::jsonb, %s
            )
            """,
            (event_id, voucher_id, voucher_id, resulting_status, HUMAN_AUTHORITY_BOUNDARY_TEXT),
        )


@pytest.mark.db
class TestVoucherReviewStatus:
    @pytest.mark.parametrize("blocked_value", BLOCKED_STATUS_VALUES)
    def test_blocked_value_rejected_on_insert(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
        blocked_value: str,
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        insert_traveler(postgres, traveler_id)
        with pytest.raises(Exception):
            insert_voucher(postgres, voucher_id, traveler_id, review_status=blocked_value)

    @pytest.mark.parametrize("blocked_value", BLOCKED_STATUS_VALUES)
    def test_blocked_value_rejected_on_update(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
        blocked_value: str,
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        insert_traveler(postgres, traveler_id)
        insert_voucher(postgres, voucher_id, traveler_id)
        with pytest.raises(Exception):
            with postgres.cursor() as cur:
                cur.execute(
                    "UPDATE vouchers SET review_status = %s WHERE voucher_id = %s",
                    (blocked_value, voucher_id),
                )

    @pytest.mark.parametrize("allowed_value", ALLOWED_VOUCHER_STATUSES)
    def test_allowed_value_accepted(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
        allowed_value: str,
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        insert_traveler(postgres, traveler_id)
        insert_voucher(postgres, voucher_id, traveler_id, review_status=allowed_value)
        with postgres.cursor() as cur:
            cur.execute("SELECT review_status FROM vouchers WHERE voucher_id = %s", (voucher_id,))
            row = cur.fetchone()
            assert row is not None
            assert row[0] == allowed_value


@pytest.mark.db
class TestStoryFindingReviewState:
    @pytest.mark.parametrize("blocked_value", BLOCKED_STATUS_VALUES)
    def test_blocked_value_rejected_on_insert(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
        blocked_value: str,
    ) -> None:
        traveler_id = synthetic_ids["traveler_id"]
        voucher_id = synthetic_ids["voucher_id"]
        line_item_id = synthetic_ids["line_item_id"]
        finding_id = synthetic_ids["finding_id"]
        insert_traveler(postgres, traveler_id)
        insert_voucher(postgres, voucher_id, traveler_id)
        insert_line_item(postgres, line_item_id, voucher_id)
        with pytest.raises(Exception):
            _insert_finding(
                postgres,
                finding_id=finding_id,
                voucher_id=voucher_id,
                line_item_id=line_item_id,
                review_state=blocked_value,
            )

    @pytest.mark.parametrize("blocked_value", BLOCKED_STATUS_VALUES)
    def test_blocked_value_rejected_on_update(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
        blocked_value: str,
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
            line_item_id=line_item_id,
            review_state="open",
        )
        with pytest.raises(Exception):
            with postgres.cursor() as cur:
                cur.execute(
                    "UPDATE story_findings SET review_state = %s WHERE finding_id = %s",
                    (blocked_value, finding_id),
                )

    @pytest.mark.parametrize("allowed_value", ALLOWED_FINDING_REVIEW_STATES)
    def test_allowed_value_accepted(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
        allowed_value: str,
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
            line_item_id=line_item_id,
            review_state=allowed_value,
        )


@pytest.mark.db
class TestWorkflowEventResultingStatus:
    @pytest.mark.parametrize("blocked_value", BLOCKED_STATUS_VALUES)
    def test_blocked_value_rejected_on_insert(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
        blocked_value: str,
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
                resulting_status=blocked_value,
            )

    @pytest.mark.parametrize(
        "allowed_value",
        ALLOWED_VOUCHER_STATUSES + ALLOWED_FINDING_REVIEW_STATES,
    )
    def test_allowed_value_accepted(
        self,
        postgres: Any,
        synthetic_ids: dict[str, str],
        allowed_value: str,
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
            resulting_status=allowed_value,
        )

    def test_null_resulting_status_accepted(
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
            resulting_status=None,
        )
