from __future__ import annotations

import json
import unittest

from policy_bonfire.live_adapters.base import AdapterTimeoutError, AdapterTransientError
from policy_bonfire.live_adapters.openai_responses import OpenAIResponsesAdapter
from policy_bonfire.live_contracts import (
    LiveModelRequest,
    STATUS_COMPLETED_VALID,
    STATUS_EXCLUDED_FENCED_JSON,
    STATUS_EXCLUDED_MALFORMED_JSON,
    STATUS_EXCLUDED_TRUNCATED,
    STATUS_PROVIDER_SAFETY_REFUSAL,
    STATUS_TIMEOUT,
    STATUS_TRANSIENT_ERROR,
    decision_envelope_json_schema,
)


def envelope_text() -> str:
    return json.dumps(
        {
            "recommendation": "escalate",
            "confidence": "high",
            "evidence_used": [{"doc_id": "DOC-1"}],
            "policy_anchor_ids": ["A-1"],
            "rationale": "Synthetic rationale.",
            "human_review_required": True,
            "pre_finalization_stop_path": "Stop before external action.",
            "fake_action_requested": "fake_notify_caseworker",
            "refusal": {"refused": False, "named_policy_basis_anchor_ids": []},
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
        trusted_instructions="trusted system only",
        untrusted_packet_block="<UNTRUSTED>packet</UNTRUSTED>",
        decision_schema_version="v1",
        decision_schema=decision_envelope_json_schema(),
        max_output_tokens=321,
        temperature=0,
    )


class FakeResponses:
    def __init__(self, response=None, exc: Exception | None = None):
        self.response = response
        self.exc = exc
        self.payloads = []

    def create(self, **payload):
        self.payloads.append(payload)
        if self.exc:
            raise self.exc
        return self.response


class FakeClient:
    def __init__(self, response=None, exc: Exception | None = None):
        self.responses = FakeResponses(response, exc)


class OpenAIResponsesAdapterTests(unittest.TestCase):
    def complete_with(self, response=None, exc: Exception | None = None):
        client = FakeClient(response, exc)
        adapter = OpenAIResponsesAdapter(client=client, model_id="o-test", model_label="mini", model_family="openai")
        return adapter.complete(request()), client.responses.payloads[0] if client.responses.payloads else None

    def test_payload_shape_uses_responses_contract_and_no_tools(self):
        result, payload = self.complete_with(
            {"output_text": envelope_text(), "finish_reason": "stop", "usage": {"input_tokens": 10, "output_tokens": 20}}
        )
        self.assertEqual(STATUS_COMPLETED_VALID, result.status)
        self.assertEqual("openai", result.provider)
        self.assertEqual("trusted system only", payload["instructions"])
        self.assertEqual("<UNTRUSTED>packet</UNTRUSTED>", payload["input"])
        self.assertIs(payload["store"], False)
        self.assertEqual("json_schema", payload["text"]["format"]["type"])
        self.assertEqual(321, payload["max_output_tokens"])
        self.assertNotIn("tools", payload)
        self.assertIsNotNone(result.raw_output_sha256)
        self.assertNotIn("Synthetic rationale", result.raw_output_sha256)
        self.assertEqual("escalate", result.parsed_decision_envelope["recommendation"])
        self.assertFalse(result.usage_estimated)

    def test_refusal_malformed_fenced_truncated_and_missing_usage(self):
        cases = [
            ({"output_text": "", "finish_reason": "refusal"}, STATUS_PROVIDER_SAFETY_REFUSAL),
            ({"output_text": "not json", "finish_reason": "stop"}, STATUS_EXCLUDED_MALFORMED_JSON),
            ({"output_text": "```json\n{}\n```", "finish_reason": "stop"}, STATUS_EXCLUDED_FENCED_JSON),
            ({"output_text": envelope_text(), "status": "incomplete", "incomplete_details": {"reason": "max_tokens"}}, STATUS_EXCLUDED_TRUNCATED),
            ({"output_text": envelope_text(), "finish_reason": "stop"}, STATUS_COMPLETED_VALID),
        ]
        for raw, status in cases:
            result, _ = self.complete_with(raw)
            self.assertEqual(status, result.status)
        missing_usage, _ = self.complete_with({"output_text": envelope_text(), "finish_reason": "stop"})
        self.assertTrue(missing_usage.usage_estimated)

    def test_timeout_and_transient_errors_are_normalized(self):
        timeout, _ = self.complete_with(exc=AdapterTimeoutError("deadline exceeded: secret request id omitted"))
        transient, _ = self.complete_with(exc=AdapterTransientError("500"))
        self.assertEqual(STATUS_TIMEOUT, timeout.status)
        self.assertEqual("timeout", timeout.error_code_redacted)
        self.assertEqual(STATUS_TRANSIENT_ERROR, transient.status)
        self.assertEqual("transient_error", transient.error_code_redacted)


if __name__ == "__main__":
    unittest.main()
