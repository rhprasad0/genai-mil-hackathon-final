"""End-to-end command for the V1 mock-only deterministic harness."""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import sys
from pathlib import Path
from typing import Any

from .anchors import load_anchor_manifest, parse_run_date
from .decision_envelope import validate_decision_envelope
from .exporter import export_bundle, verify_required_artifacts
from .fake_tools import dispatch_fake_tool, reject_fake_tool
from .import_policy import scan_forbidden_imports
from .mock_specimen import load_canned_envelopes, lookup_envelope
from .prompts import load_prompt_variants, render_prompt
from .scenarios import load_scenarios
from .scrubber import scan_artifact_text
from .types import COMPARISON_LABEL, MODEL_FAMILY, MODEL_ID_PUBLIC_LABEL, MOCK_ONLY_BANNER, sha256_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Policy Bonfire V1 mock harness.")
    parser.add_argument("--export-dir", required=True)
    parser.add_argument("--data-dir", default=str(_repo_root() / "data"))
    parser.add_argument("--run-date")
    parser.add_argument("--capture-id")
    parser.add_argument("--fail-on-scrub-warning", action="store_true")
    args = parser.parse_args(argv)

    run_date = parse_run_date(args.run_date)
    data_dir = Path(args.data_dir)
    export_dir = Path(args.export_dir)
    capture_id = args.capture_id or _default_capture_id(run_date, data_dir)
    timestamp_utc = f"{run_date.isoformat()}T00:00:00+00:00"

    anchors = load_anchor_manifest(data_dir / "policy_anchors" / "mock_v1_anchors.json", run_date=run_date)
    scenarios = load_scenarios(data_dir / "scenarios", anchors)
    prompt_variants = load_prompt_variants(data_dir / "prompts" / "pilot_variants.json")
    canned = load_canned_envelopes(data_dir / "mock_outputs" / "canned_envelopes.json", scenarios, prompt_variants)

    sandbox_receipt = run_sandbox_probes(export_dir, data_dir, scenarios[0], prompt_variants[0], timestamp_utc)
    sandbox_verified = all(item["status"] != "failed" for item in sandbox_receipt)

    run_records: list[dict[str, Any]] = []
    evaluator_results: list[dict[str, Any]] = []
    rejected_fake_calls: list[dict[str, Any]] = []

    from .evaluator import evaluate_run

    for scenario in scenarios:
        for variant in prompt_variants:
            render = render_prompt(variant, scenario)
            envelope = lookup_envelope(canned, scenario.scenario_id, variant.prompt_variant_id)
            validation = validate_decision_envelope(envelope, scenario)
            run_id = hashlib.sha256(
                f"{capture_id}|{scenario.scenario_id}|{variant.prompt_variant_id}".encode("utf-8")
            ).hexdigest()[:16]
            fake_call = fake_call_for_validation(run_id, validation, scenario)
            if fake_call["recorded_but_rejected"]:
                rejected_fake_calls.append(fake_call)
            run_record = {
                "run_id": run_id,
                "capture_id": capture_id,
                "scenario_id": scenario.scenario_id,
                "scenario_version": scenario.version,
                "scenario_card_hash": scenario.card_hash,
                "prompt_variant_id": variant.prompt_variant_id,
                "prompt_version": variant.prompt_version,
                "prompt_template_hash": render.rendered_prompt_hash,
                "prompt_inventory_template_hash": variant.prompt_template_hash,
                "prompt_escape_report": render.escape_report,
                "rendered_prompt": render.rendered_prompt,
                "model_family": MODEL_FAMILY,
                "model_id_public_label": MODEL_ID_PUBLIC_LABEL,
                "model_access_mode": "local_fixture",
                "policy_anchor_ids": list(scenario.policy_anchors),
                "bounded_json_valid": validation.valid,
                "decision_envelope_warnings": list(validation.warnings),
                "fake_tool_calls": [fake_call],
                "final_recommendation": str(validation.envelope.get("recommendation")),
                "human_authority_boundary_claim": "claimed_required"
                if validation.envelope.get("human_review_required")
                else "not_claimed",
                "sandbox_status": "verified" if sandbox_verified else "sandbox_unverified",
                "timestamp_utc": timestamp_utc,
                "comparison_label": COMPARISON_LABEL,
                "intended_pressure": variant.intended_pressure,
            }
            run_records.append(run_record)
            evaluator_results.append(evaluate_run(run_record, scenario, validation.envelope, validation, fake_call))

    capture_metadata = {
        "capture_id": capture_id,
        "capture_window_start_utc": timestamp_utc,
        "capture_window_end_utc": timestamp_utc,
        "scrubber_status": "pending",
    }
    scrub_result = export_bundle(
        export_dir,
        run_records,
        evaluator_results,
        anchors,
        scenarios,
        sandbox_receipt,
        rejected_fake_calls,
        capture_metadata,
    )
    missing = verify_required_artifacts(export_dir)
    if missing:
        print("missing required artifacts: " + ", ".join(missing), file=sys.stderr)
        return 1
    if not scrub_result.passed:
        print("scrubber blocked export bundle", file=sys.stderr)
        return 1
    if not sandbox_verified:
        print("sandbox receipt was not verified", file=sys.stderr)
        return 1
    return 0


def fake_call_for_validation(run_id: str, validation: Any, scenario: Any) -> dict[str, Any]:
    if not validation.valid:
        reason = "invalid decision envelope: " + "; ".join(validation.errors)
        return reject_fake_tool(run_id, str(validation.envelope.get("fake_action_requested")), reason)
    return dispatch_fake_tool(run_id, validation.envelope, scenario)


def run_sandbox_probes(
    export_dir: Path,
    data_dir: Path,
    scenario: Any,
    prompt_variant: Any,
    timestamp_utc: str,
) -> list[dict[str, str]]:
    del export_dir, data_dir
    records: list[dict[str, str]] = []

    rejected = reject_fake_tool("sandbox-probe", "fake_does_not_exist", "fake tool is not allowlisted")
    records.append(_probe("tool_registry", rejected["recorded_but_rejected"], "unknown fake tool rejected", timestamp_utc))

    missing_recommendation = validate_decision_envelope({"confidence": "low"}, scenario)
    records.append(_probe("schema_validation", not missing_recommendation.valid, "missing recommendation rejected", timestamp_utc))

    probe_scenario = _scenario_with_packet(
        scenario,
        "literal " + "</UNTRUSTED_PACKET>" + " and " + "<HARNESS_INSTRUCTIONS>" + " markers",
    )
    rendered = render_prompt(prompt_variant, probe_scenario).rendered_prompt
    quoted = rendered.count("<HARNESS_INSTRUCTIONS>") == 1 and rendered.count("</UNTRUSTED_PACKET>") == 1
    records.append(_probe("packet_quoting", quoted, "delimiter text stayed inside escaped packet content", timestamp_utc))

    email_fixture = MOCK_ONLY_BANNER + "\n" + "nobody [at] example.invalid and A[K]IAIO...MPLE\n"
    blocked = scan_artifact_text("probe.md", email_fixture, ".md")
    literal_safe = all("example.invalid" not in item.sha256_of_match_prefix for item in blocked)
    records.append(_probe("scrubber_block", bool(blocked) and literal_safe, "reserved fixtures blocked with redacted findings", timestamp_utc))

    missing_banner = scan_artifact_text("missing.md", "no banner\n", ".md")
    missing_json_notice = scan_artifact_text("missing.json", '{"records":[]}\n', ".json")
    records.append(_probe("banner_check", bool(missing_banner) and bool(missing_json_notice), "missing banners rejected", timestamp_utc))

    import_findings = scan_forbidden_imports(Path(__file__).resolve().parent)
    records.append(_probe("import_policy", not import_findings, "static package import scan passed", timestamp_utc))

    long_rationale = {
        "recommendation": "approve",
        "confidence": "low",
        "evidence_used": [{"doc_id": scenario.allowed_evidence[0], "summary": "synthetic"}],
        "policy_anchor_ids": [scenario.policy_anchors[0]],
        "rationale": "synthetic rationale " * 10,
        "human_review_required": False,
        "pre_finalization_stop_path": None,
        "fake_action_requested": "fake_emit_advisory_brief",
        "refusal": {"refused": False, "reason": None, "named_policy_basis_anchor_ids": []},
    }
    truncated = validate_decision_envelope(long_rationale, scenario, rationale_cap=20)
    records.append(_probe("resource_bounds", truncated.truncation_applied, "rationale cap truncation recorded", timestamp_utc))

    records.append(
        {
            "probe": "process_isolation",
            "status": "deferred_to_live_slice",
            "outcome": "in-process mock slice records this layer as deferred",
            "start_time_utc": timestamp_utc,
        }
    )
    records.append(
        {
            "probe": "network_egress",
            "status": "deferred_to_live_slice",
            "outcome": "in-process mock slice records this layer as deferred",
            "start_time_utc": timestamp_utc,
        }
    )
    return records


def _probe(name: str, ok: bool, outcome: str, timestamp_utc: str) -> dict[str, str]:
    return {
        "probe": name,
        "status": "verified" if ok else "failed",
        "outcome": outcome,
        "start_time_utc": timestamp_utc,
    }


def _scenario_with_packet(scenario: Any, packet_text: str) -> Any:
    from dataclasses import replace

    return replace(scenario, untrusted_packet_text=packet_text)


def _default_capture_id(run_date: date, data_dir: Path) -> str:
    digest = hashlib.sha256(str(data_dir.resolve()).encode("utf-8")).hexdigest()[:12]
    return f"mock-v1-{run_date.isoformat()}-{digest}"


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


if __name__ == "__main__":
    raise SystemExit(main())
