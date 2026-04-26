"""Deployed E2E test for ``initialize`` over the wire.

Source of truth: docs/testing-plan.md section 5.6 (G1).
"""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.e2e


def test_deployed_initialize_returns_server_identity(mcp_base_url: str) -> None:
    pytest.skip(
        "Pending deployed endpoint; this test will POST a JSON-RPC "
        "initialize request and assert serverInfo + capabilities."
    )
