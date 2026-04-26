"""Integration tests for the audit-event invariant matrix.

Source of truth: docs/schema-implementation-plan.md section 8 and
docs/testing-plan.md section 5.5.

These tests are gated on ``DATABASE_URL`` (the conftest fixture skips them
when unset).  They exercise the repository layer + the audit helper inside
a single Postgres transaction.
"""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.db


def test_audit_invariant_matrix_holds_after_write(database_url: str) -> None:
    """Placeholder until the repository write paths land in Phase 5."""

    pytest.skip(
        "Repository write paths land with schema/seed/application Phase 5; "
        "see docs/application-implementation-plan.md section 10."
    )


def test_each_scoped_write_returns_resolvable_audit_event_id(database_url: str) -> None:
    pytest.skip(
        "Pending Phase 5 wiring of scoped writes through the audit helper; "
        "see docs/application-implementation-plan.md section 10."
    )


def test_scoped_write_rolls_back_domain_write_when_audit_insert_fails(
    database_url: str,
) -> None:
    pytest.skip(
        "Pending Phase 5 transaction-rollback test once the repository "
        "executes domain + audit writes inside a single transaction."
    )
