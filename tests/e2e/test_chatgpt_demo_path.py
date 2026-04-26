"""Deployed E2E walk of the live ChatGPT Apps demo prompt path.

Walks the same sequence a judge sees:

  initialize -> tools/list -> list_vouchers_awaiting_action ->
  prepare_ao_review_brief -> get_voucher_packet ->
  get_policy_citation -> draft_return_comment ->
  set_voucher_review_status (blocked / refused) -> get_audit_trail.

Asserts that:
  * No tool on the demo path returns ``status = not_implemented``.
  * Every ``tools/call`` response uses standard MCP content blocks
    (``type`` in {``text``, ``image``, ``resource``, ``audio``}); no
    non-standard ``type = "json"`` block, which previously produced
    ``UNKNOWN`` / ``TaskGroup`` errors in the ChatGPT remote-MCP client.
  * The blocked-status step still refuses with a refusal envelope.
  * The refusal lands in the audit trail keyed to the voucher.
"""

from __future__ import annotations

import json

import pytest

from ._jsonrpc import call_tool, post_jsonrpc

pytestmark = pytest.mark.e2e

_VALID_CONTENT_TYPES = {"text", "image", "resource", "audio"}


def _assert_standard_content(result_envelope: dict, *, label: str) -> None:
    content = result_envelope.get("content")
    assert isinstance(content, list) and content, (
        f"{label}: tools/call result has no content blocks: {result_envelope!r}"
    )
    for block in content:
        assert isinstance(block, dict), f"{label}: bad content block {block!r}"
        block_type = block.get("type")
        assert block_type in _VALID_CONTENT_TYPES, (
            f"{label}: non-standard MCP content block type {block_type!r} "
            f"(ChatGPT Apps client expects one of {sorted(_VALID_CONTENT_TYPES)})"
        )
        if block_type == "text":
            assert isinstance(block.get("text"), str), block


def _call_with_envelope(
    base_url: str, tool_name: str, arguments: dict, *, request_id: str
) -> tuple[dict, dict]:
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }
    response = post_jsonrpc(base_url, payload)
    assert "error" not in response, response
    result = response["result"]
    _assert_standard_content(result, label=tool_name)
    structured = result.get("structuredContent") or json.loads(
        result["content"][0]["text"]
    )
    assert isinstance(structured, dict), result
    return result, structured


def test_chatgpt_demo_prompt_path(mcp_base_url: str) -> None:
    init = post_jsonrpc(
        mcp_base_url,
        {
            "jsonrpc": "2.0",
            "id": "demo-init",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "ao-radar-demo-e2e", "version": "0.1.0"},
            },
        },
    )
    assert "error" not in init, init
    assert "boundary_reminder" in init["result"], init

    tools_list = post_jsonrpc(
        mcp_base_url,
        {"jsonrpc": "2.0", "id": "demo-tools", "method": "tools/list", "params": {}},
    )
    assert "error" not in tools_list, tools_list
    advertised = {tool["name"] for tool in tools_list["result"]["tools"]}
    for required in (
        "list_vouchers_awaiting_action",
        "prepare_ao_review_brief",
        "get_voucher_packet",
        "get_policy_citation",
        "draft_return_comment",
        "set_voucher_review_status",
        "get_audit_trail",
    ):
        assert required in advertised, advertised

    _, queue = _call_with_envelope(
        mcp_base_url, "list_vouchers_awaiting_action", {"limit": 5}, request_id="demo-queue"
    )
    assert queue["status"] == "ok", queue
    assert queue["status"] != "not_implemented", queue
    assert queue["count"] >= 1, queue
    illustrative = queue["queue"][0]
    voucher_id = illustrative["voucher_id"]
    assert isinstance(voucher_id, str) and voucher_id.startswith("V-"), illustrative
    assert "review_difficulty" in illustrative, illustrative
    assert "illustration_hint" in illustrative, illustrative
    assert "approving official" in queue["boundary_reminder"].lower()

    _, brief = _call_with_envelope(
        mcp_base_url,
        "prepare_ao_review_brief",
        {"voucher_id": voucher_id, "actor_label": "ao-radar-demo-e2e"},
        request_id="demo-brief",
    )
    assert brief["status"] == "ok", brief
    assert brief["audit_event_type"] in {"retrieval", "generation"}
    finding_categories = [f["category"] for f in brief["findings"]]
    assert "boundary_reminder" in brief

    _, packet = _call_with_envelope(
        mcp_base_url,
        "get_voucher_packet",
        {"voucher_id": voucher_id},
        request_id="demo-packet",
    )
    assert packet["status"] == "ok", packet
    assert packet["voucher"]["voucher_id"] == voucher_id
    assert isinstance(packet["line_items"], list), packet
    assert packet["review_prompt_only"] is True

    citation_id = (
        brief["findings"][0].get("primary_citation_id") if finding_categories else None
    ) or "CITE-RECEIPT-001"
    _, citation = _call_with_envelope(
        mcp_base_url,
        "get_policy_citation",
        {"citation_id": citation_id},
        request_id="demo-citation",
    )
    assert citation["status"] == "ok", citation
    assert citation["citation"]["citation_id"] == citation_id
    assert "(Synthetic Demo Reference)" in citation["citation"]["excerpt_text"]

    draft_text = (
        "Could you share the supporting receipts for the line items flagged "
        "in the synthetic packet so the reviewer can reconstruct the trip? "
        "Synthetic demo draft only."
    )
    _, draft = _call_with_envelope(
        mcp_base_url,
        "draft_return_comment",
        {
            "voucher_id": voucher_id,
            "text": draft_text,
            "actor_label": "ao-radar-demo-e2e",
        },
        request_id="demo-draft",
    )
    assert draft["status"] == "ok", draft
    assert draft["draft"]["kind"] == "draft_clarification"
    assert "Nothing was sent" in draft["advisory"]

    _, refusal = _call_with_envelope(
        mcp_base_url,
        "set_voucher_review_status",
        {
            "voucher_id": voucher_id,
            "status": "approved",
            "actor_label": "ao-radar-demo-e2e",
        },
        request_id="demo-refusal",
    )
    assert refusal["refused"] is True, refusal
    assert refusal["reason"] == "prohibited_action", refusal
    assert refusal.get("audit_event_type") == "refusal"
    refusal_event_id = refusal.get("audit_event_id")
    assert isinstance(refusal_event_id, str) and refusal_event_id, refusal

    _, audit = _call_with_envelope(
        mcp_base_url,
        "get_audit_trail",
        {"voucher_id": voucher_id},
        request_id="demo-audit",
    )
    assert audit["status"] == "ok", audit
    audit_event_ids = {event["event_id"] for event in audit["events"]}
    assert refusal_event_id in audit_event_ids, audit
    matched = next(
        event for event in audit["events"] if event["event_id"] == refusal_event_id
    )
    assert matched["event_type"] == "refusal"
    assert matched["tool_name"] == "set_voucher_review_status"
    assert matched["target_kind"] == "voucher"
    assert "approving official" in matched["human_authority_boundary_reminder"].lower()


def test_no_tool_on_demo_path_returns_not_implemented(mcp_base_url: str) -> None:
    """Regression: every tool the demo prompt traverses must be wired."""

    cases = [
        ("list_vouchers_awaiting_action", {"limit": 5}),
        ("get_voucher_packet", {"voucher_id": "V-1001"}),
        ("prepare_ao_review_brief", {"voucher_id": "V-1001"}),
        ("get_policy_citation", {"citation_id": "CITE-RECEIPT-001"}),
        ("get_policy_citations", {"query": "lodging"}),
        ("get_audit_trail", {"voucher_id": "V-1001"}),
    ]
    for tool_name, arguments in cases:
        structured = call_tool(
            mcp_base_url, tool_name, arguments, request_id=f"reg-{tool_name}"
        )
        assert structured.get("status") != "not_implemented", (
            tool_name,
            structured,
        )
