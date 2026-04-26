"""E2E scenario S1: missing receipt + weak local-paper evidence (V-1002).

Source of truth: docs/testing-plan.md section 8 S1.
"""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.e2e


def test_e2e_missing_receipt_local_paper(mcp_base_url: str) -> None:
    pytest.skip(
        "Pending application Phase 2+ wiring of prepare_ao_review_brief, "
        "set_voucher_review_status, and get_audit_trail. The deployed "
        "endpoint and V-1002 seed are present, but tools currently return "
        "the Phase 1 not_implemented stub from tools/_common.py."
    )
