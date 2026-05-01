from __future__ import annotations

import unittest

from policy_bonfire.live_config import can_schedule_call, parse_live_config
from policy_bonfire.live_contracts import (
    STATUS_BLOCKED_COST_CAP,
    STATUS_LIVE_CALLS_NOT_ENABLED,
    STATUS_PROVIDER_SKIPPED_MISSING_KEY,
    STATUS_PROVIDER_SKIPPED_MISSING_RATE,
    STATUS_PROVIDER_SKIPPED_MODEL_UNAVAILABLE,
)
from policy_bonfire.live_costs import TokenRates, estimate_cost_usd, project_worst_case_cost


class LiveConfigTests(unittest.TestCase):
    def test_default_config_is_offline_and_redacted(self):
        config = parse_live_config({})
        self.assertFalse(config.live_calls_enabled)
        self.assertEqual(STATUS_LIVE_CALLS_NOT_ENABLED, config.provider_config("openai").skip_status)
        summary = config.redacted_summary()
        self.assertFalse(summary["live_calls_enabled"])
        self.assertNotIn("secret", repr(summary).lower())
        self.assertNotIn("API_KEY", repr(summary))

    def test_missing_key_model_and_rate_are_safe_skips(self):
        missing_key = parse_live_config({"PB_LIVE_CALLS": "1", "OPENAI_CHEAP_MODEL": "YOUR_MODEL_ID_HERE"})
        self.assertEqual(STATUS_PROVIDER_SKIPPED_MISSING_KEY, missing_key.provider_config("openai").skip_status)

        test_alias_key = parse_live_config({"PB_LIVE_CALLS": "1", "OPENAI_API_KEY_TEST": "not-printed", "OPENAI_CHEAP_MODEL": "YOUR_MODEL_ID_HERE"})
        self.assertEqual(STATUS_PROVIDER_SKIPPED_MISSING_RATE, test_alias_key.provider_config("openai").skip_status)
        self.assertNotIn("not-printed", repr(test_alias_key.redacted_summary()))

        missing_model = parse_live_config({"PB_LIVE_CALLS": "1", "OPENAI_API_KEY": "not-printed"})
        self.assertEqual(STATUS_PROVIDER_SKIPPED_MODEL_UNAVAILABLE, missing_model.provider_config("openai").skip_status)

        missing_rate = parse_live_config(
            {"PB_LIVE_CALLS": "1", "OPENAI_API_KEY": "not-printed", "OPENAI_CHEAP_MODEL": "YOUR_MODEL_ID_HERE"}
        )
        self.assertEqual(STATUS_PROVIDER_SKIPPED_MISSING_RATE, missing_rate.provider_config("openai").skip_status)
        self.assertNotIn("not-printed", repr(missing_rate.redacted_summary()))

    def test_provider_allowlist_and_rates_enable_only_requested_provider(self):
        config = parse_live_config(
            {
                "PB_LIVE_CALLS": "1",
                "PB_LIVE_PROVIDERS": "openai",
                "OPENAI_API_KEY": "not-printed",
                "OPENAI_CHEAP_MODEL": "YOUR_MODEL_ID_HERE",
                "PB_LIVE_RATE_OPENAI_INPUT_USD_PER_1K": "0.01",
                "PB_LIVE_RATE_OPENAI_OUTPUT_USD_PER_1K": "0.02",
            }
        )
        self.assertTrue(config.provider_config("openai").enabled)
        self.assertFalse(config.provider_config("anthropic").enabled)
        self.assertIsNone(config.provider_config("anthropic").skip_status)

    def test_cost_estimate_and_caps_block_before_adapter(self):
        self.assertAlmostEqual(0.03, estimate_cost_usd(1000, 1000, TokenRates(0.01, 0.02)))
        projection = project_worst_case_cost(
            prompt_chars=4000,
            max_output_tokens=1000,
            rates=TokenRates(1.0, 1.0),
            max_total_usd=0.01,
        )
        self.assertFalse(projection.allowed)
        self.assertEqual(STATUS_BLOCKED_COST_CAP, projection.status)

    def test_schedule_blocks_max_runs_and_cost_caps(self):
        env = {
            "PB_LIVE_CALLS": "1",
            "PB_LIVE_MAX_RUNS": "1",
            "PB_LIVE_MAX_TOTAL_USD": "0.001",
            "OPENAI_API_KEY": "not-printed",
            "OPENAI_CHEAP_MODEL": "YOUR_MODEL_ID_HERE",
            "PB_LIVE_RATE_OPENAI_INPUT_USD_PER_1K": "10",
            "PB_LIVE_RATE_OPENAI_OUTPUT_USD_PER_1K": "10",
        }
        config = parse_live_config(env)
        allowed, status, _ = can_schedule_call(config, "openai", scheduled_runs=1, prompt_chars=1)
        self.assertFalse(allowed)
        self.assertEqual(STATUS_BLOCKED_COST_CAP, status)
        allowed, status, projection = can_schedule_call(config, "openai", scheduled_runs=0, prompt_chars=10000)
        self.assertFalse(allowed)
        self.assertEqual(STATUS_BLOCKED_COST_CAP, status)
        self.assertIsNotNone(projection)


if __name__ == "__main__":
    unittest.main()
