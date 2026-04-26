"""E2E scenario S2: ambiguous LOA / mis-click / bad math (V-1004).

Source of truth: docs/testing-plan.md section 8 S2.
"""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.e2e


def test_e2e_ambiguous_loa_misclick_math(mcp_base_url: str) -> None:
    pytest.skip(
        "Pending application Phase 2+ wiring of prepare_ao_review_brief and "
        "record_ao_note. The deployed endpoint and V-1004 seed are present, "
        "but tools currently return the Phase 1 not_implemented stub."
    )
