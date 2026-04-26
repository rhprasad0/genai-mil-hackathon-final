"""E2E scenario S3: OCONUS cash / exchange-rate reconstruction (V-1007).

Source of truth: docs/testing-plan.md section 8 S3.

The seeded V-1007 brief carries a ``cash_atm_or_exchange_reconstruction``
finding flagged ``needs_human_review = true`` and a high overall brief
uncertainty.
"""

from __future__ import annotations

import pytest

from .._jsonrpc import call_tool

pytestmark = pytest.mark.e2e

_VOUCHER_ID = "V-1007"


def test_e2e_oconus_cash_exchange_rate(mcp_base_url: str) -> None:
    brief_response = call_tool(
        mcp_base_url,
        "prepare_ao_review_brief",
        {"voucher_id": _VOUCHER_ID, "actor_label": "ao-radar-e2e"},
    )
    assert brief_response["status"] == "ok", brief_response
    assert brief_response["voucher"]["voucher_id"] == _VOUCHER_ID
    assert brief_response["brief"]["brief_uncertainty"] == "high"

    findings_by_category = {f["category"]: f for f in brief_response["findings"]}
    assert "cash_atm_or_exchange_reconstruction" in findings_by_category, findings_by_category
    cash_finding = findings_by_category["cash_atm_or_exchange_reconstruction"]
    assert cash_finding["needs_human_review"] is True, cash_finding
    assert cash_finding["review_prompt_only"] is True
