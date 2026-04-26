"""E2E scenario S4: stale-memory old transaction (V-1006).

Source of truth: docs/testing-plan.md section 8 S4.
"""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.e2e


def test_e2e_stale_memory_old_transaction(mcp_base_url: str) -> None:
    pytest.skip(
        "Pending application Phase 2+ wiring of prepare_ao_review_brief. "
        "The deployed endpoint and V-1006 seed are present, but tools "
        "currently return the Phase 1 not_implemented stub."
    )
