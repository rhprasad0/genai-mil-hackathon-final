"""Deployed E2E test for ``GET /health``.

Source of truth: docs/testing-plan.md section 5.6 (G1) and
docs/application-implementation-plan.md section 12 (health response shape).

Skipped automatically when ``AO_RADAR_MCP_BASE_URL`` is unset (per the lead's
``conftest.py``).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

import pytest


pytestmark = pytest.mark.e2e

_TIMEOUT_S = 15.0


def test_deployed_health_returns_200(mcp_base_url: str) -> None:
    """``GET /health`` returns a small JSON envelope with ``ok``, ``server``, ``version``."""

    url = f"{mcp_base_url}/health"
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_S) as response:
            status = response.status
            body_bytes = response.read()
            content_type = response.headers.get("Content-Type", "")
    except urllib.error.URLError as exc:  # pragma: no cover - exercised only on outage
        pytest.fail(f"deployed health endpoint unreachable: {exc!r}")

    assert status == 200, f"expected 200 from /health, got {status}"
    assert "application/json" in content_type, (
        f"expected JSON content-type from /health, got {content_type!r}"
    )

    body = json.loads(body_bytes.decode("utf-8"))
    assert body.get("ok") is True, body
    assert isinstance(body.get("server"), str) and body["server"], body
    assert "ao-radar" in body["server"].lower(), body
    assert isinstance(body.get("version"), str) and body["version"], body
