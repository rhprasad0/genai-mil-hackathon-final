from __future__ import annotations

from datetime import date
import tempfile
import unittest
from pathlib import Path

from policy_bonfire.anchors import load_anchor_manifest
from policy_bonfire.scenarios import load_scenario_file, load_scenarios
from policy_bonfire.types import ValidationError

from tests.helpers import DATA_DIR, mutable_scenario_payload, write_json


class ScenarioLoaderTests(unittest.TestCase):
    def setUp(self):
        self.anchors = load_anchor_manifest(
            DATA_DIR / "policy_anchors" / "mock_v1_anchors.json",
            run_date=date(2026, 5, 1),
        )

    def test_all_scenarios_load(self):
        scenarios = load_scenarios(DATA_DIR / "scenarios", self.anchors)
        self.assertEqual(21, len(scenarios))
        self.assertEqual("PB-SCEN-PL-001", scenarios[0].scenario_id)
        self.assertEqual("PB-SCEN-AUD-003", scenarios[-1].scenario_id)
        self.assertTrue(all(s.public_claim_limit for s in scenarios))

    def test_rejects_missing_anchor_reference(self):
        payload = mutable_scenario_payload("01_pb_scen_pl_001_citation_laundromat.json")
        payload["policy_anchors"] = ["MISSING-ANCHOR"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scenario.json"
            write_json(path, payload)
            with self.assertRaisesRegex(ValidationError, "missing anchor"):
                load_scenario_file(path, self.anchors)

    def test_rejects_non_synthetic_card(self):
        payload = mutable_scenario_payload("01_pb_scen_pl_001_citation_laundromat.json")
        payload["synthetic_notice"] = False
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scenario.json"
            write_json(path, payload)
            with self.assertRaisesRegex(ValidationError, "synthetic_notice"):
                load_scenario_file(path, self.anchors)

    def test_rejects_missing_expected_action(self):
        payload = mutable_scenario_payload("01_pb_scen_pl_001_citation_laundromat.json")
        del payload["expected_safe_behavior"]["primary_expected_safe_control_action"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scenario.json"
            write_json(path, payload)
            with self.assertRaisesRegex(ValidationError, "primary expected"):
                load_scenario_file(path, self.anchors)

    def test_rejects_oversized_untrusted_packet_text(self):
        payload = mutable_scenario_payload("03_pb_scen_pl_003_local_custom_becomes_official_rule.json")
        payload["untrusted_packet_text"] = "x" * 801
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scenario.json"
            write_json(path, payload)
            with self.assertRaisesRegex(ValidationError, "exceeds cap"):
                load_scenario_file(path, self.anchors)


if __name__ == "__main__":
    unittest.main()
