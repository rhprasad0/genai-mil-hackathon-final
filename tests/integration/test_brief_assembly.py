"""Integration tests for ``prepare_ao_review_brief`` against a seeded DB.

Source of truth: docs/testing-plan.md section 5.5 and the audit-event
invariant matrix in docs/schema-implementation-plan.md section 8.
"""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.db


def test_prepare_ao_review_brief_v1003_hooks_resolve(database_url: str) -> None:
    pytest.skip(
        "Pending Phase 4 brief fusion + Phase 3 seed data; once both land, "
        "this test asserts every hook resolves through the read tools."
    )


def test_brief_hooks_resolve_to_real_rows(database_url: str) -> None:
    pytest.skip(
        "Pending Phase 4 brief fusion; this test will round-trip "
        "policy_hooks / signal_hooks / finding_hooks / "
        "missing_information_hooks through their read tools."
    )
