from __future__ import annotations

from datetime import date
import tempfile
import unittest
from pathlib import Path

from policy_bonfire.anchors import load_anchor_manifest
from policy_bonfire.types import ValidationError

from tests.helpers import mutable_anchor_payload, write_json


class AnchorManifestTests(unittest.TestCase):
    def test_loads_fresh_public_policy_anchors(self):
        anchors = load_anchor_manifest(
            Path("data/policy_anchors/mock_v1_anchors.json"),
            run_date=date(2026, 5, 1),
        )
        self.assertEqual(
            {
                "DOD-RAI-TRACEABLE",
                "DOD-RAI-RELIABLE",
                "DOD-RAI-RESPONSIBLE",
                "DOD-RAI-GOVERNABLE",
                "CDAO-RAI-PATHWAY-GOVERNANCE",
            },
            set(anchors),
        )

    def test_rejects_stale_anchor(self):
        payload = mutable_anchor_payload()
        payload["anchors"][0]["citation_date_checked"] = "2025-01-01"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "anchors.json"
            write_json(path, payload)
            with self.assertRaisesRegex(ValidationError, "blocked_pending_anchor_refresh"):
                load_anchor_manifest(path, run_date=date(2026, 5, 1))

    def test_rejects_bad_status(self):
        payload = mutable_anchor_payload()
        payload["anchors"][0]["retrieval_status"] = "failed"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "anchors.json"
            write_json(path, payload)
            with self.assertRaisesRegex(ValidationError, "retrieval_status"):
                load_anchor_manifest(path, run_date=date(2026, 5, 1))

    def test_rejects_missing_policy_point(self):
        payload = mutable_anchor_payload()
        payload["anchors"][0]["supported_claim"] = ""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "anchors.json"
            write_json(path, payload)
            with self.assertRaisesRegex(ValidationError, "supported_claim"):
                load_anchor_manifest(path, run_date=date(2026, 5, 1))

    def test_rejects_non_mock_source_url(self):
        payload = mutable_anchor_payload()
        payload["anchors"][0]["source_url"] = "http" + "s://example.test/anchor"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "anchors.json"
            write_json(path, payload)
            with self.assertRaisesRegex(ValidationError, "source_url"):
                load_anchor_manifest(path, run_date=date(2026, 5, 1))


if __name__ == "__main__":
    unittest.main()
