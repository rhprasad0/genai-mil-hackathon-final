from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from policy_bonfire.exporter import required_artifact_paths
from policy_bonfire.live_adapters.base import FakeLiveAdapter
from policy_bonfire.live_config import parse_live_config
from policy_bonfire.live_contracts import LiveModelResponse, STATUS_EXCLUDED_FENCED_JSON
from policy_bonfire.run_live_provider_slice import main, run_live_slice
from policy_bonfire.types import CSV_LIVE_RUN_BANNER, LIVE_RUN_BANNER
from tests.helpers import DATA_DIR
from policy_bonfire.anchors import parse_run_date


class LiveRunnerCliTests(unittest.TestCase):
    def test_cli_default_is_offline_and_writes_skipped_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            export_dir = Path(tmp) / "live"
            status = main(["--data-dir", str(DATA_DIR), "--export-dir", str(export_dir), "--run-date", "2026-05-01", "--capture-id", "offline-skip"])
            self.assertEqual(0, status)
            receipt = (export_dir / "live_provider_receipt.md").read_text(encoding="utf-8")
            self.assertEqual(LIVE_RUN_BANNER, receipt.splitlines()[0])
            self.assertIn("live_calls_not_enabled", receipt)
            records = json.loads((export_dir / "run_records.json").read_text(encoding="utf-8"))
            self.assertEqual(LIVE_RUN_BANNER, records["_live_run_notice"])
            self.assertTrue(all(record["status"] == "live_calls_not_enabled" for record in records["run_records"]))

    def test_injected_fake_adapter_scores_without_raw_prompt_or_response(self):
        env = {
            "PB_LIVE_CALLS": "1",
            "PB_LIVE_PROVIDERS": "openai",
            "OPENAI_API_KEY": "test-placeholder",
            "OPENAI_CHEAP_MODEL": "YOUR_MODEL_ID_HERE",
            "PB_LIVE_RATE_OPENAI_INPUT_USD_PER_1K": "0.001",
            "PB_LIVE_RATE_OPENAI_OUTPUT_USD_PER_1K": "0.001",
        }
        config = parse_live_config(env)
        adapters = {"openai": FakeLiveAdapter("openai", "YOUR_MODEL_ID_HERE", "cheap-mini-tier")}
        with tempfile.TemporaryDirectory() as tmp:
            export_dir = Path(tmp) / "live"
            result = run_live_slice(export_dir, DATA_DIR, parse_run_date("2026-05-01"), "fake-live", config, adapters)
            self.assertTrue(result.passed, result.findings)
            for path in required_artifact_paths(export_dir, artifact_mode="live"):
                self.assertTrue(path.exists(), path)
            usage = (export_dir / "live_usage_summary.csv").read_text(encoding="utf-8")
            self.assertEqual(CSV_LIVE_RUN_BANNER, usage.splitlines()[0])
            records = json.loads((export_dir / "run_records.json").read_text(encoding="utf-8"))["run_records"]
            scored = [record for record in records if record.get("scored") is True]
            self.assertEqual(9, len(scored))
            self.assertNotIn("rendered_prompt", json.dumps(records))
            self.assertNotIn("raw_response", json.dumps(records).lower())

    def test_run_live_slice_hard_blocks_injected_adapter_when_live_calls_disabled(self):
        config = parse_live_config({})
        adapters = {"openai": FakeLiveAdapter("openai", "offline-fake-model", "cheap-mini-tier")}
        with tempfile.TemporaryDirectory() as tmp:
            export_dir = Path(tmp) / "live"
            result = run_live_slice(export_dir, DATA_DIR, parse_run_date("2026-05-01"), "no-live", config, adapters)
            self.assertTrue(result.passed, result.findings)
            records = json.loads((export_dir / "run_records.json").read_text(encoding="utf-8"))["run_records"]
            openai = [record for record in records if record.get("provider") == "openai"]
            self.assertEqual(1, len(openai))
            self.assertEqual("live_calls_not_enabled", openai[0]["status"])
            self.assertTrue(all(record.get("scored") is False for record in records))

    def test_offline_skipped_records_do_not_persist_exact_model_id(self):
        config = parse_live_config({
            "PB_LIVE_PROVIDERS": "openai",
            "OPENAI_API_KEY": "test-placeholder",
            "OPENAI_CHEAP_MODEL": "SHOULD_NOT_BE_USED",
        })
        with tempfile.TemporaryDirectory() as tmp:
            export_dir = Path(tmp) / "live"
            result = run_live_slice(export_dir, DATA_DIR, parse_run_date("2026-05-01"), "offline-model-hygiene", config, {})
            self.assertTrue(result.passed, result.findings)
            records = json.loads((export_dir / "run_records.json").read_text(encoding="utf-8"))["run_records"]
            openai = [record for record in records if record.get("provider") == "openai"][0]
            self.assertEqual("live_calls_not_enabled", openai["status"])
            self.assertEqual("not_recorded_offline", openai["model_id_exact"])
            self.assertNotIn("SHOULD_NOT_BE_USED", json.dumps(records))

    def test_excluded_live_response_usage_is_costed_in_artifacts(self):
        env = {
            "PB_LIVE_CALLS": "1",
            "PB_LIVE_PROVIDERS": "openai",
            "OPENAI_API_KEY": "test-placeholder",
            "OPENAI_CHEAP_MODEL": "YOUR_MODEL_ID_HERE",
            "PB_LIVE_RATE_OPENAI_INPUT_USD_PER_1K": "0.001",
            "PB_LIVE_RATE_OPENAI_OUTPUT_USD_PER_1K": "0.005",
            "PB_LIVE_MAX_RUNS": "1",
        }
        config = parse_live_config(env)
        adapter = FakeLiveAdapter("openai", "YOUR_MODEL_ID_HERE", "cheap-mini-tier")
        adapter.enqueue(
            LiveModelResponse(
                status=STATUS_EXCLUDED_FENCED_JSON,
                provider="openai",
                model_id_exact="YOUR_MODEL_ID_HERE",
                model_id_public_label="cheap-mini-tier",
                model_family="openai_lineage",
                usage_input_tokens=490,
                usage_output_tokens=452,
                usage_estimated=False,
                cost_estimate=0.0,
                finish_reason="end_turn",
                latency_ms=12,
            )
        )
        with tempfile.TemporaryDirectory() as tmp:
            export_dir = Path(tmp) / "live"
            result = run_live_slice(export_dir, DATA_DIR, parse_run_date("2026-05-01"), "excluded-cost", config, {"openai": adapter})
            self.assertTrue(result.passed, result.findings)
            records = json.loads((export_dir / "run_records.json").read_text(encoding="utf-8"))["run_records"]
            excluded = [record for record in records if record.get("status") == STATUS_EXCLUDED_FENCED_JSON][0]
            self.assertEqual("0.002750", f"{excluded['cost_estimate']:.6f}")
            usage = (export_dir / "live_usage_summary.csv").read_text(encoding="utf-8")
            self.assertIn("0.002750", usage)

    def test_cumulative_cost_cap_reserves_projection_across_calls(self):
        env = {
            "PB_LIVE_CALLS": "1",
            "PB_LIVE_PROVIDERS": "openai",
            "OPENAI_API_KEY": "test-placeholder",
            "OPENAI_CHEAP_MODEL": "YOUR_MODEL_ID_HERE",
            "PB_LIVE_RATE_OPENAI_INPUT_USD_PER_1K": "0.001",
            "PB_LIVE_RATE_OPENAI_OUTPUT_USD_PER_1K": "0.001",
            "PB_LIVE_MAX_TOTAL_USD": "0.01",
        }
        config = parse_live_config(env)
        adapters = {"openai": FakeLiveAdapter("openai", "YOUR_MODEL_ID_HERE", "cheap-mini-tier")}
        with tempfile.TemporaryDirectory() as tmp:
            export_dir = Path(tmp) / "live"
            result = run_live_slice(export_dir, DATA_DIR, parse_run_date("2026-05-01"), "cost-reserve", config, adapters)
            self.assertTrue(result.passed, result.findings)
            records = json.loads((export_dir / "run_records.json").read_text(encoding="utf-8"))["run_records"]
            openai = [record for record in records if record.get("provider") == "openai"]
            self.assertEqual(1, sum(1 for record in openai if record["status"] == "completed_valid"))
            self.assertEqual(8, sum(1 for record in openai if record["status"] == "blocked_cost_cap"))


if __name__ == "__main__":
    unittest.main()
