"""Deployed E2E refusal regression for blocked-status round-trip.

Source of truth: docs/testing-plan.md section 6 G5.
"""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.e2e


def test_deployed_blocked_status_values_refused_with_audit(mcp_base_url: str) -> None:
    pytest.skip(
        "Pending deployed endpoint; this test will issue "
        "set_voucher_review_status with each blocked value and assert a "
        "matching refusal event lands in get_audit_trail."
    )
