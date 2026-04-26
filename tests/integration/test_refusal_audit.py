"""Integration tests for refusal-path audit invariants.

Source of truth: docs/testing-plan.md section 5.5 and section 6 G3.
"""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.db


def test_refusal_blocks_domain_write_and_records_sanitized_event(database_url: str) -> None:
    pytest.skip(
        "Pending Phase 5 wiring; this test will issue a blocked-status "
        "set_voucher_review_status call and assert exactly one "
        "event_type=refusal row was written before the response returned."
    )
