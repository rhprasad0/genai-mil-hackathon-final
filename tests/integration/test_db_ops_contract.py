"""Integration tests for the private DB-ops Lambda contract.

Source of truth: docs/testing-plan.md section 7 and
docs/application-implementation-plan.md section 12.
"""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.db


def test_db_ops_migrate_succeeds(database_url: str) -> None:
    pytest.skip(
        "Pending Phase 4 application wiring; this test exercises "
        "ao_radar_db_ops.handler.lambda_handler with operation=migrate "
        "and asserts the migration runner advances the schema."
    )


def test_db_ops_seed_succeeds(database_url: str) -> None:
    pytest.skip(
        "Pending Phase 3 seed routine ownership by the synthetic-data team; "
        "this test exercises ao_radar_db_ops.handler with operation=seed."
    )


def test_db_ops_seed_reset_succeeds(database_url: str) -> None:
    pytest.skip(
        "Pending Phase 3 seed routine; this test exercises "
        "ao_radar_db_ops.handler with operation=seed, reset=True."
    )
