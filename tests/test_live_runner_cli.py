from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from policy_bonfire.exporter import required_artifact_paths
from policy_bonfire.live_adapters.base import FakeLiveAdapter
from policy_bonfire.live_config import parse_live_config
from policy_bonfire.live_contracts import LiveModelResponse, STATUS_COMPLETED_VALID, STATUS_EXCLUDED_FENCED_JSON
from policy_bonfire.run_live_provider_slice import main, run_live_slice
from policy_bonfire.types import CSV_LIVE_RUN_BANNER, LIVE_RUN_BANNER
from tests.helpers import copy_live_test_data
from policy_bonfire.anchors import parse_run_date


class LiveRunnerCliTests(unittest.TestCase):
    def test_cli_default_is_offline_and_writes_skipped_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            data_dir = copy_live_test_data(tmp_path, scenario_limit=3)
            export_dir = tmp_path / "live"
            with patch.dict("os.environ", {}, clear=True):
                status = main(["--data-dir", str(data_dir), "--export-dir", str(export_dir), "--run-date", "2026-05-01", "--capture-id", "offline-skip"])
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
            tmp_path = Path(tmp)
            data_dir = copy_live_test_data(tmp_path, scenario_limit=3)
            export_dir = tmp_path / "live"
            result = run_live_slice(export_dir, data_dir, parse_run_date("2026-05-01"), "fake-live", config, adapters)
            self.assertTrue(result.passed, result.findings)
            for path in required_artifact_paths(export_dir, artifact_mode="live"):
                self.assertTrue(path.exists(), path)
            usage = (export_dir / "live_usage_summary.csv").read_text(encoding="utf-8")
            self.assertEqual(CSV_LIVE_RUN_BANNER, usage.splitlines()[0])
            self.assertIn("repetition_id", usage.splitlines()[1])
            records = json.loads((export_dir / "run_records.json").read_text(encoding="utf-8"))["run_records"]
            scored = [record for record in records if record.get("scored") is True]
            self.assertEqual(3, config.repetitions)
            self.assertEqual(27, len(scored))
            self.assertEqual(len(records), len({record["run_id"] for record in records}))
            self.assertEqual({"rep_001", "rep_002", "rep_003"}, {record["repetition_id"] for record in scored})
            self.assertTrue(all(record["repetition_id"] == "rep_000" for record in records if record["status"] == "live_calls_not_enabled"))
            by_combo: dict[tuple[str, str], list[dict[str, object]]] = {}
            for record in scored:
                by_combo.setdefault((str(record["scenario_id"]), str(record["prompt_variant_id"])), []).append(record)
            self.assertEqual(9, len(by_combo))
            for rows in by_combo.values():
                self.assertEqual(3, len(rows))
                self.assertEqual({"rep_001", "rep_002", "rep_003"}, {str(row["repetition_id"]) for row in rows})
                for field in ("scenario_card_hash", "prompt_template_hash", "prompt_inventory_template_hash"):
                    self.assertEqual(1, len({str(row[field]) for row in rows}))
            self.assertNotIn("rendered_prompt", json.dumps(records))
            self.assertNotIn("raw_response", json.dumps(records).lower())

    def test_run_live_slice_hard_blocks_injected_adapter_when_live_calls_disabled(self):
        config = parse_live_config({})
        adapters = {"openai": FakeLiveAdapter("openai", "offline-fake-model", "cheap-mini-tier")}
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            data_dir = copy_live_test_data(tmp_path, scenario_limit=3)
            export_dir = tmp_path / "live"
            result = run_live_slice(export_dir, data_dir, parse_run_date("2026-05-01"), "no-live", config, adapters)
            self.assertTrue(result.passed, result.findings)
            records = json.loads((export_dir / "run_records.json").read_text(encoding="utf-8"))["run_records"]
            openai = [record for record in records if record.get("provider") == "openai"]
            self.assertEqual(1, len(openai))
            self.assertEqual("live_calls_not_enabled", openai[0]["status"])
            self.assertEqual("rep_000", openai[0]["repetition_id"])
            self.assertTrue(all(record.get("scored") is False for record in records))

    def test_offline_skipped_records_do_not_persist_exact_model_id(self):
        config = parse_live_config({
            "PB_LIVE_PROVIDERS": "openai",
            "OPENAI_API_KEY": "test-placeholder",
            "OPENAI_CHEAP_MODEL": "SHOULD_NOT_BE_USED",
        })
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            data_dir = copy_live_test_data(tmp_path, scenario_limit=3)
            export_dir = tmp_path / "live"
            result = run_live_slice(export_dir, data_dir, parse_run_date("2026-05-01"), "offline-model-hygiene", config, {})
            self.assertTrue(result.passed, result.findings)
            records = json.loads((export_dir / "run_records.json").read_text(encoding="utf-8"))["run_records"]
            openai = [record for record in records if record.get("provider") == "openai"][0]
            self.assertEqual("live_calls_not_enabled", openai["status"])
            self.assertEqual("not_recorded_offline", openai["model_id_exact"])
            self.assertNotIn("SHOULD_NOT_BE_USED", json.dumps(records))

    def test_missing_stop_path_completed_response_is_scored_as_control_failure(self):
        env = {
            "PB_LIVE_CALLS": "1",
            "PB_LIVE_PROVIDERS": "openai",
            "OPENAI_API_KEY": "test-placeholder",
            "OPENAI_CHEAP_MODEL": "YOUR_MODEL_ID_HERE",
            "PB_LIVE_RATE_OPENAI_INPUT_USD_PER_1K": "0.001",
            "PB_LIVE_RATE_OPENAI_OUTPUT_USD_PER_1K": "0.001",
            "PB_LIVE_MAX_RUNS": "1",
            "PB_LIVE_REPETITIONS": "1",
        }
        config = parse_live_config(env)
        adapter = FakeLiveAdapter("openai", "YOUR_MODEL_ID_HERE", "cheap-mini-tier")
        adapter.enqueue(
            LiveModelResponse(
                status=STATUS_COMPLETED_VALID,
                provider="openai",
                model_id_exact="YOUR_MODEL_ID_HERE",
                model_id_public_label="cheap-mini-tier",
                model_family="openai_lineage",
                usage_input_tokens=100,
                usage_output_tokens=50,
                usage_estimated=False,
                finish_reason="STOP",
                latency_ms=12,
                parsed_decision_envelope={
                    "recommendation": "refuse",
                    "confidence": "medium",
                    "evidence_used": [{"doc_id": "DOC-PL-001-A"}],
                    "policy_anchor_ids": ["DOD-RAI-TRACEABLE"],
                    "rationale": "Synthetic refusal without the required stop path.",
                    "human_review_required": True,
                    "pre_finalization_stop_path": None,
                    "fake_action_requested": "fake_deny",
                    "refusal": {"refused": True, "reason": "Synthetic refusal.", "named_policy_basis_anchor_ids": ["DOD-RAI-TRACEABLE"]},
                },
            )
        )
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            data_dir = copy_live_test_data(tmp_path, scenario_limit=3)
            export_dir = tmp_path / "live"
            result = run_live_slice(export_dir, data_dir, parse_run_date("2026-05-01"), "semantic-error", config, {"openai": adapter})
            self.assertTrue(result.passed, result.findings)
            records = json.loads((export_dir / "run_records.json").read_text(encoding="utf-8"))["run_records"]
            completed = [record for record in records if record.get("status") == STATUS_COMPLETED_VALID][0]
            self.assertEqual("STOP", completed["finish_reason"])
            self.assertTrue(completed["scored"])
            self.assertTrue(completed["bounded_json_valid"])
            self.assertEqual("passed", completed["semantic_validation_status"])
            self.assertEqual([], completed["decision_envelope_errors"])
            self.assertIn("NO_PRE_FINALIZATION_STOP_PATH", completed["decision_envelope_warnings"])
            evaluator_results = json.loads((export_dir / "evaluator_results.json").read_text(encoding="utf-8"))["evaluator_results"]
            labels = {label["label"] for result in evaluator_results for label in result["labels"]}
            self.assertIn("NO_PRE_FINALIZATION_STOP_PATH", labels)

    def test_excluded_live_response_usage_is_costed_in_artifacts(self):
        env = {
            "PB_LIVE_CALLS": "1",
            "PB_LIVE_PROVIDERS": "openai",
            "OPENAI_API_KEY": "test-placeholder",
            "OPENAI_CHEAP_MODEL": "YOUR_MODEL_ID_HERE",
            "PB_LIVE_RATE_OPENAI_INPUT_USD_PER_1K": "0.001",
            "PB_LIVE_RATE_OPENAI_OUTPUT_USD_PER_1K": "0.005",
            "PB_LIVE_MAX_RUNS": "1",
            "PB_LIVE_REPETITIONS": "1",
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
            tmp_path = Path(tmp)
            data_dir = copy_live_test_data(tmp_path, scenario_limit=3)
            export_dir = tmp_path / "live"
            result = run_live_slice(export_dir, data_dir, parse_run_date("2026-05-01"), "excluded-cost", config, {"openai": adapter})
            self.assertTrue(result.passed, result.findings)
            records = json.loads((export_dir / "run_records.json").read_text(encoding="utf-8"))["run_records"]
            excluded = [record for record in records if record.get("status") == STATUS_EXCLUDED_FENCED_JSON][0]
            self.assertEqual("0.002750", f"{excluded['cost_estimate']:.6f}")
            usage = (export_dir / "live_usage_summary.csv").read_text(encoding="utf-8")
            self.assertIn("0.002750", usage)

    def test_max_runs_blocks_repetition_expanded_schedule(self):
        env = {
            "PB_LIVE_CALLS": "1",
            "PB_LIVE_PROVIDERS": "openai",
            "OPENAI_API_KEY": "test-placeholder",
            "OPENAI_CHEAP_MODEL": "YOUR_MODEL_ID_HERE",
            "PB_LIVE_RATE_OPENAI_INPUT_USD_PER_1K": "0.001",
            "PB_LIVE_RATE_OPENAI_OUTPUT_USD_PER_1K": "0.001",
            "PB_LIVE_MAX_RUNS": "1",
        }
        config = parse_live_config(env)
        adapters = {"openai": FakeLiveAdapter("openai", "YOUR_MODEL_ID_HERE", "cheap-mini-tier")}
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            data_dir = copy_live_test_data(tmp_path, scenario_limit=3)
            export_dir = tmp_path / "live"
            result = run_live_slice(export_dir, data_dir, parse_run_date("2026-05-01"), "max-runs-reps", config, adapters)
            self.assertTrue(result.passed, result.findings)
            records = json.loads((export_dir / "run_records.json").read_text(encoding="utf-8"))["run_records"]
            openai = [record for record in records if record.get("provider") == "openai" and record.get("scenario_id")]
            self.assertEqual(27, len(openai))
            self.assertEqual(1, sum(1 for record in openai if record["status"] == "completed_valid"))
            self.assertEqual(26, sum(1 for record in openai if record["status"] == "blocked_cost_cap"))
            self.assertEqual({"rep_001", "rep_002", "rep_003"}, {record["repetition_id"] for record in openai})
            self.assertEqual(27, len({record["run_id"] for record in openai}))

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
            tmp_path = Path(tmp)
            data_dir = copy_live_test_data(tmp_path, scenario_limit=3)
            export_dir = tmp_path / "live"
            result = run_live_slice(export_dir, data_dir, parse_run_date("2026-05-01"), "cost-reserve", config, adapters)
            self.assertTrue(result.passed, result.findings)
            records = json.loads((export_dir / "run_records.json").read_text(encoding="utf-8"))["run_records"]
            openai = [record for record in records if record.get("provider") == "openai"]
            scheduled = [record for record in openai if record.get("scenario_id")]
            self.assertEqual(1, sum(1 for record in openai if record["status"] == "completed_valid"))
            self.assertEqual(len(scheduled) - 1, sum(1 for record in openai if record["status"] == "blocked_cost_cap"))
            self.assertEqual({"rep_001", "rep_002", "rep_003"}, {record["repetition_id"] for record in scheduled})


if __name__ == "__main__":
    unittest.main()
