"""Contract tests for ``initialize``.

Source of truth: docs/testing-plan.md section 5.3.
"""

from __future__ import annotations

from ao_radar_mcp.server import build_server


def test_initialize_returns_configured_server_identity() -> None:
    server = build_server(server_name="ao-radar-mcp", server_version="0.1.0")
    payload = server.initialize()
    assert payload["serverInfo"] == {"name": "ao-radar-mcp", "version": "0.1.0"}
    assert "capabilities" in payload
    assert payload["capabilities"]["tools"]["listChanged"] is False
    assert "boundary_reminder" in payload
    assert payload["boundary_reminder"].startswith(
        "AO Radar is a synthetic pre-decision review aid"
    )
