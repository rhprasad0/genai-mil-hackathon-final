from __future__ import annotations

import json
import unittest

from policy_bonfire.live_contracts import (
    STATUS_COMPLETED_VALID,
    STATUS_EXCLUDED_FENCED_JSON,
    STATUS_EXCLUDED_MALFORMED_JSON,
    STATUS_EXCLUDED_SCHEMA_INVALID,
    STATUS_EXCLUDED_TRUNCATED,
    STATUS_PROVIDER_SAFETY_REFUSAL,
)
from policy_bonfire.live_json import (
    build_bounded_repair_prompt,
    parse_strict_decision_json,
    parse_with_optional_repair,
)
from policy_bonfire.mock_specimen import lookup_envelope
from policy_bonfire.types import stable_json

from tests.helpers import load_all


class LiveJsonTests(unittest.TestCase):
    def setUp(self):
        _, scenarios, prompts, canned = load_all()
        self.scenario = scenarios[0]
        self.prompt = prompts[0]
        self.valid_envelope = lookup_envelope(canned, self.scenario.scenario_id, self.prompt.prompt_variant_id)
        self.valid_json = stable_json(self.valid_envelope)

    def test_strict_json_validates_local_decision_envelope(self):
        result = parse_strict_decision_json(self.valid_json, self.scenario)
        self.assertEqual(STATUS_COMPLETED_VALID, result.status)
        self.assertEqual(self.valid_envelope["recommendation"], result.parsed_decision_envelope["recommendation"])
        self.assertIsNotNone(result.raw_output_sha256)

    def test_fenced_json_is_classified_not_soft_parsed(self):
        result = parse_strict_decision_json("```json\n" + self.valid_json + "\n```", self.scenario)
        self.assertEqual(STATUS_EXCLUDED_FENCED_JSON, result.status)
        self.assertIsNone(result.parsed_decision_envelope)

    def test_prose_wrapped_and_malformed_json_are_excluded(self):
        prose = parse_strict_decision_json("Here is JSON: " + self.valid_json, self.scenario)
        self.assertEqual(STATUS_EXCLUDED_MALFORMED_JSON, prose.status)
        malformed = parse_strict_decision_json('{"recommendation": ', self.scenario)
        self.assertEqual(STATUS_EXCLUDED_MALFORMED_JSON, malformed.status)

    def test_truncation_and_refusal_finish_reasons_are_not_repaired(self):
        calls = []

        def repair(prompt: str) -> str:
            calls.append(prompt)
            return self.valid_json

        truncated = parse_with_optional_repair(
            '{"recommendation":',
            self.scenario,
            original_prompt_hash="abc123",
            schema_instruction="Use the decision envelope schema.",
            repair_call=repair,
            finish_reason="length",
        )
        self.assertEqual(STATUS_EXCLUDED_TRUNCATED, truncated.status)
        refusal = parse_with_optional_repair(
            None,
            self.scenario,
            original_prompt_hash="abc123",
            schema_instruction="Use the decision envelope schema.",
            repair_call=repair,
            finish_reason="safety",
        )
        self.assertEqual(STATUS_PROVIDER_SAFETY_REFUSAL, refusal.status)
        self.assertEqual([], calls)

    def test_schema_invalid_can_use_one_bounded_repair_turn(self):
        invalid = dict(self.valid_envelope)
        invalid.pop("rationale")
        prompts_seen = []

        def repair(prompt: str) -> str:
            prompts_seen.append(prompt)
            return self.valid_json

        raw_invalid = json.dumps(invalid)
        result = parse_with_optional_repair(
            raw_invalid,
            self.scenario,
            original_prompt_hash="hash-only-not-prompt",
            schema_instruction="Return only a valid decision envelope JSON object.",
            repair_call=repair,
        )
        self.assertEqual(STATUS_COMPLETED_VALID, result.status)
        self.assertTrue(result.repair_attempted)
        self.assertEqual(1, len(prompts_seen))
        repair_prompt = prompts_seen[0]
        self.assertIn("hash-only-not-prompt", repair_prompt)
        self.assertIn("schema_invalid", repair_prompt)
        self.assertNotIn(raw_invalid, repair_prompt)
        self.assertNotIn("judge", repair_prompt.lower())
        self.assertNotIn("score", repair_prompt.lower())

    def test_repair_prompt_contains_only_bounded_context(self):
        prompt = build_bounded_repair_prompt(
            original_prompt_hash="abc123",
            validation_error_class="json_decode_error",
            schema_instruction="Return JSON matching schema version v1.",
        )
        self.assertIn("abc123", prompt)
        self.assertIn("json_decode_error", prompt)
        self.assertIn("Return JSON matching schema version v1.", prompt)
        self.assertNotIn("malformed output", prompt.lower())
        self.assertNotIn("evaluator", prompt.lower())

    def test_invalid_schema_without_repair_is_excluded(self):
        invalid = dict(self.valid_envelope)
        invalid["policy_anchor_ids"] = ["invented"]
        result = parse_strict_decision_json(json.dumps(invalid), self.scenario)
        self.assertEqual(STATUS_EXCLUDED_SCHEMA_INVALID, result.status)


if __name__ == "__main__":
    unittest.main()
