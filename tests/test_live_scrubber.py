from __future__ import annotations

import unittest

from policy_bonfire.scrubber import scan_artifact_text, write_scrub_report
from policy_bonfire.types import LIVE_RUN_BANNER, CSV_LIVE_RUN_BANNER, ScrubResult


class LiveScrubberTests(unittest.TestCase):
    def test_live_banner_is_accepted_for_live_artifacts(self):
        self.assertEqual((), scan_artifact_text("live_provider_receipt.md", LIVE_RUN_BANNER + "\n# Live\nno official action authorized\n", ".md"))
        self.assertEqual((), scan_artifact_text("live_usage_summary.csv", CSV_LIVE_RUN_BANNER + "\nprovider,run_count\nopenai,0\n", ".csv"))

    def test_blocks_live_secret_and_raw_body_shapes_without_echoing_literals(self):
        synthetic_key = "sk-" + "a" * 24
        synthetic_request_id = "req_" + "b" * 26
        synthetic_path = "/" + "home" + "/person/private"
        unsafe = LIVE_RUN_BANNER + f"\nraw_response: {synthetic_key} {synthetic_request_id}\n{synthetic_path}\n"
        findings = scan_artifact_text("live_provider_receipt.md", unsafe, ".md")
        classes = {finding.finding_class for finding in findings}

        self.assertIn("OPENAI_KEY_SHAPE", classes)
        self.assertIn("PROVIDER_REQUEST_ID", classes)
        self.assertIn("RAW_PROMPT_OR_RESPONSE_DUMP", classes)
        self.assertIn("LOCAL_PATH", classes)
        for finding in findings:
            self.assertNotIn("sk-", finding.sha256_of_match_prefix)
            self.assertNotIn("req_", finding.sha256_of_match_prefix)


if __name__ == "__main__":
    unittest.main()
