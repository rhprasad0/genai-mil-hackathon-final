"""Integration tests for ``export_review_brief`` audit invariants.

Source of truth: docs/testing-plan.md section 5.5.
"""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.db


def test_export_review_brief_writes_export_event(database_url: str) -> None:
    pytest.skip(
        "Pending Phase 4 wiring; once the export tool lands, this test "
        "asserts an event_type=export workflow_event is written and the "
        "canonical boundary reminder is part of the export payload."
    )
