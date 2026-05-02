from __future__ import annotations

import json
import unittest

from policy_bonfire.live_adapters.anthropic_messages import AnthropicMessagesAdapter
from policy_bonfire.live_contracts import (
    LiveModelRequest,
    STATUS_COMPLETED_VALID,
    STATUS_EXCLUDED_FENCED_JSON,
    STATUS_EXCLUDED_MALFORMED_JSON,
    STATUS_EXCLUDED_TRUNCATED,
    STATUS_PROVIDER_SAFETY_REFUSAL,
    decision_envelope_json_schema,
)


def envelope_text() -> str:
    return json.dumps(
        {
            "recommendation": "refuse",
            "confidence": "medium",
            "evidence_used": [{"doc_id": "DOC-1"}],
            "policy_anchor_ids": ["A-1"],
            "rationale": "Synthetic refusal rationale.",
            "human_review_required": True,
            "pre_finalization_stop_path": "Stop path.",
            "fake_action_requested": "fake_notify_caseworker",
            "refusal": {"refused": True, "named_policy_basis_anchor_ids": ["A-1"]},
        }
    )


def request() -> LiveModelRequest:
    return LiveModelRequest(
        capture_id="cap",
        scenario_id="scen",
        scenario_hash="hash",
        anchor_ids=("A-1",),
        allowed_evidence_ids=("DOC-1",),
        prompt_variant_id="variant",
        prompt_template_hash="tmpl",
        rendered_prompt_hash="rendered",
        trusted_instructions="trusted anthropic system",
        untrusted_packet_block="synthetic untrusted packet",
        decision_schema_version="v1",
        decision_schema=decision_envelope_json_schema(),
        max_output_tokens=222,
        temperature=0,
    )


class FakeMessages:
    def __init__(self, response):
        self.response = response
        self.payloads = []

    def create(self, **payload):
        self.payloads.append(payload)
        return self.response


class FakeClient:
    def __init__(self, response):
        self.messages = FakeMessages(response)


class AnthropicMessagesAdapterTests(unittest.TestCase):
    def complete_with(self, response):
        client = FakeClient(response)
        adapter = AnthropicMessagesAdapter(client=client, model_id="claude-test", model_label="haiku", model_family="claude")
        return adapter.complete(request()), client.messages.payloads[0]

    def test_payload_shape_uses_messages_contract_and_no_tools(self):
        result, payload = self.complete_with(
            {"content": [{"type": "text", "text": envelope_text()}], "stop_reason": "end_turn", "usage": {"input_tokens": 11, "output_tokens": 22}}
        )
        self.assertEqual(STATUS_COMPLETED_VALID, result.status)
        self.assertEqual("anthropic", result.provider)
        self.assertTrue(payload["system"].startswith("trusted anthropic system"))
        self.assertEqual([{"role": "user", "content": "synthetic untrusted packet"}], payload["messages"])
        self.assertEqual(222, payload["max_tokens"])
        self.assertIn("Return exactly one JSON object", payload["system"])
        self.assertEqual(
            {
                "format": {
                    "type": "json_schema",
                    "name": "policy_bonfire_decision_envelope",
                    "schema": request().decision_schema,
                }
            },
            payload["output_config"],
        )
        self.assertNotIn("tools", payload)
        self.assertEqual("refuse", result.parsed_decision_envelope["recommendation"])
        self.assertFalse(result.usage_estimated)

    def test_response_statuses_and_missing_usage(self):
        cases = [
            ({"content": [{"type": "text", "text": ""}], "stop_reason": "safety"}, STATUS_PROVIDER_SAFETY_REFUSAL),
            ({"content": [{"type": "tool_use", "name": "not_allowed"}], "stop_reason": "end_turn"}, STATUS_EXCLUDED_MALFORMED_JSON),
            ({"content": [{"type": "text", "text": "not json"}], "stop_reason": "end_turn"}, STATUS_EXCLUDED_MALFORMED_JSON),
            ({"content": [{"type": "text", "text": "```json\n{}\n```"}], "stop_reason": "end_turn"}, STATUS_EXCLUDED_FENCED_JSON),
            ({"content": [{"type": "text", "text": envelope_text()}], "stop_reason": "max_tokens"}, STATUS_EXCLUDED_TRUNCATED),
            ({"content": [{"type": "text", "text": envelope_text()}], "stop_reason": "end_turn"}, STATUS_COMPLETED_VALID),
        ]
        for raw, status in cases:
            result, _ = self.complete_with(raw)
            self.assertEqual(status, result.status)
        missing_usage, _ = self.complete_with({"content": [{"type": "text", "text": envelope_text()}], "stop_reason": "end_turn"})
        self.assertTrue(missing_usage.usage_estimated)


if __name__ == "__main__":
    unittest.main()
