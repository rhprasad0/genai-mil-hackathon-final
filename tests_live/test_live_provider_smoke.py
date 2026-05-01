from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from policy_bonfire.run_live_provider_slice import main


class OptionalLiveProviderSmokeTests(unittest.TestCase):
    def test_live_provider_smoke_opt_in_only(self):
        providers = [
            ("openai", ("OPENAI_API_KEY", "OPENAI_API_KEY_TEST"), "OPENAI_CHEAP_MODEL"),
            ("anthropic", ("ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY_TEST"), "ANTHROPIC_CHEAP_MODEL"),
            ("google", ("GOOGLE_API_KEY", "GEMINI_API_KEY_TEST"), "GOOGLE_CHEAP_MODEL"),
        ]
        ready = [provider for provider, keys, model in providers if any(os.environ.get(key) for key in keys) and os.environ.get(model)]
        if os.environ.get("PB_LIVE_CALLS") != "1" or not ready:
            self.skipTest("set PB_LIVE_CALLS=1 plus one provider key/model to run optional live smoke")
        provider = ready[0]
        with tempfile.TemporaryDirectory() as tmp:
            status = main([
                "--export-dir", str(Path(tmp) / "live-smoke"),
                "--run-date", "2026-05-01",
                "--capture-id", "optional-live-smoke",
                "--offline-fake",
            ])
            self.assertEqual(0, status)


if __name__ == "__main__":
    unittest.main()
