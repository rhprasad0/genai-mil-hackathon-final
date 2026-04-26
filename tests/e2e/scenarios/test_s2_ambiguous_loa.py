"""E2E scenario S2: ambiguous LOA / mis-click / bad math (V-1004).

Source of truth: docs/testing-plan.md section 8 S2.
"""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.e2e


def test_e2e_ambiguous_loa_misclick_math(mcp_base_url: str) -> None:
    pytest.skip(
        "Pending deployed endpoint + seeded V-1004; this scenario walks "
        "prepare_ao_review_brief and record_ao_note, asserting findings "
        "include ambiguous_loa_or_funding_reference, "
        "miscategorized_line_item, and paperwork_or_math_inconsistency."
    )
