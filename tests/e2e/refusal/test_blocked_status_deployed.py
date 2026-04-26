"""Deployed E2E refusal regression for blocked-status round-trip.

Source of truth: docs/testing-plan.md section 6 G5.
"""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.e2e


def test_deployed_blocked_status_values_refused_with_audit(mcp_base_url: str) -> None:
    pytest.skip(
        "Pending application Phase 4+ wiring of set_voucher_review_status "
        "and get_audit_trail. The deployed endpoint is present, but those "
        "tools currently return the Phase 1 not_implemented stub instead "
        "of refusal envelopes coupled to workflow_events."
    )
