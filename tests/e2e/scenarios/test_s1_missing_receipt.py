"""E2E scenario S1: missing receipt + weak local-paper evidence (V-1002).

Source of truth: docs/testing-plan.md section 8 S1.
"""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.e2e


def test_e2e_missing_receipt_local_paper(mcp_base_url: str) -> None:
    pytest.skip(
        "Pending deployed endpoint + seeded V-1002; this scenario walks "
        "prepare_ao_review_brief, set_voucher_review_status, and "
        "get_audit_trail end-to-end."
    )
