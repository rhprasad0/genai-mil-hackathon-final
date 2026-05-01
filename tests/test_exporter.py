from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from policy_bonfire.exporter import required_artifact_paths
from policy_bonfire.run_mock_v1 import main
from policy_bonfire.types import CSV_MOCK_ONLY_BANNER, MOCK_ONLY_BANNER

from tests.helpers import DATA_DIR


class ExporterTests(unittest.TestCase):
    def test_required_files_and_banners(self):
        with tempfile.TemporaryDirectory() as tmp:
            export_dir = Path(tmp) / "bundle"
            status = main(
                [
                    "--data-dir",
                    str(DATA_DIR),
                    "--export-dir",
                    str(export_dir),
                    "--run-date",
                    "2026-05-01",
                    "--capture-id",
                    "test-exporter",
                ]
            )
            self.assertEqual(0, status)
            for path in required_artifact_paths(export_dir):
                self.assertTrue(path.exists(), path)
                text = path.read_text(encoding="utf-8")
                if path.suffix == ".json":
                    payload = json.loads(text)
                    self.assertEqual(MOCK_ONLY_BANNER, payload["_mock_only_notice"])
                    self.assertEqual("_mock_only_notice", next(iter(payload)))
                elif path.suffix == ".csv":
                    self.assertEqual(CSV_MOCK_ONLY_BANNER, text.splitlines()[0])
                else:
                    self.assertEqual(MOCK_ONLY_BANNER, text.splitlines()[0])


if __name__ == "__main__":
    unittest.main()
