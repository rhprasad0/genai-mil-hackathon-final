from __future__ import annotations

import unittest

from policy_bonfire.decision_envelope import validate_decision_envelope
from policy_bonfire.fake_tools import dispatch_fake_tool, reject_fake_tool
from policy_bonfire.mock_specimen import lookup_envelope
from policy_bonfire.run_mock_v1 import fake_call_for_validation

from tests.helpers import load_all


class FakeToolTests(unittest.TestCase):
    def setUp(self):
        _, self.scenarios, _, self.canned = load_all()
        self.scenario_by_id = {scenario.scenario_id: scenario for scenario in self.scenarios}

    def test_unknown_tool_is_inert_and_rejected(self):
        record = reject_fake_tool("run-1", "fake_does_not_exist", "fake tool is not allowlisted")
        self.assertFalse(record["accepted"])
        self.assertTrue(record["recorded_but_rejected"])
        self.assertIn("allowlisted", record["rejection_reason"])

    def test_allowed_request_info_is_accepted(self):
        scenario = self.scenario_by_id["PB-SCEN-PL-002"]
        envelope = lookup_envelope(self.canned, scenario.scenario_id, "cautious_baseline")
        record = dispatch_fake_tool("run-2", envelope, scenario)
        self.assertTrue(record["accepted"])
        self.assertFalse(record["recorded_but_rejected"])

    def test_final_denial_in_request_info_scenario_is_rejected(self):
        scenario = self.scenario_by_id["PB-SCEN-PL-002"]
        envelope = lookup_envelope(self.canned, scenario.scenario_id, "policy_voice_specimen")
        record = dispatch_fake_tool("run-3", envelope, scenario)
        self.assertFalse(record["accepted"])
        self.assertTrue(record["recorded_but_rejected"])
        self.assertIn("disallowed", record["rejection_reason"])

    def test_invented_anchor_attempt_is_rejected_and_recorded(self):
        scenario = self.scenario_by_id["PB-SCEN-PL-001"]
        envelope = lookup_envelope(self.canned, scenario.scenario_id, "policy_voice_specimen")
        record = dispatch_fake_tool("run-4", envelope, scenario)
        self.assertFalse(record["accepted"])
        self.assertTrue(record["recorded_but_rejected"])
        self.assertIn("invented policy anchor", record["rejection_reason"])

    def test_invalid_envelope_is_rejected_before_fake_tool_dispatch(self):
        scenario = self.scenario_by_id["PB-SCEN-PL-001"]
        envelope = lookup_envelope(self.canned, scenario.scenario_id, "cautious_baseline")
        envelope["policy_anchor_ids"] = []
        validation = validate_decision_envelope(envelope, scenario)
        self.assertFalse(validation.valid)
        record = fake_call_for_validation("run-invalid", validation, scenario)
        self.assertFalse(record["accepted"])
        self.assertTrue(record["recorded_but_rejected"])
        self.assertIn("invalid decision envelope", record["rejection_reason"])


if __name__ == "__main__":
    unittest.main()
