from __future__ import annotations

import json
import unittest

from policy_bonfire.live_adapters.google_gemini import GoogleGeminiAdapter
from policy_bonfire.live_contracts import (
    LiveModelRequest,
    STATUS_COMPLETED_VALID,
    STATUS_EXCLUDED_FENCED_JSON,
    STATUS_EXCLUDED_MALFORMED_JSON,
    STATUS_EXCLUDED_TRUNCATED,
    STATUS_PROVIDER_NO_CANDIDATE,
    STATUS_PROVIDER_SAFETY_REFUSAL,
    decision_envelope_json_schema,
)


def envelope_text() -> str:
    return json.dumps(
        {
            "recommendation": "approve",
            "confidence": "low",
            "evidence_used": [{"doc_id": "DOC-1"}],
            "policy_anchor_ids": ["A-1"],
            "rationale": "Synthetic rationale.",
            "human_review_required": False,
            "pre_finalization_stop_path": None,
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
        trusted_instructions="trusted gemini system",
        untrusted_packet_block="gemini untrusted packet",
        decision_schema_version="v1",
        decision_schema=decision_envelope_json_schema(),
        max_output_tokens=111,
        temperature=0,
    )


class FakeModels:
    def __init__(self, response):
        self.response = response
        self.payloads = []

    def generate_content(self, **payload):
        self.payloads.append(payload)
        return self.response


class FakeClient:
    def __init__(self, response):
        self.models = FakeModels(response)


def candidate(text: str | None = None, *, finish="STOP", parts=None, safety=None):
    if parts is None:
        parts = [{"text": text}]
    return {"content": {"parts": parts}, "finishReason": finish, "safetyRatings": safety or []}


class GoogleGeminiAdapterTests(unittest.TestCase):
    def complete_with(self, response):
        client = FakeClient(response)
        adapter = GoogleGeminiAdapter(client=client, model_id="gemini-test", model_label="flash-lite", model_family="gemini")
        return adapter.complete(request()), client.models.payloads[0]

    def test_payload_shape_uses_generate_content_contract_and_no_tools(self):
        result, payload = self.complete_with(
            {"candidates": [candidate(envelope_text())], "usageMetadata": {"promptTokenCount": 12, "candidatesTokenCount": 24}}
        )
        self.assertEqual(STATUS_COMPLETED_VALID, result.status)
        self.assertEqual("google", result.provider)
        self.assertEqual("gemini-test", payload["model"])
        self.assertEqual({"parts": [{"text": "trusted gemini system"}]}, payload["systemInstruction"])
        self.assertEqual([{"role": "user", "parts": [{"text": "gemini untrusted packet"}]}], payload["contents"])
        self.assertEqual("application/json", payload["generationConfig"]["responseMimeType"])
        self.assertEqual(111, payload["generationConfig"]["maxOutputTokens"])
        self.assertIn("responseSchema", payload["generationConfig"])
        for forbidden in ("tools", "toolConfig", "functionDeclarations", "codeExecution", "googleSearch", "retrieval", "grounding"):
            self.assertNotIn(forbidden, payload)
        self.assertEqual("approve", result.parsed_decision_envelope["recommendation"])
        self.assertFalse(result.usage_estimated)

    def test_response_statuses_and_missing_usage(self):
        cases = [
            ({"candidates": []}, STATUS_PROVIDER_NO_CANDIDATE),
            ({"promptFeedback": {"blockReason": "SAFETY"}, "candidates": []}, STATUS_PROVIDER_SAFETY_REFUSAL),
            ({"candidates": [candidate(envelope_text(), safety=[{"blocked": True}])]}, STATUS_PROVIDER_SAFETY_REFUSAL),
            ({"candidates": [candidate(parts=[{"functionCall": {"name": "not_allowed"}}])]}, STATUS_EXCLUDED_MALFORMED_JSON),
            ({"candidates": [candidate("not json")]}, STATUS_EXCLUDED_MALFORMED_JSON),
            ({"candidates": [candidate("```json\n{}\n```")]}, STATUS_EXCLUDED_FENCED_JSON),
            ({"candidates": [candidate(envelope_text(), finish="MAX_TOKENS")]}, STATUS_EXCLUDED_TRUNCATED),
            ({"candidates": [candidate(envelope_text())]}, STATUS_COMPLETED_VALID),
        ]
        for raw, status in cases:
            result, _ = self.complete_with(raw)
            self.assertEqual(status, result.status)
        missing_usage, _ = self.complete_with({"candidates": [candidate(envelope_text())]})
        self.assertTrue(missing_usage.usage_estimated)


if __name__ == "__main__":
    unittest.main()
