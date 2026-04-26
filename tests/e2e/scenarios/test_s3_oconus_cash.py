"""E2E scenario S3: OCONUS cash / exchange-rate reconstruction (V-1007).

Source of truth: docs/testing-plan.md section 8 S3.
"""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.e2e


def test_e2e_oconus_cash_exchange_rate(mcp_base_url: str) -> None:
    pytest.skip(
        "Pending deployed endpoint + seeded V-1007; this scenario walks "
        "prepare_ao_review_brief and asserts a "
        "cash_atm_or_exchange_reconstruction finding with "
        "needs_human_review=true."
    )
