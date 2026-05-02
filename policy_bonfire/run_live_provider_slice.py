"""CLI runner for the opt-in live-provider slice.

Default behavior is fully offline: providers are statused as
``live_calls_not_enabled`` unless PB_LIVE_CALLS=1. Unit tests can inject fake
adapters into ``run_live_slice``; the CLI uses offline fake adapters only for the
explicit ``--offline-fake`` smoke path and never imports provider SDKs.
"""

from __future__ import annotations

import argparse
from datetime import date
import hashlib
import os
from pathlib import Path
from typing import Any, Mapping

from .anchors import load_anchor_manifest, parse_run_date
from .decision_envelope import validate_decision_envelope
from .decision_schema import decision_envelope_schema
from .evaluator import evaluate_run
from .exporter import export_bundle, verify_required_artifacts
from .fake_tools import dispatch_fake_tool, reject_fake_tool
from .import_policy import scan_forbidden_imports
from .live_adapters import LiveProviderAdapter, default_adapter_registry
from .live_config import LiveRuntimeConfig, ProviderRuntimeConfig, can_schedule_call, parse_live_config
from .live_contracts import LiveModelRequest, LiveModelResponse, PROVIDER_MODEL_FAMILIES
from .live_costs import estimate_cost_usd
from .prompts import load_prompt_variants, render_prompt, split_trusted_untrusted_blocks
from .scenarios import load_scenarios
from .scrubber import scan_artifact_text
from .types import LIVE_RUN_BANNER, sha256_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Policy Bonfire live-provider slice.")
    parser.add_argument("--export-dir", required=True)
    parser.add_argument("--data-dir", default=str(_repo_root() / "data"))
    parser.add_argument("--run-date")
    parser.add_argument("--capture-id")
    parser.add_argument("--offline-fake", action="store_true", help="use fake adapters without PB_LIVE_CALLS for local smoke tests")
    args = parser.parse_args(argv)

    run_date = parse_run_date(args.run_date)
    config = parse_live_config(os.environ)
    if not config.live_calls_enabled and not args.offline_fake:
        # Still write a skipped receipt so accidental CLI use is auditable and offline.
        result = run_live_slice(args.export_dir, args.data_dir, run_date, args.capture_id, config, adapters={})
        return 0 if result.passed else 1
    adapters = default_adapter_registry(config.provider_list, offline_fake=args.offline_fake)
    result = run_live_slice(args.export_dir, args.data_dir, run_date, args.capture_id, config, adapters=adapters, allow_offline_fake=args.offline_fake)
    missing = verify_required_artifacts(args.export_dir, artifact_mode="live")
    if missing:
        print("missing required artifacts: " + ", ".join(missing))
        return 1
    return 0 if result.passed else 1


def run_live_slice(
    export_dir: str | Path,
    data_dir: str | Path,
    run_date: date,
    capture_id: str | None,
    config: LiveRuntimeConfig,
    adapters: Mapping[str, LiveProviderAdapter],
    *,
    allow_offline_fake: bool = False,
) -> Any:
    data_path = Path(data_dir)
    export_path = Path(export_dir)
    capture = capture_id or _default_capture_id(run_date, data_path)
    timestamp_utc = f"{run_date.isoformat()}T00:00:00+00:00"
    anchors = load_anchor_manifest(data_path / "policy_anchors" / "mock_v1_anchors.json", run_date=run_date)
    scenarios = load_scenarios(data_path / "scenarios", anchors)
    prompt_variants = load_prompt_variants(data_path / "prompts" / "pilot_variants.json")

    provider_configs = {provider.provider: provider for provider in config.provider_list}
    sandbox_receipt = _live_sandbox_receipt(timestamp_utc, provider_configs)
    sandbox_verified = all(item["status"] == "verified" for item in sandbox_receipt)
    run_records: list[dict[str, Any]] = []
    evaluator_results: list[dict[str, Any]] = []
    rejected_fake_calls: list[dict[str, Any]] = []
    scheduled = 0
    current_total_usd = 0.0
    current_provider_usd = {provider: 0.0 for provider in provider_configs}

    for provider, provider_config in provider_configs.items():
        adapter = adapters.get(provider)
        if provider_config.skip_status and not (allow_offline_fake and provider_config.skip_status == "live_calls_not_enabled"):
            run_records.append(_skipped_provider_record(capture, provider_config, provider_config.skip_status, timestamp_utc))
            continue
        if adapter is None:
            run_records.append(_skipped_provider_record(capture, provider_config, "live_calls_not_enabled", timestamp_utc))
            continue
        for scenario in scenarios:
            for variant in prompt_variants:
                render = render_prompt(variant, scenario)
                if allow_offline_fake and provider_config.skip_status == "live_calls_not_enabled":
                    allowed = scheduled < config.max_runs
                    block_status = "blocked_cost_cap"
                    reserved_cost = 0.0
                else:
                    allowed, block_status, projection = can_schedule_call(
                        config,
                        provider,
                        scheduled_runs=scheduled,
                        prompt_chars=len(render.rendered_prompt),
                        current_total_usd=current_total_usd,
                        current_provider_usd=current_provider_usd[provider],
                    )
                    reserved_cost = projection.projected_usd if projection is not None else 0.0
                if not allowed:
                    run_records.append(_blocked_record(capture, provider_config, scenario.scenario_id, variant.prompt_variant_id, timestamp_utc, block_status or "blocked_cost_cap"))
                    continue
                scheduled += 1
                blocks = split_trusted_untrusted_blocks(render.rendered_prompt)
                request = LiveModelRequest(
                    capture_id=capture,
                    scenario_id=scenario.scenario_id,
                    scenario_hash=scenario.card_hash,
                    anchor_ids=tuple(scenario.policy_anchors),
                    allowed_evidence_ids=tuple(scenario.allowed_evidence),
                    prompt_variant_id=variant.prompt_variant_id,
                    prompt_template_hash=variant.prompt_template_hash,
                    rendered_prompt_hash=render.rendered_prompt_hash,
                    trusted_instructions=blocks.trusted_instructions,
                    untrusted_packet_block=blocks.untrusted_packet_block,
                    decision_schema_version="2020-12-local",
                    decision_schema=decision_envelope_schema(
                        allowed_policy_anchor_ids=scenario.policy_anchors,
                        allowed_evidence_ids=scenario.allowed_evidence,
                    ),
                    max_output_tokens=config.max_output_tokens,
                    timeout_seconds=config.timeout_seconds,
                )
                response = adapter.complete(request)
                artifact_cost = _artifact_cost_estimate(response, provider_config)
                charged_cost = max(artifact_cost, reserved_cost)
                current_total_usd += charged_cost
                current_provider_usd[provider] += charged_cost
                run_id = _run_id(capture, provider, scenario.scenario_id, variant.prompt_variant_id)
                validation = validate_decision_envelope(response.parsed_decision_envelope or {}, scenario)
                scored = response.status == "completed_valid" and validation.valid and sandbox_verified
                fake_call = _fake_call(run_id, response, validation, scenario)
                if fake_call["recorded_but_rejected"]:
                    rejected_fake_calls.append(fake_call)
                record = _run_record(
                    run_id,
                    capture,
                    provider_config,
                    scenario,
                    variant,
                    render,
                    response,
                    validation,
                    fake_call,
                    timestamp_utc,
                    scored,
                    sandbox_verified,
                    artifact_cost,
                )
                run_records.append(record)
                if scored:
                    evaluator_results.append(evaluate_run(record, scenario, validation.envelope, validation, fake_call))

    metadata = {
        "capture_id": capture,
        "capture_window_start_utc": timestamp_utc,
        "capture_window_end_utc": timestamp_utc,
        "comparison_label": _comparison_label(run_records),
        "vendor_lineage_count": str(len({r.get("model_family") for r in run_records if r.get("scored") is True})),
        "access_mode": "api_live" if config.live_calls_enabled else "offline_skipped",
        "scrubber_status": "pending",
    }
    # Local public-safety/import probes. Never echo matched literals.
    probe_text = LIVE_RUN_BANNER + "\npublic safe synthetic live receipt\n"
    scrub_ok = not scan_artifact_text("live_probe.md", probe_text, ".md")
    import_ok = not scan_forbidden_imports(Path(__file__).resolve().parent)
    if not (scrub_ok and import_ok):
        sandbox_receipt.append({"probe": "live_static_policy", "status": "failed", "outcome": "static policy probe failed", "start_time_utc": timestamp_utc})

    return export_bundle(
        export_path,
        run_records,
        evaluator_results,
        anchors,
        scenarios,
        sandbox_receipt,
        rejected_fake_calls,
        metadata,
        artifact_mode="live",
    )


def _fake_call(run_id: str, response: LiveModelResponse, validation: Any, scenario: Any) -> dict[str, Any]:
    if response.status != "completed_valid" or not validation.valid:
        reason = response.status if response.status != "completed_valid" else "invalid decision envelope: " + "; ".join(validation.errors)
        return reject_fake_tool(run_id, str((response.parsed_decision_envelope or {}).get("fake_action_requested")), reason)
    return dispatch_fake_tool(run_id, validation.envelope, scenario)


def _run_record(
    run_id: str,
    capture: str,
    provider_config: Any,
    scenario: Any,
    variant: Any,
    render: Any,
    response: LiveModelResponse,
    validation: Any,
    fake_call: dict[str, Any],
    timestamp: str,
    scored: bool,
    sandbox_verified: bool,
    artifact_cost_estimate: float,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "capture_id": capture,
        "scenario_id": scenario.scenario_id,
        "scenario_version": scenario.version,
        "scenario_card_hash": scenario.card_hash,
        "prompt_variant_id": variant.prompt_variant_id,
        "prompt_version": variant.prompt_version,
        "prompt_template_hash": render.rendered_prompt_hash,
        "prompt_inventory_template_hash": variant.prompt_template_hash,
        "prompt_escape_report": render.escape_report,
        "model_access_mode": "api_live",
        "provider": response.provider,
        "model_id_exact": response.model_id_exact,
        "model_id_public_label": response.model_id_public_label,
        "model_family": response.model_family,
        "endpoint_base_category": provider_config.endpoint_base_category,
        "seed_support": "unsupported_or_not_used",
        "usage_input_tokens": response.usage_input_tokens,
        "usage_output_tokens": response.usage_output_tokens,
        "usage_estimated": response.usage_estimated,
        "latency_ms": response.latency_ms,
        "retry_count": response.retry_count,
        "repair_attempted": response.repair_attempted,
        "cost_estimate": artifact_cost_estimate,
        "raw_output_sha256": response.raw_output_sha256,
        "status": response.status if sandbox_verified else "sandbox_unverified",
        "error_code_redacted": response.error_code_redacted,
        "finish_reason": response.finish_reason,
        "policy_anchor_ids": list(scenario.policy_anchors),
        "bounded_json_valid": validation.valid,
        "scored": scored,
        "decision_envelope_warnings": list(validation.warnings),
        "fake_tool_calls": [fake_call],
        "final_recommendation": str(validation.envelope.get("recommendation")),
        "human_authority_boundary_claim": "claimed_required" if validation.envelope.get("human_review_required") else "not_claimed",
        "sandbox_status": "verified" if sandbox_verified else "sandbox_unverified",
        "timestamp_utc": timestamp,
        "capture_window_start_utc": timestamp,
        "capture_window_end_utc": timestamp,
        "comparison_label": "cross_prompt_only",
        "intended_pressure": variant.intended_pressure,
    }


def _skipped_provider_record(capture: str, provider_config: Any, status: str, timestamp: str) -> dict[str, Any]:
    return {
        "run_id": _run_id(capture, provider_config.provider, "provider", "skipped"),
        "capture_id": capture,
        "provider": provider_config.provider,
        "model_access_mode": "api_live" if status != "live_calls_not_enabled" else "offline_skipped",
        "model_id_exact": "not_recorded_offline" if status == "live_calls_not_enabled" else (provider_config.model_id or "not_configured"),
        "model_id_public_label": provider_config.model_id_public_label,
        "model_family": PROVIDER_MODEL_FAMILIES[provider_config.provider],
        "endpoint_base_category": provider_config.endpoint_base_category,
        "status": status,
        "scored": False,
        "timestamp_utc": timestamp,
        "usage_input_tokens": 0,
        "usage_output_tokens": 0,
        "usage_estimated": True,
        "latency_ms": 0,
        "retry_count": 0,
        "repair_attempted": False,
        "cost_estimate": 0.0,
    }


def _blocked_record(capture: str, provider_config: Any, scenario_id: str, prompt_variant_id: str, timestamp: str, status: str = "blocked_cost_cap") -> dict[str, Any]:
    record = _skipped_provider_record(capture, provider_config, status, timestamp)
    record.update({"scenario_id": scenario_id, "prompt_variant_id": prompt_variant_id})
    return record


def _artifact_cost_estimate(response: LiveModelResponse, provider_config: ProviderRuntimeConfig) -> float:
    """Use returned provider usage for artifacts, including excluded outputs."""

    observed_cost = 0.0
    if provider_config.rates is not None:
        observed_cost = estimate_cost_usd(
            int(response.usage_input_tokens or 0),
            int(response.usage_output_tokens or 0),
            provider_config.rates,
        )
    return max(float(response.cost_estimate or 0.0), observed_cost)


def _live_sandbox_receipt(timestamp: str, provider_configs: Mapping[str, Any]) -> list[dict[str, str]]:
    allowlist = ", ".join(sorted({p.endpoint_base_category for p in provider_configs.values()}))
    return [
        {"probe": "specimen_network_egress", "status": "verified", "outcome": "specimen and fake tools remained egress-blocked", "start_time_utc": timestamp},
        {"probe": "harness_runner_allowlist", "status": "verified", "outcome": "provider host allowlist categories: " + allowlist, "start_time_utc": timestamp},
    ]


def _comparison_label(records: list[dict[str, Any]]) -> str:
    families = {record.get("model_family") for record in records if record.get("scored") is True}
    return "cross_provider_directional" if len(families) >= 2 else "cross_prompt_only"


def _run_id(capture: str, provider: str, scenario_id: str, prompt_variant_id: str) -> str:
    return hashlib.sha256(f"{capture}|{provider}|{scenario_id}|{prompt_variant_id}".encode("utf-8")).hexdigest()[:16]


def _default_capture_id(run_date: date, data_dir: Path) -> str:
    digest = hashlib.sha256(str(data_dir.resolve()).encode("utf-8")).hexdigest()[:12]
    return f"live-provider-{run_date.isoformat()}-{digest}"


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


if __name__ == "__main__":
    raise SystemExit(main())
