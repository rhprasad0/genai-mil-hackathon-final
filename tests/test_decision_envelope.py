from __future__ import annotations

import copy
import unittest

from policy_bonfire.decision_envelope import validate_decision_envelope
from policy_bonfire.mock_specimen import lookup_envelope

from tests.helpers import load_all


class DecisionEnvelopeTests(unittest.TestCase):
    def test_canned_envelopes_validate(self):
        _, scenarios, prompts, canned = load_all()
        for scenario in scenarios:
            for prompt in prompts:
                envelope = lookup_envelope(canned, scenario.scenario_id, prompt.prompt_variant_id)
                result = validate_decision_envelope(envelope, scenario)
                self.assertTrue(result.valid, (scenario.scenario_id, prompt.prompt_variant_id, result.errors))

    def test_rejects_invented_anchor(self):
        _, scenarios, _, canned = load_all()
        envelope = lookup_envelope(canned, "PB-SCEN-001", "cautious_baseline")
        envelope["policy_anchor_ids"] = ["NOT-PROVIDED"]
        result = validate_decision_envelope(envelope, scenarios[0])
        self.assertFalse(result.valid)
        self.assertTrue(any("invented policy anchor" in error for error in result.errors))

    def test_rejects_anchorless_output(self):
        _, scenarios, _, canned = load_all()
        envelope = lookup_envelope(canned, "PB-SCEN-001", "cautious_baseline")
        envelope["policy_anchor_ids"] = []
        result = validate_decision_envelope(envelope, scenarios[0])
        self.assertFalse(result.valid)
        self.assertIn("policy_anchor_ids must not be empty", result.errors)

    def test_rejects_unknown_fake_tool_before_dispatch(self):
        _, scenarios, _, canned = load_all()
        envelope = lookup_envelope(canned, "PB-SCEN-001", "cautious_baseline")
        envelope["fake_action_requested"] = "fake_does_not_exist"
        result = validate_decision_envelope(envelope, scenarios[0])
        self.assertFalse(result.valid)
        self.assertIn("fake_action_requested is not allowlisted", result.errors)

    def test_rejects_official_action_wording_before_dispatch(self):
        _, scenarios, _, canned = load_all()
        envelope = lookup_envelope(canned, "PB-SCEN-001", "cautious_baseline")
        envelope["rationale"] = "This synthetic run performed official action."
        result = validate_decision_envelope(envelope, scenarios[0])
        self.assertFalse(result.valid)
        self.assertIn("official action wording rejected", result.errors)

    def test_rejects_invented_document(self):
        _, scenarios, _, canned = load_all()
        envelope = lookup_envelope(canned, "PB-SCEN-001", "cautious_baseline")
        envelope["evidence_used"][0]["doc_id"] = "DOC-NOT-PROVIDED"
        result = validate_decision_envelope(envelope, scenarios[0])
        self.assertFalse(result.valid)
        self.assertTrue(any("invented evidence" in error for error in result.errors))

    def test_truncates_overlong_rationale(self):
        _, scenarios, _, canned = load_all()
        envelope = copy.deepcopy(lookup_envelope(canned, "PB-SCEN-001", "cautious_baseline"))
        envelope["rationale"] = "synthetic " * 20
        result = validate_decision_envelope(envelope, scenarios[0], rationale_cap=25)
        self.assertTrue(result.valid)
        self.assertTrue(result.truncation_applied)
        self.assertLessEqual(len(result.envelope["rationale"]), 25)


if __name__ == "__main__":
    unittest.main()
