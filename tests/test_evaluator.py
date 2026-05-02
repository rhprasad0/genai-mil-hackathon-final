from __future__ import annotations

import unittest

from tests.helpers import evaluator_matrix


EXPECTED_SCENARIO_COUNT = 10
PROMPT_VARIANT_COUNT = 3
EXPECTED_RUN_COUNT = EXPECTED_SCENARIO_COUNT * PROMPT_VARIANT_COUNT


class EvaluatorTests(unittest.TestCase):
    def test_ten_by_three_matrix_has_representative_failures(self):
        rows = evaluator_matrix()
        self.assertEqual(EXPECTED_RUN_COUNT, len(rows))
        self.assertEqual(set(), {item["label"] for item in rows[("PB-SCEN-001", "cautious_baseline")]["labels"]})
        self.assertIn("INVENTED_CITATION", {item["label"] for item in rows[("PB-SCEN-003", "policy_voice_specimen")]["labels"]})
        self.assertIn("UNSUPPORTED_DENIAL", {item["label"] for item in rows[("PB-SCEN-002", "decorative_hitl_specimen")]["labels"]})
        self.assertIn("UNSUPPORTED_DENIAL", {item["label"] for item in rows[("PB-SCEN-002", "policy_voice_specimen")]["labels"]})


if __name__ == "__main__":
    unittest.main()
