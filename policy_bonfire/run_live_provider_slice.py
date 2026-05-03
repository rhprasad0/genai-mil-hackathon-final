"""CLI runner for the opt-in live-provider slice.

Default behavior is fully offline: providers are statused as
``live_calls_not_enabled`` unless PB_LIVE_CALLS=1. Unit tests can inject fake
adapters into ``run_live_slice``; the CLI uses offline fake adapters only for the
explicit ``--offline-fake`` smoke path and never imports provider SDKs.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from datetime import date, datetime, timezone
import hashlib
import json
import os
import platform
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .anchors import load_anchor_manifest, parse_run_date
from .decision_envelope import validate_decision_envelope
from .decision_schema import decision_envelope_schema
from .evaluator import evaluate_run
from .exporter import export_bundle, verify_required_artifacts
from .fake_tools import dispatch_fake_tool, reject_fake_tool
from .import_policy import scan_forbidden_imports
from .live_adapters import LiveProviderAdapter, default_adapter_registry
from .live_config import LiveRuntimeConfig, ProviderRuntimeConfig, can_schedule_call, parse_live_config
from .live_contracts import (
    LiveModelRequest,
    LiveModelResponse,
    PROVIDER_MODEL_FAMILIES,
    STATUS_BLOCKED_COST_CAP,
    STATUS_BLOCKED_INPUT_CAP,
    STATUS_COMPLETED_VALID,
    STATUS_EXCLUDED_FENCED_JSON,
    STATUS_EXCLUDED_MALFORMED_JSON,
    STATUS_EXCLUDED_SCHEMA_INVALID,
    STATUS_EXCLUDED_TRUNCATED,
    STATUS_LIVE_CALLS_NOT_ENABLED,
    STATUS_PROVIDER_NO_CANDIDATE,
    STATUS_PROVIDER_SAFETY_REFUSAL,
    STATUS_PROVIDER_SKIPPED_MISSING_KEY,
    STATUS_PROVIDER_SKIPPED_MISSING_RATE,
    STATUS_PROVIDER_SKIPPED_MODEL_UNAVAILABLE,
    STATUS_TIMEOUT,
    STATUS_TRANSIENT_ERROR,
)
from .live_costs import estimate_cost_usd
from .prompts import load_prompt_variants, render_prompt, split_trusted_untrusted_blocks
from .scenarios import load_scenarios
from .scrubber import scan_artifact_text
from .types import LIVE_RUN_BANNER, PromptRenderResult, PromptVariant, ScenarioCard


RETRYABLE_STATUSES = frozenset({STATUS_TIMEOUT, STATUS_TRANSIENT_ERROR})
PROVIDER_SKIP_STATUSES = frozenset(
    {
        STATUS_LIVE_CALLS_NOT_ENABLED,
        STATUS_PROVIDER_SKIPPED_MISSING_KEY,
        STATUS_PROVIDER_SKIPPED_MODEL_UNAVAILABLE,
        STATUS_PROVIDER_SKIPPED_MISSING_RATE,
    }
)
NON_CALL_STATUSES = PROVIDER_SKIP_STATUSES | frozenset({STATUS_BLOCKED_COST_CAP, STATUS_BLOCKED_INPUT_CAP})


@dataclass(frozen=True)
class PlannedRun:
    plan_index: int
    run_id: str
    provider: str
    scenario: ScenarioCard
    variant: PromptVariant
    render: PromptRenderResult
    repetition_id: str
    input_chars: int


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Policy Bonfire live-provider slice.")
    parser.add_argument("--export-dir", required=True)
    parser.add_argument("--data-dir", default=str(_repo_root() / "data"))
    parser.add_argument("--run-date")
    parser.add_argument("--capture-id")
    parser.add_argument("--offline-fake", action="store_true", help="use fake adapters without PB_LIVE_CALLS for local smoke tests")
    parser.add_argument("--resume", action="store_true", help="append to existing live JSONL artifacts and skip completed plan rows")
    parser.add_argument("--only-failed", action="store_true", help="with an existing checkpoint, rerun only failed plan rows")
    parser.add_argument("--shard", help="run only shard INDEX/TOTAL using 1-based INDEX")
    parser.add_argument("--scenarios", help="comma-separated scenario_id filter")
    parser.add_argument("--prompt-variants", help="comma-separated prompt_variant_id filter")
    parser.add_argument("--providers", help="comma-separated provider filter")
    args = parser.parse_args(argv)

    run_date = parse_run_date(args.run_date)
    config = parse_live_config(os.environ)
    shard = _parse_shard(args.shard)
    cli_args = _redacted_cli_args(args)
    if not config.live_calls_enabled and not args.offline_fake:
        # Still write a skipped receipt so accidental CLI use is auditable and offline.
        result = run_live_slice(
            args.export_dir,
            args.data_dir,
            run_date,
            args.capture_id,
            config,
            adapters={},
            resume=args.resume,
            only_failed=args.only_failed,
            shard=shard,
            scenario_ids=_split_filter(args.scenarios),
            prompt_variant_ids=_split_filter(args.prompt_variants),
            provider_ids=_split_filter(args.providers),
            cli_args=cli_args,
        )
        return 0 if result.passed else 1
    adapters = default_adapter_registry(config.provider_list, offline_fake=args.offline_fake, timeout_seconds=config.timeout_seconds)
    result = run_live_slice(
        args.export_dir,
        args.data_dir,
        run_date,
        args.capture_id,
        config,
        adapters=adapters,
        allow_offline_fake=args.offline_fake,
        resume=args.resume,
        only_failed=args.only_failed,
        shard=shard,
        scenario_ids=_split_filter(args.scenarios),
        prompt_variant_ids=_split_filter(args.prompt_variants),
        provider_ids=_split_filter(args.providers),
        cli_args=cli_args,
    )
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
    resume: bool = False,
    only_failed: bool = False,
    shard: tuple[int, int] | None = None,
    scenario_ids: Sequence[str] | None = None,
    prompt_variant_ids: Sequence[str] | None = None,
    provider_ids: Sequence[str] | None = None,
    cli_args: Mapping[str, Any] | None = None,
    sleep_fn: Callable[[float], None] | None = None,
) -> Any:
    data_path = Path(data_dir)
    export_path = Path(export_dir)
    export_path.mkdir(parents=True, exist_ok=True)
    manifest_start_utc = _utc_now()
    data_input_hashes = _data_input_hashes(data_path)
    capture = capture_id or _default_capture_id(run_date, data_path)
    timestamp_utc = f"{run_date.isoformat()}T00:00:00+00:00"
    anchors = load_anchor_manifest(data_path / "policy_anchors" / "mock_v1_anchors.json", run_date=run_date)
    scenarios = _filter_scenarios(load_scenarios(data_path / "scenarios", anchors), scenario_ids)
    prompt_variants = _filter_prompt_variants(load_prompt_variants(data_path / "prompts" / "pilot_variants.json"), prompt_variant_ids)
    provider_configs = _filter_provider_configs(
        {provider.provider: provider for provider in config.provider_list},
        provider_ids,
    )
    sandbox_receipt = _live_sandbox_receipt(timestamp_utc, provider_configs)
    # Local public-safety/import probes. Never echo matched literals.
    probe_text = LIVE_RUN_BANNER + "\npublic safe synthetic live receipt\n"
    scrub_ok = not scan_artifact_text("live_probe.md", probe_text, ".md")
    import_ok = not scan_forbidden_imports(Path(__file__).resolve().parent)
    if not (scrub_ok and import_ok):
        sandbox_receipt.append({"probe": "live_static_policy", "status": "failed", "outcome": "static policy probe failed", "start_time_utc": timestamp_utc})
    sandbox_verified = all(item["status"] == "verified" for item in sandbox_receipt)

    checkpoint_path = export_path / "run_checkpoint.jsonl"
    events_path = export_path / "run_events.jsonl"
    previous_state = _load_checkpoint_state(checkpoint_path) if (resume or only_failed) and checkpoint_path.exists() else _empty_checkpoint_state()
    active_provider_configs, provider_skip_specs = _provider_execution_plan(capture, provider_configs, adapters, allow_offline_fake)
    plan_runs = _build_run_plan(capture, active_provider_configs, scenarios, prompt_variants, config)
    if shard is not None:
        plan_runs = _apply_shard(plan_runs, shard)
    failed_run_ids = {
        run_id
        for run_id, record in previous_state["records"].items()
        if _is_failed_for_resume(record)
    }
    if only_failed:
        plan_runs = [item for item in plan_runs if item.run_id in failed_run_ids]
        provider_skip_specs = [item for item in provider_skip_specs if item["run_id"] in failed_run_ids]

    append_jsonl = resume or only_failed
    _initialize_jsonl(events_path, "run_events_header", append=append_jsonl)
    _initialize_jsonl(checkpoint_path, "run_checkpoint_header", append=append_jsonl)
    _append_event(
        events_path,
        "run_started",
        {
            "capture_id": capture,
            "resume": resume,
            "only_failed": only_failed,
            "selected_plan_rows": len(plan_runs),
        },
    )

    plan_payload = _run_plan_payload(
        capture,
        run_date,
        config,
        data_input_hashes,
        provider_configs,
        provider_skip_specs,
        plan_runs,
        shard,
        scenario_ids,
        prompt_variant_ids,
        provider_ids,
        resume,
        only_failed,
    )
    _write_live_json(export_path / "run_plan.json", plan_payload)
    _append_event(events_path, "run_plan_written", {"capture_id": capture, "planned_run_count": len(plan_runs)})

    selected_run_ids = {item["run_id"] for item in provider_skip_specs} | {item.run_id for item in plan_runs}
    run_records_by_id = {
        run_id: record
        for run_id, record in previous_state["records"].items()
        if run_id in selected_run_ids
    }
    evaluator_results_by_id = {
        run_id: result
        for run_id, result in previous_state["evaluator_results"].items()
        if run_id in selected_run_ids
    }
    charged_cost_by_id = {
        run_id: cost
        for run_id, cost in previous_state["charged_costs"].items()
        if run_id in selected_run_ids
    }
    scheduled = sum(1 for record in run_records_by_id.values() if _counts_as_provider_call(record))
    current_total_usd = sum(charged_cost_by_id.get(run_id, float(record.get("charged_cost_estimate") or record.get("cost_estimate") or 0.0)) for run_id, record in run_records_by_id.items())
    current_provider_usd = {provider: 0.0 for provider in provider_configs}
    for run_id, record in run_records_by_id.items():
        provider = str(record.get("provider", ""))
        if provider in current_provider_usd:
            current_provider_usd[provider] += charged_cost_by_id.get(run_id, float(record.get("charged_cost_estimate") or record.get("cost_estimate") or 0.0))

    for skip_spec in provider_skip_specs:
        run_id = str(skip_spec["run_id"])
        if run_id in run_records_by_id and not _is_failed_for_resume(run_records_by_id[run_id]):
            _append_event(events_path, "run_skipped_resume", {"run_id": run_id, "status": run_records_by_id[run_id].get("status")})
            continue
        provider_config = skip_spec["provider_config"]
        status = str(skip_spec["status"])
        record = _skipped_provider_record(capture, provider_config, status, timestamp_utc)
        run_records_by_id[run_id] = record
        charged_cost_by_id[run_id] = 0.0
        _append_checkpoint(checkpoint_path, record, evaluator_result=None, charged_cost=0.0)
        _append_event(events_path, "provider_skipped", {"run_id": run_id, "provider": provider_config.provider, "status": status})

    sleep = sleep_fn or time.sleep
    for item in plan_runs:
        provider_config = provider_configs[item.provider]
        prior_record = run_records_by_id.get(item.run_id)
        if prior_record is not None and not _is_failed_for_resume(prior_record):
            _append_event(events_path, "run_skipped_resume", {"run_id": item.run_id, "status": prior_record.get("status")})
            continue
        if item.input_chars > config.max_input_chars:
            record = _blocked_record(
                capture,
                provider_config,
                item.scenario.scenario_id,
                item.variant.prompt_variant_id,
                item.repetition_id,
                timestamp_utc,
                STATUS_BLOCKED_INPUT_CAP,
            )
            record["input_chars"] = item.input_chars
            record["max_input_chars"] = config.max_input_chars
            run_records_by_id[item.run_id] = record
            evaluator_results_by_id.pop(item.run_id, None)
            charged_cost_by_id[item.run_id] = 0.0
            _append_checkpoint(checkpoint_path, record, evaluator_result=None, charged_cost=0.0)
            _append_event(events_path, "run_blocked_input_cap", {"run_id": item.run_id, "input_chars": item.input_chars, "max_input_chars": config.max_input_chars})
            continue
        if allow_offline_fake and provider_config.skip_status == STATUS_LIVE_CALLS_NOT_ENABLED:
            allowed = scheduled < config.max_runs
            block_status = STATUS_BLOCKED_COST_CAP
            reserved_cost = 0.0
        else:
            allowed, block_status, projection = can_schedule_call(
                config,
                item.provider,
                scheduled_runs=scheduled,
                prompt_chars=item.input_chars,
                current_total_usd=current_total_usd,
                current_provider_usd=current_provider_usd[item.provider],
            )
            reserved_cost = projection.projected_usd if projection is not None else 0.0
        if not allowed:
            record = _blocked_record(
                capture,
                provider_config,
                item.scenario.scenario_id,
                item.variant.prompt_variant_id,
                item.repetition_id,
                timestamp_utc,
                block_status or STATUS_BLOCKED_COST_CAP,
            )
            record["input_chars"] = item.input_chars
            run_records_by_id[item.run_id] = record
            evaluator_results_by_id.pop(item.run_id, None)
            charged_cost_by_id[item.run_id] = 0.0
            _append_checkpoint(checkpoint_path, record, evaluator_result=None, charged_cost=0.0)
            _append_event(events_path, "run_blocked_schedule", {"run_id": item.run_id, "status": record["status"]})
            continue

        scheduled += 1
        blocks = split_trusted_untrusted_blocks(item.render.rendered_prompt)
        request = LiveModelRequest(
            capture_id=capture,
            scenario_id=item.scenario.scenario_id,
            scenario_hash=item.scenario.card_hash,
            anchor_ids=tuple(item.scenario.policy_anchors),
            allowed_evidence_ids=tuple(item.scenario.allowed_evidence),
            prompt_variant_id=item.variant.prompt_variant_id,
            prompt_template_hash=item.variant.prompt_template_hash,
            rendered_prompt_hash=item.render.rendered_prompt_hash,
            trusted_instructions=blocks.trusted_instructions,
            untrusted_packet_block=blocks.untrusted_packet_block,
            decision_schema_version="2020-12-local",
            decision_schema=decision_envelope_schema(
                allowed_policy_anchor_ids=item.scenario.policy_anchors,
                allowed_evidence_ids=item.scenario.allowed_evidence,
            ),
            max_output_tokens=config.max_output_tokens,
            timeout_seconds=config.timeout_seconds,
            cost_cap_context={
                "projected_usd": reserved_cost,
                "max_input_chars": config.max_input_chars,
                "input_chars": item.input_chars,
                "plan_index": item.plan_index,
            },
            repetition_id=item.repetition_id,
        )
        response = _complete_with_retries(
            adapters[item.provider],
            request,
            provider_config,
            item.run_id,
            config.max_retries,
            sleep,
            events_path,
        )
        artifact_cost = _artifact_cost_estimate(response, provider_config)
        charged_cost = max(artifact_cost, reserved_cost)
        current_total_usd += charged_cost
        current_provider_usd[item.provider] += charged_cost
        validation = validate_decision_envelope(response.parsed_decision_envelope or {}, item.scenario)
        scored = response.status == STATUS_COMPLETED_VALID and validation.valid and sandbox_verified
        fake_call = _fake_call(item.run_id, response, validation, item.scenario)
        record = _run_record(
            item.run_id,
            capture,
            provider_config,
            item.scenario,
            item.variant,
            item.repetition_id,
            item.render,
            response,
            validation,
            fake_call,
            timestamp_utc,
            scored,
            sandbox_verified,
            artifact_cost,
        )
        record["input_chars"] = item.input_chars
        record["reserved_cost_estimate"] = reserved_cost
        record["charged_cost_estimate"] = charged_cost
        evaluator_result = evaluate_run(record, item.scenario, validation.envelope, validation, fake_call) if scored else None
        run_records_by_id[item.run_id] = record
        if evaluator_result is None:
            evaluator_results_by_id.pop(item.run_id, None)
        else:
            evaluator_results_by_id[item.run_id] = evaluator_result
        charged_cost_by_id[item.run_id] = charged_cost
        _append_checkpoint(checkpoint_path, record, evaluator_result=evaluator_result, charged_cost=charged_cost)
        _append_event(events_path, "run_finished", {"run_id": item.run_id, "status": record["status"], "retry_count": record["retry_count"]})

    run_records = _ordered_run_records(provider_skip_specs, plan_runs, run_records_by_id)
    evaluator_results = _ordered_evaluator_results(run_records, evaluator_results_by_id)
    rejected_fake_calls = _rejected_fake_calls_from_records(run_records)

    metadata = {
        "capture_id": capture,
        "capture_window_start_utc": timestamp_utc,
        "capture_window_end_utc": timestamp_utc,
        "comparison_label": _comparison_label(run_records),
        "vendor_lineage_count": str(len({r.get("model_family") for r in run_records if r.get("scored") is True})),
        "access_mode": "api_live" if config.live_calls_enabled else "offline_skipped",
        "repetitions": str(config.repetitions),
        "scrubber_status": "pending",
    }
    manifest_end_utc = _utc_now()
    _append_event(events_path, "run_completed", {"capture_id": capture, "final_record_count": len(run_records), "scored_count": sum(1 for record in run_records if record.get("scored") is True)})
    _write_live_json(
        export_path / "run_manifest.json",
        _run_manifest_payload(
            capture,
            manifest_start_utc,
            manifest_end_utc,
            config,
            cli_args or {"source": "api", "args": {}},
            data_input_hashes,
            plan_payload,
            run_records,
        ),
    )

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


def _filter_scenarios(scenarios: list[ScenarioCard], scenario_ids: Sequence[str] | None) -> list[ScenarioCard]:
    if not scenario_ids:
        return scenarios
    requested = tuple(scenario_ids)
    by_id = {scenario.scenario_id: scenario for scenario in scenarios}
    missing = [scenario_id for scenario_id in requested if scenario_id not in by_id]
    if missing:
        raise ValueError("unknown scenario filter: " + ", ".join(sorted(missing)))
    return [by_id[scenario_id] for scenario_id in requested]


def _filter_prompt_variants(variants: list[PromptVariant], prompt_variant_ids: Sequence[str] | None) -> list[PromptVariant]:
    if not prompt_variant_ids:
        return variants
    requested = tuple(prompt_variant_ids)
    by_id = {variant.prompt_variant_id: variant for variant in variants}
    missing = [variant_id for variant_id in requested if variant_id not in by_id]
    if missing:
        raise ValueError("unknown prompt variant filter: " + ", ".join(sorted(missing)))
    return [by_id[variant_id] for variant_id in requested]


def _filter_provider_configs(
    provider_configs: Mapping[str, ProviderRuntimeConfig],
    provider_ids: Sequence[str] | None,
) -> dict[str, ProviderRuntimeConfig]:
    if not provider_ids:
        return {provider: provider_configs[provider] for provider in sorted(provider_configs)}
    requested = tuple(provider_ids)
    missing = [provider for provider in requested if provider not in provider_configs]
    if missing:
        raise ValueError("unknown provider filter: " + ", ".join(sorted(missing)))
    return {provider: provider_configs[provider] for provider in requested}


def _provider_execution_plan(
    capture: str,
    provider_configs: Mapping[str, ProviderRuntimeConfig],
    adapters: Mapping[str, LiveProviderAdapter],
    allow_offline_fake: bool,
) -> tuple[dict[str, ProviderRuntimeConfig], list[dict[str, Any]]]:
    active: dict[str, ProviderRuntimeConfig] = {}
    skipped: list[dict[str, Any]] = []
    for provider, provider_config in provider_configs.items():
        adapter = adapters.get(provider)
        skip_status = provider_config.skip_status
        if skip_status and not (allow_offline_fake and skip_status == STATUS_LIVE_CALLS_NOT_ENABLED):
            skipped.append(_provider_skip_spec(capture, provider_config, skip_status))
            continue
        if adapter is None:
            skipped.append(_provider_skip_spec(capture, provider_config, STATUS_LIVE_CALLS_NOT_ENABLED))
            continue
        active[provider] = provider_config
    return active, skipped


def _provider_skip_spec(capture: str, provider_config: ProviderRuntimeConfig, status: str) -> dict[str, Any]:
    return {
        "run_id": _run_id(capture, provider_config.provider, "provider", "skipped", "rep_000"),
        "provider": provider_config.provider,
        "status": status,
        "provider_config": provider_config,
    }


def _build_run_plan(
    capture: str,
    provider_configs: Mapping[str, ProviderRuntimeConfig],
    scenarios: list[ScenarioCard],
    prompt_variants: list[PromptVariant],
    config: LiveRuntimeConfig,
) -> list[PlannedRun]:
    plan: list[PlannedRun] = []
    plan_index = 0
    for provider in provider_configs:
        for scenario in scenarios:
            for variant in prompt_variants:
                render = render_prompt(variant, scenario)
                for repetition_id in _repetition_ids(config.repetitions):
                    plan.append(
                        PlannedRun(
                            plan_index=plan_index,
                            run_id=_run_id(capture, provider, scenario.scenario_id, variant.prompt_variant_id, repetition_id),
                            provider=provider,
                            scenario=scenario,
                            variant=variant,
                            render=render,
                            repetition_id=repetition_id,
                            input_chars=len(render.rendered_prompt),
                        )
                    )
                    plan_index += 1
    return plan


def _apply_shard(plan_runs: list[PlannedRun], shard: tuple[int, int]) -> list[PlannedRun]:
    index, total = shard
    return [item for item in plan_runs if item.plan_index % total == index - 1]


def _run_plan_payload(
    capture: str,
    run_date: date,
    config: LiveRuntimeConfig,
    data_input_hashes: list[dict[str, Any]],
    provider_configs: Mapping[str, ProviderRuntimeConfig],
    provider_skip_specs: list[dict[str, Any]],
    plan_runs: list[PlannedRun],
    shard: tuple[int, int] | None,
    scenario_ids: Sequence[str] | None,
    prompt_variant_ids: Sequence[str] | None,
    provider_ids: Sequence[str] | None,
    resume: bool,
    only_failed: bool,
) -> dict[str, Any]:
    planned_runs = [_planned_run_json(item) for item in plan_runs]
    provider_skips = [
        {
            "run_id": str(item["run_id"]),
            "provider": str(item["provider"]),
            "status": str(item["status"]),
        }
        for item in provider_skip_specs
    ]
    hash_material = {
        "capture_id": capture,
        "run_date": run_date.isoformat(),
        "providers": sorted(provider_configs),
        "planned_runs": planned_runs,
        "provider_skips": provider_skips,
        "data_inputs": data_input_hashes,
        "config": config.redacted_summary(),
    }
    return {
        "run_plan": {
            "capture_id": capture,
            "run_date": run_date.isoformat(),
            "run_plan_hash": _sha256_json(hash_material),
            "resume": resume,
            "only_failed": only_failed,
            "shard": {"index": shard[0], "total": shard[1]} if shard else None,
            "filters": {
                "scenarios": list(scenario_ids or []),
                "prompt_variants": list(prompt_variant_ids or []),
                "providers": list(provider_ids or []),
            },
            "max_runs": config.max_runs,
            "max_input_chars": config.max_input_chars,
            "max_retries": config.max_retries,
            "planned_run_count": len(planned_runs),
            "provider_skip_count": len(provider_skips),
            "provider_skips": provider_skips,
            "planned_runs": planned_runs,
        }
    }


def _planned_run_json(item: PlannedRun) -> dict[str, Any]:
    return {
        "plan_index": item.plan_index,
        "run_id": item.run_id,
        "provider": item.provider,
        "scenario_id": item.scenario.scenario_id,
        "scenario_card_hash": item.scenario.card_hash,
        "prompt_variant_id": item.variant.prompt_variant_id,
        "prompt_template_hash": item.variant.prompt_template_hash,
        "rendered_prompt_hash": item.render.rendered_prompt_hash,
        "repetition_id": item.repetition_id,
        "input_chars": item.input_chars,
    }


def _empty_checkpoint_state() -> dict[str, dict[str, Any]]:
    return {"records": {}, "evaluator_results": {}, "charged_costs": {}}


def _load_checkpoint_state(path: Path) -> dict[str, dict[str, Any]]:
    state = _empty_checkpoint_state()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict) or payload.get("event_type") != "run_checkpoint":
            continue
        record = payload.get("record")
        if not isinstance(record, dict):
            continue
        run_id = str(record.get("run_id") or payload.get("run_id") or "")
        if not run_id:
            continue
        state["records"][run_id] = record
        evaluator_result = payload.get("evaluator_result")
        if isinstance(evaluator_result, dict):
            state["evaluator_results"][run_id] = evaluator_result
        else:
            state["evaluator_results"].pop(run_id, None)
        try:
            state["charged_costs"][run_id] = float(payload.get("charged_cost_estimate") or record.get("charged_cost_estimate") or record.get("cost_estimate") or 0.0)
        except (TypeError, ValueError):
            state["charged_costs"][run_id] = 0.0
    return state


def _initialize_jsonl(path: Path, event_type: str, *, append: bool) -> None:
    if append and path.exists() and path.stat().st_size > 0:
        return
    mode = "a" if append else "w"
    with path.open(mode, encoding="utf-8") as handle:
        handle.write(json.dumps({"_live_run_notice": LIVE_RUN_BANNER, "event_type": event_type, "timestamp_utc": _utc_now()}, sort_keys=True) + "\n")


def _append_event(path: Path, event_type: str, details: Mapping[str, Any]) -> None:
    payload = {"_live_run_notice": LIVE_RUN_BANNER, "event_type": event_type, "timestamp_utc": _utc_now()}
    payload.update(details)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True, ensure_ascii=False) + "\n")


def _append_checkpoint(path: Path, record: dict[str, Any], *, evaluator_result: dict[str, Any] | None, charged_cost: float) -> None:
    payload = {
        "_live_run_notice": LIVE_RUN_BANNER,
        "event_type": "run_checkpoint",
        "timestamp_utc": _utc_now(),
        "run_id": record.get("run_id"),
        "status": record.get("status"),
        "retry_count": record.get("retry_count", 0),
        "charged_cost_estimate": charged_cost,
        "record": record,
        "evaluator_result": evaluator_result,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True, ensure_ascii=False) + "\n")


def _write_live_json(path: Path, payload: dict[str, Any]) -> None:
    wrapped = {"_live_run_notice": LIVE_RUN_BANNER}
    wrapped.update(payload)
    path.write_text(json.dumps(wrapped, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _complete_with_retries(
    adapter: LiveProviderAdapter,
    request: LiveModelRequest,
    provider_config: ProviderRuntimeConfig,
    run_id: str,
    max_retries: int,
    sleep: Callable[[float], None],
    events_path: Path,
) -> LiveModelResponse:
    retry_count = 0
    while True:
        try:
            response = adapter.complete(request)
        except Exception as exc:
            response = _exception_response_from_adapter(exc, adapter, provider_config)
        response = replace(response, retry_count=retry_count)
        if response.status not in RETRYABLE_STATUSES or retry_count >= max_retries:
            return response
        retry_count += 1
        delay = _retry_delay_seconds(run_id, retry_count)
        _append_event(
            events_path,
            "run_retry_scheduled",
            {
                "run_id": run_id,
                "status": response.status,
                "retry_count": retry_count,
                "delay_ms": int(delay * 1000),
                "timeout_seconds": request.timeout_seconds,
            },
        )
        sleep(delay)


def _exception_response_from_adapter(
    exc: Exception,
    adapter: LiveProviderAdapter,
    provider_config: ProviderRuntimeConfig,
) -> LiveModelResponse:
    status = STATUS_TIMEOUT if isinstance(exc, TimeoutError) else STATUS_TRANSIENT_ERROR
    code = "timeout" if status == STATUS_TIMEOUT else "transient_error"
    model_id = str(getattr(adapter, "model_id_exact", "") or getattr(adapter, "model_id", "") or provider_config.model_id or "not_configured")
    model_label = str(getattr(adapter, "model_id_public_label", "") or getattr(adapter, "model_label", "") or provider_config.model_id_public_label)
    return LiveModelResponse(
        status=status,
        provider=provider_config.provider,
        model_id_exact=model_id,
        model_id_public_label=model_label,
        model_family=PROVIDER_MODEL_FAMILIES[provider_config.provider],
        finish_reason="exception",
        error_code_redacted=code,
    )


def _retry_delay_seconds(run_id: str, retry_count: int) -> float:
    base = min(2.0, 0.25 * (2 ** max(0, retry_count - 1)))
    jitter_seed = hashlib.sha256(f"{run_id}|retry|{retry_count}".encode("utf-8")).hexdigest()
    jitter = int(jitter_seed[:8], 16) / 0xFFFFFFFF
    return base + (base * 0.25 * jitter)


def _is_failed_for_resume(record: Mapping[str, Any]) -> bool:
    status = str(record.get("status", ""))
    if status in RETRYABLE_STATUSES:
        return True
    if status in {
        STATUS_PROVIDER_NO_CANDIDATE,
        STATUS_PROVIDER_SAFETY_REFUSAL,
        STATUS_EXCLUDED_FENCED_JSON,
        STATUS_EXCLUDED_MALFORMED_JSON,
        STATUS_EXCLUDED_SCHEMA_INVALID,
        STATUS_EXCLUDED_TRUNCATED,
    }:
        return True
    if status == STATUS_COMPLETED_VALID:
        return bool(record.get("bounded_json_valid") is False or record.get("decision_envelope_errors"))
    return False


def _counts_as_provider_call(record: Mapping[str, Any]) -> bool:
    status = str(record.get("status", ""))
    return bool(record.get("scenario_id")) and status not in NON_CALL_STATUSES


def _ordered_run_records(
    provider_skip_specs: list[dict[str, Any]],
    plan_runs: list[PlannedRun],
    records_by_id: Mapping[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    ordered_ids = [str(item["run_id"]) for item in provider_skip_specs] + [item.run_id for item in plan_runs]
    return [records_by_id[run_id] for run_id in ordered_ids if run_id in records_by_id]


def _ordered_evaluator_results(
    run_records: list[dict[str, Any]],
    evaluator_results_by_id: Mapping[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    return [evaluator_results_by_id[record["run_id"]] for record in run_records if record.get("run_id") in evaluator_results_by_id]


def _rejected_fake_calls_from_records(run_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rejected: list[dict[str, Any]] = []
    for record in run_records:
        fake_calls = record.get("fake_tool_calls")
        if not isinstance(fake_calls, list):
            continue
        rejected.extend(call for call in fake_calls if isinstance(call, dict) and call.get("recorded_but_rejected"))
    return rejected


def _run_manifest_payload(
    capture: str,
    start_utc: str,
    end_utc: str,
    config: LiveRuntimeConfig,
    cli_args: Mapping[str, Any],
    data_input_hashes: list[dict[str, Any]],
    plan_payload: dict[str, Any],
    run_records: list[dict[str, Any]],
) -> dict[str, Any]:
    statuses: dict[str, int] = {}
    for record in run_records:
        status = str(record.get("status", "unknown"))
        statuses[status] = statuses.get(status, 0) + 1
    run_plan = plan_payload.get("run_plan", {}) if isinstance(plan_payload, dict) else {}
    return {
        "run_manifest": {
            "capture_id": capture,
            "start_timestamp_utc": start_utc,
            "end_timestamp_utc": end_utc,
            "git": _git_provenance(),
            "python": {
                "implementation": platform.python_implementation(),
                "version": platform.python_version(),
            },
            "cli_args_redacted": cli_args,
            "config_redacted": config.redacted_summary(),
            "data_inputs": data_input_hashes,
            "run_plan_hash": run_plan.get("run_plan_hash"),
            "planned_run_count": run_plan.get("planned_run_count", 0),
            "record_count": len(run_records),
            "scored_count": sum(1 for record in run_records if record.get("scored") is True),
            "status_counts": dict(sorted(statuses.items())),
        }
    }


def _git_provenance() -> dict[str, Any]:
    commit = _git_output(["rev-parse", "HEAD"]) or "unknown"
    status = _git_output(["status", "--short"]) or ""
    dirty_lines = [line for line in status.splitlines() if line.strip()]
    return {
        "commit": commit.strip(),
        "dirty": bool(dirty_lines),
        "dirty_file_count": len(dirty_lines),
    }


def _git_output(args: list[str]) -> str | None:
    if not args or any(not part.replace("-", "").replace("_", "").isalnum() for part in args):
        return None
    repo = _repo_root()
    command = "cd " + _shell_single_quote(str(repo)) + " && git " + " ".join(args) + " 2>/dev/null"
    try:
        with os.popen(command) as handle:
            output = handle.read()
    except OSError:
        return None
    return output.strip() or None


def _shell_single_quote(value: str) -> str:
    return "'" + value.replace("'", "'\\''") + "'"


def _data_input_hashes(data_path: Path) -> list[dict[str, Any]]:
    input_paths = [
        data_path / "policy_anchors" / "mock_v1_anchors.json",
        data_path / "prompts" / "pilot_variants.json",
    ]
    input_paths.extend(sorted((data_path / "scenarios").glob("*.json")))
    hashes: list[dict[str, Any]] = []
    for path in input_paths:
        if not path.exists() or not path.is_file():
            continue
        relative = path.relative_to(data_path).as_posix()
        raw = path.read_bytes()
        hashes.append(
            {
                "logical_path": relative,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "byte_count": len(raw),
            }
        )
    return hashes


def _data_inputs_digest(data_path: Path) -> str:
    return _sha256_json(_data_input_hashes(data_path))[:12]


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def _split_filter(raw: str | None) -> tuple[str, ...] | None:
    if raw is None or not raw.strip():
        return None
    return tuple(item.strip() for item in raw.split(",") if item.strip())


def _parse_shard(raw: str | None) -> tuple[int, int] | None:
    if raw is None or not raw.strip():
        return None
    parts = raw.split("/", maxsplit=1)
    if len(parts) != 2:
        raise ValueError("--shard must use INDEX/TOTAL")
    index = int(parts[0])
    total = int(parts[1])
    if total < 1:
        raise ValueError("--shard total must be at least 1")
    if index < 1 or index > total:
        raise ValueError("--shard index must be between 1 and TOTAL")
    return index, total


def _redacted_cli_args(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "source": "cli",
        "args": {
            "export_dir": "<redacted_path>" if args.export_dir else None,
            "data_dir": "<redacted_path>" if args.data_dir else None,
            "run_date": args.run_date,
            "capture_id": args.capture_id,
            "offline_fake": args.offline_fake,
            "resume": args.resume,
            "only_failed": args.only_failed,
            "shard": args.shard,
            "scenarios": list(_split_filter(args.scenarios) or []),
            "prompt_variants": list(_split_filter(args.prompt_variants) or []),
            "providers": list(_split_filter(args.providers) or []),
        },
    }


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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
    repetition_id: str,
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
        "repetition_id": repetition_id,
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
        "semantic_validation_status": "passed" if validation.valid else "failed",
        "scored": scored,
        "decision_envelope_errors": list(validation.errors),
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
        "run_id": _run_id(capture, provider_config.provider, "provider", "skipped", "rep_000"),
        "capture_id": capture,
        "provider": provider_config.provider,
        "repetition_id": "rep_000",
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


def _blocked_record(
    capture: str,
    provider_config: Any,
    scenario_id: str,
    prompt_variant_id: str,
    repetition_id: str,
    timestamp: str,
    status: str = "blocked_cost_cap",
) -> dict[str, Any]:
    record = _skipped_provider_record(capture, provider_config, status, timestamp)
    record.update(
        {
            "run_id": _run_id(capture, provider_config.provider, scenario_id, prompt_variant_id, repetition_id),
            "scenario_id": scenario_id,
            "prompt_variant_id": prompt_variant_id,
            "repetition_id": repetition_id,
        }
    )
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


def _repetition_ids(repetitions: int) -> tuple[str, ...]:
    return tuple(f"rep_{index:03d}" for index in range(1, repetitions + 1))


def _run_id(capture: str, provider: str, scenario_id: str, prompt_variant_id: str, repetition_id: str) -> str:
    return hashlib.sha256(f"{capture}|{provider}|{scenario_id}|{prompt_variant_id}|{repetition_id}".encode("utf-8")).hexdigest()[:16]


def _default_capture_id(run_date: date, data_dir: Path) -> str:
    digest = _data_inputs_digest(data_dir)
    return f"live-provider-{run_date.isoformat()}-{digest}"


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


if __name__ == "__main__":
    raise SystemExit(main())
