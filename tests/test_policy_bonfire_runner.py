import importlib.util
import json
import sys
from pathlib import Path


RUNNER_PATH = Path(__file__).resolve().parents[1] / "experiments" / "policy-bonfire" / "run_model_sweep.py"
spec = importlib.util.spec_from_file_location("policy_bonfire_runner", RUNNER_PATH)
runner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runner
spec.loader.exec_module(runner)


def test_extract_json_object_from_fenced_response():
    raw = """Here is the synthetic result:\n```json\n{\"status\": \"SYNTHETIC\", \"value\": 3}\n```"""

    parsed = runner.extract_json_object(raw)

    assert parsed == {"status": "SYNTHETIC", "value": 3}


def test_safety_scan_blocks_private_paths_and_secret_values():
    private_path = "/" + "home/example"
    secret_assignment = "SE" + "CRET=abc123"
    text = f"SYNTHETIC trace accidentally included {private_path} and {secret_assignment}"

    findings = runner.scan_public_safety(text)

    assert any(finding["rule"] == "private_path" for finding in findings)
    assert any(finding["rule"] == "secret_assignment" for finding in findings)


def test_actor_schema_validation_requires_expected_channels():
    actor = {
        "red_plan": "SYNTHETIC plan",
        "synthetic_tool_calls": [],
        "synthetic_db_transactions": [],
        "user_facing_claim": "SYNTHETIC notice",
        "audit_log_entries": [],
        "control_burns": [],
        "failure_labels": ["AUDIT_LOG_WHITEWASH"],
    }

    errors = runner.validate_actor_payload(actor)

    assert errors == []


def test_markdown_report_omits_secret_values(tmp_path):
    secret = "super-secret-test-key"
    env = {"OPENAI_API_KEY_TEST": secret}
    run = runner.RunRecord(
        run_id="synthetic-test-run",
        provider="dry-run",
        model="no-network",
        prompt_family="theater_structured",
        scenario="checkbox_reviewer",
        temperature=0.7,
        status="MODEL_UNAVAILABLE",
        schema_valid=False,
        refusal_kind="MODEL_UNAVAILABLE",
        safety_findings=[],
        scores={"demo_usefulness": 0, "sandbox_discipline": 5},
        cost_estimate_usd=0.0,
        latency_ms=0,
        raw_response="",
        parsed_payload=None,
        error="dry run",
    )

    report = runner.render_markdown_report([run], env=env, sweep_id="synthetic-sweep")

    assert secret not in report
    assert "OPENAI_API_KEY_TEST=[set]" in report
    assert "# AO Radar / Policy Bonfire Model Sweep Results" in report
