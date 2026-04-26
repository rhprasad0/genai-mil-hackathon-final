"""Integration tests for fraud-mock client + Lambda invoke.

Source of truth: docs/testing-plan.md section 5.5 and
docs/application-implementation-plan.md section 9.
"""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.db


def test_fraud_mock_deterministic_across_invocations(database_url: str) -> None:
    pytest.skip(
        "Pending Phase 3 fraud-mock client wiring against a deployed "
        "fraud-mock Lambda or local stub. Determinism is already covered "
        "by tests/unit/test_fraud_mock.py."
    )


def test_fraud_mock_replay_does_not_duplicate_signal_keys(database_url: str) -> None:
    pytest.skip(
        "Pending Phase 3 idempotent upsert through repository.signals."
    )
