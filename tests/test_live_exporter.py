from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from policy_bonfire.live_adapters.base import FakeLiveAdapter
from policy_bonfire.live_config import parse_live_config
from policy_bonfire.run_live_provider_slice import run_live_slice
from policy_bonfire.types import CSV_LIVE_RUN_BANNER, LIVE_RUN_BANNER
from policy_bonfire.anchors import parse_run_date
from tests.helpers import DATA_DIR


class LiveExporterTests(unittest.TestCase):
    def test_live_artifacts_have_live_banner_and_usage_summary(self):
        config = parse_live_config({
            "PB_LIVE_CALLS": "1",
            "PB_LIVE_PROVIDERS": "openai",
            "OPENAI_API_KEY": "test-placeholder",
            "OPENAI_CHEAP_MODEL": "YOUR_MODEL_ID_HERE",
            "PB_LIVE_RATE_OPENAI_INPUT_USD_PER_1K": "0.001",
            "PB_LIVE_RATE_OPENAI_OUTPUT_USD_PER_1K": "0.001",
        })
        with tempfile.TemporaryDirectory() as tmp:
            export_dir = Path(tmp) / "bundle"
            result = run_live_slice(export_dir, DATA_DIR, parse_run_date("2026-05-01"), "live-export", config, {"openai": FakeLiveAdapter("openai")})
            self.assertTrue(result.passed, result.findings)
            for name in ["failure_cases.md", "model_comparison.md", "live_provider_receipt.md", "scrub_report.md"]:
                self.assertEqual(LIVE_RUN_BANNER, (export_dir / name).read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(CSV_LIVE_RUN_BANNER, (export_dir / "live_usage_summary.csv").read_text(encoding="utf-8").splitlines()[0])
            payload = json.loads((export_dir / "run_records.json").read_text(encoding="utf-8"))
            self.assertEqual(LIVE_RUN_BANNER, payload["_live_run_notice"])
            receipt = (export_dir / "live_provider_receipt.md").read_text(encoding="utf-8")
            self.assertIn("no_secrets_statement", receipt)
            self.assertIn("sandbox_status: verified", receipt)
            self.assertNotIn("raw_prompt", receipt.lower())
            self.assertNotIn("request_id", receipt.lower())
            model_comparison = (export_dir / "model_comparison.md").read_text(encoding="utf-8")
            self.assertIn("comparison_label: cross_prompt_only", model_comparison)
            self.assertIn("model_access_mode: api_live", model_comparison)
            self.assertIn("vendor_lineage_count: 1", model_comparison)
            self.assertIn("scored_run_count: 9", model_comparison)
            self.assertNotIn("comparison_label: mock_only", model_comparison)
            self.assertNotIn("no live provider behavior measured", model_comparison)
            scrub_report = (export_dir / "scrub_report.md").read_text(encoding="utf-8")
            self.assertIn("live-shaped bundle", scrub_report)
            self.assertNotIn("mock-only bundle", scrub_report)


if __name__ == "__main__":
    unittest.main()
