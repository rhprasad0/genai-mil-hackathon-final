from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from policy_bonfire.run_mock_v1 import main
from policy_bonfire.types import CSV_MOCK_ONLY_BANNER, MOCK_ONLY_BANNER

from tests.helpers import DATA_DIR, ROOT
from tests.test_evaluator import EXPECTED_RUN_COUNT


PROTECTED_PATHS = [
    ROOT / "docs" / "hackathon-submission-receipt.md",
    ROOT / "docs" / "demo-receipts.md",
]
PROTECTED_DIRS = [ROOT / "assets" / "demo"]


class MockV1EndToEndTests(unittest.TestCase):
    def test_cli_tempdir_isolated_bundle_and_matrix(self):
        before = _protected_fingerprint()
        repo_before = _repo_source_fingerprint()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            data_copy = tmp_path / "data"
            shutil.copytree(DATA_DIR, data_copy)
            export_one = tmp_path / "export-one"
            export_two = tmp_path / "export-two"
            args = [
                "--data-dir",
                str(data_copy),
                "--run-date",
                "2026-05-01",
                "--capture-id",
                "e2e-capture",
            ]
            self.assertEqual(0, main(args + ["--export-dir", str(export_one)]))
            self.assertEqual(0, main(args + ["--export-dir", str(export_two)]))

            run_records = json.loads((export_one / "run_records.json").read_text(encoding="utf-8"))
            evaluator_results = json.loads((export_one / "evaluator_results.json").read_text(encoding="utf-8"))
            self.assertEqual(MOCK_ONLY_BANNER, run_records["_mock_only_notice"])
            self.assertEqual(EXPECTED_RUN_COUNT, len(run_records["run_records"]))
            self.assertEqual(EXPECTED_RUN_COUNT, len(evaluator_results["evaluator_results"]))
            self.assertTrue(all(record["model_id_public_label"] == "mock-specimen-v1" for record in run_records["run_records"]))

            observed = {
                (row["scenario_id"], row["prompt_variant_id"]): {item["label"] for item in row["labels"]}
                for row in evaluator_results["evaluator_results"]
            }
            self.assertEqual(EXPECTED_RUN_COUNT, len(observed))
            self.assertIn(("PB-SCEN-010", "decorative_hitl_specimen"), observed)

            self.assertEqual(
                (export_one / "run_records.json").read_bytes(),
                (export_two / "run_records.json").read_bytes(),
            )
            self.assertEqual(
                (export_one / "evaluator_results.json").read_bytes(),
                (export_two / "evaluator_results.json").read_bytes(),
            )

            for path in export_one.rglob("*"):
                if not path.is_file():
                    continue
                text = path.read_text(encoding="utf-8")
                if path.suffix == ".json":
                    self.assertEqual(MOCK_ONLY_BANNER, json.loads(text)["_mock_only_notice"])
                elif path.suffix == ".csv":
                    self.assertEqual(CSV_MOCK_ONLY_BANNER, text.splitlines()[0])
                else:
                    self.assertEqual(MOCK_ONLY_BANNER, text.splitlines()[0])

        self.assertEqual(before, _protected_fingerprint())
        self.assertEqual(repo_before, _repo_source_fingerprint())


def _repo_source_fingerprint():
    digest = hashlib.sha256()
    excluded_dirs = {".git", "artifacts", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
    excluded_suffixes = {".pyc", ".pyo"}
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if excluded_dirs.intersection(path.relative_to(ROOT).parts):
            continue
        if path.suffix in excluded_suffixes:
            continue
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _protected_fingerprint():
    digest = hashlib.sha256()
    for path in PROTECTED_PATHS:
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    for directory in PROTECTED_DIRS:
        for path in sorted(directory.rglob("*")):
            if path.is_file():
                digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
                digest.update(path.read_bytes())
    return digest.hexdigest()


if __name__ == "__main__":
    unittest.main()
