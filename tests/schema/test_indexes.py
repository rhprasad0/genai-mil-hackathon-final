"""Sanity tests that the named indexes exist (via ``pg_indexes``).

Schema plan section 5 enumerates per-table indexes, and section 6 enumerates
unique constraints that materialize as unique indexes. This test does not
benchmark performance; it only verifies the names exist after migrations
have applied.
"""

from __future__ import annotations

from typing import Any

import pytest

EXPECTED_INDEXES = (
    # vouchers
    "vouchers_traveler_id_idx",
    "vouchers_review_status_open_idx",
    "vouchers_demo_packet_submitted_at_idx",
    # voucher_line_items
    "voucher_line_items_voucher_id_idx",
    "voucher_line_items_voucher_line_index_uidx",
    "voucher_line_items_expense_date_idx",
    # evidence_refs
    "evidence_refs_voucher_id_idx",
    "evidence_refs_line_item_id_idx",
    # prior_voucher_summaries
    "prior_voucher_summaries_traveler_id_idx",
    # policy_citations
    "policy_citations_topic_idx",
    # external_anomaly_signals
    "external_anomaly_signals_voucher_id_idx",
    "external_anomaly_signals_signal_type_idx",
    "external_anomaly_signals_voucher_signal_key_uidx",
    # story_findings
    "story_findings_voucher_id_idx",
    "story_findings_category_idx",
    "story_findings_voucher_severity_idx",
    "story_findings_needs_human_review_idx",
    # missing_information_items
    "missing_information_items_voucher_id_idx",
    # review_briefs
    "review_briefs_voucher_id_idx",
    # ao_notes
    "ao_notes_voucher_id_idx",
    "ao_notes_voucher_kind_idx",
    # workflow_events
    "workflow_events_voucher_id_idx",
    "workflow_events_voucher_occurred_at_idx",
    "workflow_events_event_type_idx",
)


@pytest.mark.db
@pytest.mark.parametrize("index_name", EXPECTED_INDEXES)
def test_index_exists(postgres: Any, index_name: str) -> None:
    with postgres.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM pg_indexes WHERE schemaname = current_schema() AND indexname = %s",
            (index_name,),
        )
        row = cur.fetchone()
        assert row is not None, f"expected index {index_name!r} to exist"


@pytest.mark.db
def test_unique_voucher_signal_key_index_is_unique(postgres: Any) -> None:
    """Verify the signal_key uniqueness index is actually UNIQUE."""

    with postgres.cursor() as cur:
        cur.execute(
            """
            SELECT indexdef FROM pg_indexes
            WHERE schemaname = current_schema()
              AND indexname = 'external_anomaly_signals_voucher_signal_key_uidx'
            """,
        )
        row = cur.fetchone()
        assert row is not None
        assert "UNIQUE" in row[0].upper()


@pytest.mark.db
def test_review_briefs_voucher_version_unique_constraint(postgres: Any) -> None:
    """Verify the review_briefs (voucher_id, version) unique constraint exists."""

    with postgres.cursor() as cur:
        cur.execute(
            """
            SELECT 1 FROM pg_constraint
            WHERE conname = 'review_briefs_voucher_version_unique'
              AND contype = 'u'
            """,
        )
        row = cur.fetchone()
        assert row is not None, "expected unique constraint on review_briefs(voucher_id, version)"
