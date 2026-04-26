"""Deployed E2E test for ``tools/list`` over the wire.

Source of truth: docs/testing-plan.md section 5.6 (G1, G2).
"""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.e2e


def test_deployed_tools_list_returns_full_catalog(mcp_base_url: str) -> None:
    pytest.skip(
        "Pending deployed endpoint; this test will POST a JSON-RPC "
        "tools/list and assert the response equals the spec catalog "
        "exactly and excludes generic-data-access patterns."
    )
