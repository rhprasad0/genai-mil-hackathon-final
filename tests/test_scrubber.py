from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from policy_bonfire.scrubber import scan_artifact_text, write_scrub_report
from policy_bonfire.types import MOCK_ONLY_BANNER, ScrubResult


class ScrubberTests(unittest.TestCase):
    def test_clean_synthetic_markdown_passes(self):
        text = MOCK_ONLY_BANNER + "\nSynthetic mock-only artifact with no sensitive fixture text.\n"
        findings = scan_artifact_text("clean.md", text, ".md")
        self.assertEqual((), findings)

    def test_blocks_private_and_sensitive_patterns_without_echoing_literals(self):
        email = "nobody [at] example.invalid"
        token = "A[K]IAIO...MPLE"
        private_path = "/" + "home" + "/synthetic/path"
        local_url = "http" + "://" + "local" + "host:8000/mock"
        public_url = "http" + "s://example.test/mock"
        record_id = "voucher" + "ABC12345"
        text = (
            MOCK_ONLY_BANNER
            + "\n"
            + "\n".join(
                [
                    email,
                    token,
                    private_path,
                    local_url,
                    public_url,
                    record_id,
                    "performed official action",
                ]
            )
            + "\n"
        )
        findings = scan_artifact_text("bad.md", text, ".md")
        classes = {finding.finding_class for finding in findings}
        self.assertIn("EMAIL_ADDRESS", classes)
        self.assertIn("AWS_KEY_SHAPE", classes)
        self.assertIn("LOCAL_PATH", classes)
        self.assertIn("LOCAL_URL", classes)
        self.assertIn("HTTP_URL", classes)
        self.assertIn("REAL_LOOKING_RECORD_ID", classes)
        self.assertIn("OFFICIAL_ACTION_WORDING", classes)

        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "scrub_report.md"
            result = ScrubResult(status="blocked", findings=findings, checked_artifacts=())
            write_scrub_report(report, result)
            report_text = report.read_text(encoding="utf-8")
            for literal in (email, token, private_path, local_url, public_url, record_id):
                self.assertNotIn(literal, report_text)
            self.assertEqual((), scan_artifact_text("scrub_report.md", report_text, ".md"))

    def test_rejects_missing_banner_and_json_notice(self):
        md_findings = scan_artifact_text("missing.md", "plain text\n", ".md")
        json_findings = scan_artifact_text("run_records.json", '{"run_records":[]}\n', ".json")
        self.assertTrue(any(f.finding_class == "MISSING_OR_ALTERED_BANNER" for f in md_findings))
        self.assertTrue(any(f.finding_class == "MISSING_OR_ALTERED_BANNER" for f in json_findings))


if __name__ == "__main__":
    unittest.main()
