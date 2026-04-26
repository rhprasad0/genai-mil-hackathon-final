"""Contract test for ``export_review_brief`` input schema.

Source of truth: docs/testing-plan.md section 5.3.
"""

from __future__ import annotations

from ao_radar_mcp.server import build_server


def test_export_review_brief_schema_accepts_voucher_or_brief_id() -> None:
    server = build_server(server_name="ao-radar-mcp", server_version="0.1.0")
    schema = server.tools["export_review_brief"].input_schema
    properties = schema["properties"]
    assert "voucher_id" in properties
    assert "brief_id" in properties
    assert properties["format"]["enum"] == ["markdown", "json"]
    assert schema["additionalProperties"] is False
    assert {"required": ["voucher_id"]} in schema["anyOf"]
    assert {"required": ["brief_id"]} in schema["anyOf"]
