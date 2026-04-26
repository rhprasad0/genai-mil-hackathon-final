"""E2E scenario S3: OCONUS cash / exchange-rate reconstruction (V-1007).

Source of truth: docs/testing-plan.md section 8 S3.
"""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.e2e


def test_e2e_oconus_cash_exchange_rate(mcp_base_url: str) -> None:
    pytest.skip(
        "Pending application Phase 2+ wiring of prepare_ao_review_brief. "
        "The deployed endpoint and V-1007 seed are present, but tools "
        "currently return the Phase 1 not_implemented stub."
    )
