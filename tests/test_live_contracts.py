from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from policy_bonfire.anchors import load_anchor_manifest
from policy_bonfire.decision_schema import DECISION_SCHEMA_VERSION, REQUIRED_DECISION_FIELDS, build_decision_envelope_schema
from policy_bonfire.live_contracts import (
    ALLOWED_LIVE_STATUSES,
    ALLOWED_PROVIDERS,
    MODEL_FAMILY_LABELS,
    STATUS_COMPLETED_VALID,
    LiveModelRequest,
    LiveModelResponse,
)
from policy_bonfire.prompts import load_prompt_variants, render_prompt, split_trusted_untrusted_blocks
from policy_bonfire.scenarios import load_scenarios

from tests.helpers import copy_live_test_data


def _load_live_test_inputs():
    with tempfile.TemporaryDirectory() as tmp:
        data_dir = copy_live_test_data(Path(tmp), scenario_limit=3)
        anchors = load_anchor_manifest(data_dir / "policy_anchors" / "mock_v1_anchors.json")
        scenarios = load_scenarios(data_dir / "scenarios", anchors)
        variants = load_prompt_variants(data_dir / "prompts" / "pilot_variants.json")
        return scenarios, variants


class LiveContractTests(unittest.TestCase):
    def test_allowed_status_and_provider_sets_include_required_values(self):
        self.assertEqual({"openai", "anthropic", "google"}, set(ALLOWED_PROVIDERS))
        for status in (
            "completed_valid",
            "provider_safety_refusal",
            "provider_no_candidate",
            "excluded_malformed_json",
            "excluded_fenced_json",
            "excluded_truncated",
            "excluded_schema_invalid",
            "provider_skipped_missing_key",
            "provider_skipped_model_unavailable",
            "provider_skipped_missing_rate",
            "blocked_cost_cap",
            "timeout",
            "transient_error",
            "sandbox_unverified",
            "live_calls_not_enabled",
        ):
            self.assertIn(status, ALLOWED_LIVE_STATUSES)

    def test_decision_schema_contains_existing_required_envelope_fields(self):
        schema = build_decision_envelope_schema()
        self.assertEqual(DECISION_SCHEMA_VERSION, schema["$id"])
        self.assertEqual(set(REQUIRED_DECISION_FIELDS), set(schema["required"]))
        props = schema["properties"]
        for field in REQUIRED_DECISION_FIELDS:
            self.assertIn(field, props)
        self.assertIn("approve", props["recommendation"]["enum"])
        self.assertIn("refuse", props["recommendation"]["enum"])
        self.assertIn("doc_id", props["evidence_used"]["items"]["properties"])
        self.assertIn("named_policy_basis_anchor_ids", props["refusal"]["properties"])
        self.assertFalse(schema["additionalProperties"])
        self.assertFalse(props["evidence_used"]["items"]["additionalProperties"])
        self.assertEqual({"doc_id", "summary"}, set(props["evidence_used"]["items"]["required"]))
        self.assertFalse(props["refusal"]["additionalProperties"])
        self.assertEqual({"refused", "reason", "named_policy_basis_anchor_ids"}, set(props["refusal"]["required"]))

    def test_decision_schema_can_constrain_policy_and_evidence_ids_per_scenario(self):
        schema = build_decision_envelope_schema(
            allowed_policy_anchor_ids=("DOD-RAI-TRACEABLE", "DOD-RAI-RELIABLE"),
            allowed_evidence_ids=("DOC-201", "DOC-202"),
        )
        props = schema["properties"]
        self.assertEqual(["DOC-201", "DOC-202"], props["evidence_used"]["items"]["properties"]["doc_id"]["enum"])
        self.assertEqual(["DOD-RAI-RELIABLE", "DOD-RAI-TRACEABLE"], props["policy_anchor_ids"]["items"]["enum"])
        self.assertEqual(
            ["DOD-RAI-RELIABLE", "DOD-RAI-TRACEABLE"],
            props["refusal"]["properties"]["named_policy_basis_anchor_ids"]["items"]["enum"],
        )

    def test_provider_trusted_instructions_include_scenario_citable_units(self):
        scenarios, variants = _load_live_test_inputs()
        rendered = render_prompt(variants[0], scenarios[1])
        blocks = split_trusted_untrusted_blocks(rendered.rendered_prompt)
        self.assertIn("<TRUSTED_SCENARIO>", blocks.trusted_instructions)
        self.assertIn("Policy anchors: DOD-RAI-TRACEABLE, DOD-RAI-RELIABLE", blocks.trusted_instructions)
        self.assertIn("DOC-PL-002-A", blocks.trusted_instructions)
        self.assertIn("Never invent policy anchor IDs", blocks.trusted_instructions)
        self.assertNotIn("<UNTRUSTED_PACKET>", blocks.trusted_instructions)

    def test_request_response_are_provider_neutral_dataclasses(self):
        scenarios, variants = _load_live_test_inputs()
        rendered = render_prompt(variants[0], scenarios[0])
        blocks = split_trusted_untrusted_blocks(rendered.rendered_prompt)
        schema = build_decision_envelope_schema()
        req = LiveModelRequest(
            capture_id="cap-001",
            scenario_id=scenarios[0].scenario_id,
            scenario_hash=scenarios[0].card_hash,
            anchor_ids=scenarios[0].policy_anchors,
            prompt_variant_id=variants[0].prompt_variant_id,
            prompt_template_hash=variants[0].prompt_template_hash,
            rendered_prompt_hash=rendered.rendered_prompt_hash,
            trusted_instructions=blocks.trusted_instructions,
            untrusted_packet_block=blocks.untrusted_packet_block,
            decision_schema_version=DECISION_SCHEMA_VERSION,
            decision_schema=schema,
            max_output_tokens=800,
            cost_cap_context={"projected_usd": 0.01},
        )
        self.assertNotIn("API_KEY", repr(req))
        self.assertEqual("rep_001", req.repetition_id)
        self.assertNotIn("<UNTRUSTED_PACKET>", req.trusted_instructions)
        self.assertIn("<UNTRUSTED_PACKET>", req.untrusted_packet_block)
        resp = LiveModelResponse(
            status=STATUS_COMPLETED_VALID,
            provider="openai",
            model_id_exact="YOUR_MODEL_ID_HERE",
            model_id_public_label="cheap mini tier",
            model_family=MODEL_FAMILY_LABELS["openai"],
            parsed_decision_envelope={"recommendation": "escalate"},
        )
        self.assertEqual("openai_lineage", resp.model_family)


if __name__ == "__main__":
    unittest.main()
