"""Deployed E2E test for ``GET /health``.

Source of truth: docs/testing-plan.md section 5.6 (G1).

Skipped automatically when ``AO_RADAR_MCP_BASE_URL`` is unset (per the lead's
``conftest.py``).
"""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.e2e


def test_deployed_health_returns_200(mcp_base_url: str) -> None:
    pytest.skip(
        "Pending deployed endpoint; this test will fetch GET /health "
        "and assert ok / server / version using urllib.request."
    )
