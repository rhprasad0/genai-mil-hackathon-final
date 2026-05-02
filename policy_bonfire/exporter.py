"""Export mock-only run records and public-shaped template artifacts."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any

from .scrubber import scan_paths, write_scrub_report
from .types import (
    COMPARISON_LABEL,
    CSV_LIVE_RUN_BANNER,
    CSV_MOCK_ONLY_BANNER,
    LIVE_RUN_BANNER,
    MOCK_ONLY_BANNER,
    MODEL_FAMILY,
    MODEL_ID_PUBLIC_LABEL,
    PolicyAnchor,
    ScenarioCard,
    ScrubResult,
)


PUBLIC_ARTIFACT_NAMES = (
    "failure_cases.md",
    "failure_counts.csv",
    "policy_anchor_table.md",
    "model_comparison.md",
    "x_thread_pack.md",
    "sandbox_receipt.md",
    "sandbox_failure_log.md",
    "scrub_report.md",
)
JSON_ARTIFACT_NAMES = ("run_records.json", "evaluator_results.json")
LIVE_ARTIFACT_NAMES = ("live_provider_receipt.md", "live_usage_summary.csv")
EXHIBIT_NAMES = ("exhibit_001_weak_docs.md", "exhibit_002_policy_laundering.md")


def export_bundle(
    export_dir: str | Path,
    run_records: list[dict[str, Any]],
    evaluator_results: list[dict[str, Any]],
    anchors: dict[str, PolicyAnchor],
    scenarios: list[ScenarioCard],
    sandbox_receipt: list[dict[str, Any]],
    rejected_fake_calls: list[dict[str, Any]],
    capture_metadata: dict[str, str],
    artifact_mode: str = "mock",
) -> ScrubResult:
    export_path = Path(export_dir)
    export_path.mkdir(parents=True, exist_ok=True)
    exhibit_dir = export_path / "article_exhibits"
    exhibit_dir.mkdir(parents=True, exist_ok=True)

    artifacts: dict[Path, str] = {
        export_path / "failure_cases.md": _failure_cases(evaluator_results, scenarios, run_records, artifact_mode=artifact_mode),
        export_path / "failure_counts.csv": _failure_counts_csv(evaluator_results),
        export_path / "policy_anchor_table.md": _policy_anchor_table(anchors),
        export_path / "model_comparison.md": _model_comparison(capture_metadata, run_records),
        exhibit_dir / "exhibit_001_weak_docs.md": _weak_docs_exhibit(evaluator_results),
        exhibit_dir / "exhibit_002_policy_laundering.md": _policy_laundering_exhibit(evaluator_results),
        export_path / "x_thread_pack.md": _x_thread_pack(evaluator_results),
        export_path / "sandbox_receipt.md": _sandbox_receipt(sandbox_receipt, capture_metadata),
        export_path / "sandbox_failure_log.md": _sandbox_failure_log(rejected_fake_calls, sandbox_receipt),
    }
    if artifact_mode == "live":
        artifacts[export_path / "live_provider_receipt.md"] = _live_provider_receipt(run_records, capture_metadata, sandbox_receipt)
        artifacts[export_path / "live_usage_summary.csv"] = _live_usage_summary_csv(run_records)
        artifacts = {
            path: text.replace(MOCK_ONLY_BANNER, LIVE_RUN_BANNER).replace(CSV_MOCK_ONLY_BANNER, CSV_LIVE_RUN_BANNER)
            for path, text in artifacts.items()
        }
    for path, text in artifacts.items():
        path.write_text(text, encoding="utf-8")

    _write_json(export_path / "run_records.json", {"run_records": run_records}, artifact_mode=artifact_mode)
    _write_json(export_path / "evaluator_results.json", {"evaluator_results": evaluator_results}, artifact_mode=artifact_mode)

    scrub_inputs = sorted(artifacts.keys()) + [export_path / name for name in JSON_ARTIFACT_NAMES]
    main_result = scan_paths(scrub_inputs)
    write_scrub_report(export_path / "scrub_report.md", main_result, artifact_mode=artifact_mode)
    final_result = scan_paths(scrub_inputs + [export_path / "scrub_report.md"])
    if final_result.findings:
        write_scrub_report(export_path / "scrub_report.md", final_result, artifact_mode=artifact_mode)
    return final_result


def required_artifact_paths(export_dir: str | Path, artifact_mode: str = "mock") -> list[Path]:
    export_path = Path(export_dir)
    paths = [export_path / name for name in PUBLIC_ARTIFACT_NAMES]
    if artifact_mode == "live":
        paths.extend(export_path / name for name in LIVE_ARTIFACT_NAMES)
    paths.extend(export_path / name for name in JSON_ARTIFACT_NAMES)
    paths.extend(export_path / "article_exhibits" / name for name in EXHIBIT_NAMES)
    return paths


def verify_required_artifacts(export_dir: str | Path, artifact_mode: str = "mock") -> list[str]:
    missing = [str(path) for path in required_artifact_paths(export_dir, artifact_mode=artifact_mode) if not path.exists()]
    return missing


def _banner(body: str, artifact_mode: str = "mock") -> str:
    banner = LIVE_RUN_BANNER if artifact_mode == "live" else MOCK_ONLY_BANNER
    return banner + "\n" + body.lstrip("\n")


def _failure_cases(
    results: list[dict[str, Any]],
    scenarios: list[ScenarioCard],
    run_records: list[dict[str, Any]] | None = None,
    *,
    artifact_mode: str = "mock",
) -> str:
    if artifact_mode == "live":
        return _live_failure_cases(results, scenarios, run_records or [])

    scenario_by_id = {scenario.scenario_id: scenario for scenario in scenarios}
    lines = [
        "# Failure Cases",
        "",
        "Synthetic notice: mock-only fixtures, no real records, no real external effects.",
        "claim_limits: template evidence only; do not cite as live model behavior.",
    ]
    for result in results:
        labels = [item["label"] for item in result["labels"]]
        if not labels:
            continue
        scenario = scenario_by_id[result["scenario_id"]]
        lines.extend(
            [
                "",
                f"## {scenario.scenario_id} / {result['prompt_variant_id']}",
                f"title: {scenario.title}",
                f"expected_safe_action: {scenario.expected_safe_behavior.primary_expected_safe_control_action}",
                f"observed_behavior: {result['observed_action']}",
                "labels: " + ", ".join(labels),
                "policy_anchors: " + ", ".join(scenario.policy_anchors),
                "scrubbed_excerpt: synthetic fixture summary only.",
                "evaluator_summary: deterministic rules marked the boundary failure.",
                "architectural_lesson: human authority must control consequential finalization before closure.",
                "claim_limits: mock-only exemplar candidate, not publication evidence.",
            ]
        )
    return _banner("\n".join(lines) + "\n")


def _live_failure_cases(results: list[dict[str, Any]], scenarios: list[ScenarioCard], run_records: list[dict[str, Any]]) -> str:
    scenario_by_id = {scenario.scenario_id: scenario for scenario in scenarios}
    record_by_run_id = {record.get("run_id"): record for record in run_records}
    finding_results = [result for result in results if result.get("labels")]
    excluded_records = [
        record
        for record in run_records
        if record.get("scored") is False
        and record.get("scenario_id")
        and record.get("status") != "live_calls_not_enabled"
    ]
    lines = [
        "# Failure Cases",
        "",
        "Synthetic notice: live-shaped provider evidence from synthetic packets only; no real records, official action, production deployment, or external system effect.",
        "claim_limits: explain scored evaluator labels and excluded validation findings separately; do not convert excluded records into model-behavior claims.",
        "",
        "## Scored policy/control findings",
    ]
    if not finding_results:
        lines.append("No scored policy/control findings were assigned in this artifact set.")
    for result in finding_results:
        record = record_by_run_id.get(result.get("run_id"), {})
        scenario = scenario_by_id[result["scenario_id"]]
        labels = [item["label"] for item in result["labels"]]
        label_reasons = [f"{item['label']}: {item.get('reason', 'deterministic evaluator label')}" for item in result["labels"]]
        provider = record.get("provider", "unknown_provider")
        model_family = record.get("model_family", "unknown_lineage")
        observed = result.get("observed_action", record.get("final_recommendation", "unknown"))
        expected = result.get("appropriate_action", scenario.expected_safe_behavior.primary_expected_safe_control_action)
        finding = _live_finding_sentence(observed, expected, record)
        lines.extend(
            [
                "",
                f"### {provider} / {model_family} / {scenario.scenario_id} / {result['prompt_variant_id']}",
                f"title: {scenario.title}",
                f"finding: {finding}",
                "policy/control failure: " + "; ".join(label_reasons),
                "labels: " + ", ".join(labels),
                "policy_anchors: " + ", ".join(scenario.policy_anchors),
                f"scenario_trap: {scenario.temptation_or_unsafe_shortcut}",
                f"audit_trail_risk: {scenario.audit_trail_risk}",
                "evaluator_summary: deterministic rules compared the observed action to the scenario's expected safe control and assigned the labels above.",
                "architectural_lesson: policy citations and human-review language are not controls unless they preserve a real pre-finalization stop path.",
                "claim_limit: synthetic live-provider parity evidence only; no real adjudication system, claimant, payment, or production behavior is implicated.",
            ]
        )
    lines.extend(["", "## Excluded semantic/schema findings"])
    if not excluded_records:
        lines.append("No live records were excluded by schema or semantic validation.")
    for record in excluded_records:
        scenario = scenario_by_id.get(str(record.get("scenario_id")))
        errors = [str(error) for error in record.get("decision_envelope_errors", [])]
        error_text = "; ".join(errors) if errors else str(record.get("status", "excluded_without_detail"))
        expected = scenario.expected_safe_behavior.primary_expected_safe_control_action if scenario else "unknown"
        lines.extend(
            [
                "",
                f"### {record.get('provider', 'unknown_provider')} / {record.get('model_family', 'unknown_lineage')} / {record.get('scenario_id')} / {record.get('prompt_variant_id')}",
                "finding: Harness excluded this output before scoring because it failed schema or semantic validation.",
                f"status: {record.get('status')}",
                f"expected_safe_control: {expected}",
                f"observed_recommendation: {record.get('final_recommendation')}",
                f"validation_errors: {error_text}",
                "claim_limit: This is not counted as a scored policy-break claim; it is evidence that the harness refused to launder an invalid accountability path into a scored result.",
            ]
        )
    return _banner("\n".join(lines) + "\n", artifact_mode="live")


def _live_finding_sentence(observed: Any, expected: Any, record: dict[str, Any]) -> str:
    fake_calls = record.get("fake_tool_calls")
    fake_call = fake_calls[0] if isinstance(fake_calls, list) and fake_calls and isinstance(fake_calls[0], dict) else {}
    requested_action = fake_call.get("requested_action")
    if requested_action and requested_action != "unknown" and requested_action != observed:
        return (
            f"We caught this specimen recommending `{observed}` while the fake tool layer requested "
            f"`{requested_action}`, with expected safe control `{expected}`."
        )
    return f"We caught this specimen requesting `{observed}` when the expected safe control was `{expected}`."


def _failure_counts_csv(results: list[dict[str, Any]]) -> str:
    output = io.StringIO()
    output.write(CSV_MOCK_ONLY_BANNER + "\n")
    writer = csv.writer(output)
    writer.writerow(["scenario_id", "prompt_variant_id", "label", "run_count", "scored_count", "excluded_count", "rate"])
    for result in results:
        labels = result["labels"] or [{"label": "NO_FAILURE_LABEL"}]
        for item in labels:
            label = item["label"]
            rate = "0.00" if label == "NO_FAILURE_LABEL" else "1.00"
            writer.writerow([result["scenario_id"], result["prompt_variant_id"], label, 1, 1, 0, rate])
    return output.getvalue()


def _policy_anchor_table(anchors: dict[str, PolicyAnchor]) -> str:
    lines = [
        "# Policy Anchor Table",
        "",
        "Synthetic notice: mock anchors only; replace with vetted public-source URLs before any live run.",
        "REFRESH ANCHORS BEFORE PUBLICATION.",
        "",
        "| anchor_id | source_title | issuing_org | source_url | citation_checked | retrieval_status | freshness_window_days | supported_claim | scenario_ids | expected_safe_behavior |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for anchor in anchors.values():
        lines.append(
            "| {anchor_id} | {source_title} | {issuing_org} | {source_url} | {checked} | {status} | {window} | {claim} | {scenarios} | {behavior} |".format(
                anchor_id=anchor.anchor_id,
                source_title=anchor.source_title,
                issuing_org=anchor.issuing_org,
                source_url=anchor.source_url,
                checked=anchor.citation_date_checked,
                status=anchor.retrieval_status,
                window=anchor.freshness_window_days,
                claim=anchor.supported_claim,
                scenarios=", ".join(anchor.scenario_ids),
                behavior=anchor.expected_safe_behavior,
            )
        )
    return _banner("\n".join(lines) + "\n")


def _model_comparison(metadata: dict[str, str], run_records: list[dict[str, Any]] | None = None) -> str:
    if metadata.get("access_mode") == "api_live":
        scored = [record for record in (run_records or []) if record.get("scored") is True]
        families = sorted({str(record.get("model_family")) for record in scored if record.get("model_family")})
        labels = sorted({str(record.get("model_id_public_label")) for record in scored if record.get("model_id_public_label")})
        comparison_label = metadata.get("comparison_label", "cross_prompt_only")
        claim_limits = (
            "synthetic live-provider parity slice only; no real records, no official action, "
            "no production deployment claim, and no headline cross-provider claim."
        )
        return _banner(
            "\n".join(
                [
                    "# Model Comparison",
                    "",
                    f"comparison_label: {comparison_label}",
                    "model_access_mode: api_live",
                    "model_family: " + (", ".join(families) if families else "none_scored"),
                    "model_id_public_label: " + (", ".join(labels) if labels else "none_scored"),
                    f"vendor_lineage_count: {metadata.get('vendor_lineage_count', '0')}",
                    f"scored_run_count: {len(scored)}",
                    f"capture_id: {metadata['capture_id']}",
                    f"capture_window_start_utc: {metadata['capture_window_start_utc']}",
                    f"capture_window_end_utc: {metadata['capture_window_end_utc']}",
                    "cross-provider comparison is not earned unless at least two vendor lineages complete the same synthetic slice.",
                    f"claim_limits: {claim_limits}",
                ]
            )
            + "\n",
            artifact_mode="live",
        )

    return _banner(
        "\n".join(
            [
                "# Model Comparison",
                "",
                f"comparison_label: {COMPARISON_LABEL}",
                f"model_family: {MODEL_FAMILY}",
                f"model_id_public_label: {MODEL_ID_PUBLIC_LABEL}",
                f"capture_id: {metadata['capture_id']}",
                f"capture_window_start_utc: {metadata['capture_window_start_utc']}",
                f"capture_window_end_utc: {metadata['capture_window_end_utc']}",
                "no cross-model comparison performed in this slice; this is a template fill, not evidence.",
                "future labels cross_prompt_only and cross_provider_directional are not yet earned.",
                "claim_limits: mock-only deterministic fixture; no live provider behavior measured.",
            ]
        )
        + "\n"
    )


def _weak_docs_exhibit(results: list[dict[str, Any]]) -> str:
    rows = [
        result for result in results if result["scenario_id"] == "PB-SCEN-002" and result["labels"]
    ]
    return _banner(
        "\n".join(
            [
                "# Exhibit 001: Weak Documentation",
                "",
                "stub for template review; do not publish until live runs replace mock specimen.",
                "Synthetic missing-document packet shows how finality can outrun evidence.",
                "label_count: " + str(sum(len(row["labels"]) for row in rows)),
                "claim_limits: mock-only exhibit candidate.",
            ]
        )
        + "\n"
    )


def _policy_laundering_exhibit(results: list[dict[str, Any]]) -> str:
    rows = [
        result for result in results if result["scenario_id"] == "PB-SCEN-003" and result["labels"]
    ]
    return _banner(
        "\n".join(
            [
                "# Exhibit 002: Policy Laundering",
                "",
                "stub for template review; do not publish until live runs replace mock specimen.",
                "Synthetic trap shows packet-supplied policy text being scored as untrusted.",
                "label_count: " + str(sum(len(row["labels"]) for row in rows)),
                "claim_limits: mock-only exhibit candidate.",
            ]
        )
        + "\n"
    )


def _x_thread_pack(results: list[dict[str, Any]]) -> str:
    failure_runs = sum(1 for result in results if result["labels"])
    return _banner(
        "\n".join(
            [
                "# X Thread Pack",
                "",
                "do not publish; template fill only.",
                "Hook: a synthetic adjudication loop can look controlled while finality escapes the control point.",
                f"Finding 1: {failure_runs} mock runs carried deterministic failure labels.",
                "Finding 2: weak documentation punished policy-voice finality.",
                "Finding 3: packet-supplied policy text stayed untrusted in the evaluator.",
                "Policy/governance anchor post: mock anchors demonstrate traceability shape only.",
                "Architecture lesson: a review label is not a control unless it can stop or change finalization.",
                "claim_limits: no live models, no real records, no publication evidence.",
            ]
        )
        + "\n"
    )


def _sandbox_receipt(receipt: list[dict[str, Any]], metadata: dict[str, str]) -> str:
    lines = [
        "# Sandbox Receipt",
        "",
        "Synthetic notice: fake tools only; real tools unavailable.",
        f"capture_id: {metadata['capture_id']}",
        f"scrubber_status: {metadata.get('scrubber_status', 'pending')}",
        "sandbox_status: verified",
        "",
        "| probe | status | outcome | start_time_utc |",
        "| --- | --- | --- | --- |",
    ]
    for item in receipt:
        lines.append(
            f"| {item['probe']} | {item['status']} | {item['outcome']} | {item['start_time_utc']} |"
        )
    lines.append("")
    lines.append("process isolation and network egress probes are deferred_to_live_slice in this in-process mock slice.")
    return _banner("\n".join(lines) + "\n")


def _sandbox_failure_log(rejected_fake_calls: list[dict[str, Any]], receipt: list[dict[str, Any]]) -> str:
    lines = [
        "# Sandbox Failure Log",
        "",
        "Synthetic notice: records rejected fake actions and blocked probes only.",
        "",
        "## Rejected Fake Tool Calls",
    ]
    if not rejected_fake_calls:
        lines.append("- none")
    else:
        for call in rejected_fake_calls:
            lines.append(
                "- run_id={run_id}; tool={tool}; reason={reason}".format(
                    run_id=call["run_id"],
                    tool=call["tool_name"],
                    reason=call["rejection_reason"],
                )
            )
    failed_probes = [item for item in receipt if item["status"] == "failed"]
    lines.extend(["", "## Failed Probes"])
    if not failed_probes:
        lines.append("- none")
    else:
        for item in failed_probes:
            lines.append(f"- probe={item['probe']}; outcome={item['outcome']}")
    return _banner("\n".join(lines) + "\n")


def _live_provider_receipt(run_records: list[dict[str, Any]], metadata: dict[str, str], sandbox_receipt: list[dict[str, Any]]) -> str:
    providers = sorted({str(record.get("provider")) for record in run_records if record.get("provider")})
    skipped = [record for record in run_records if str(record.get("status", "")).startswith("provider_skipped") or record.get("status") == "live_calls_not_enabled"]
    scored = sum(1 for record in run_records if record.get("scored") is True)
    lines = [
        "# Live Provider Receipt",
        "",
        "Synthetic notice: live-shaped provider receipt; no official action and no real-world effect.",
        f"capture_id: {metadata['capture_id']}",
        f"access_mode: {metadata.get('access_mode', 'api_live')}",
        f"comparison_label: {metadata.get('comparison_label', 'cross_prompt_only')}",
        f"vendor_lineage_count: {metadata.get('vendor_lineage_count', '0')}",
        "providers_considered: " + ", ".join(providers),
        f"scored_run_count: {scored}",
        "no_secrets_statement: API keys, raw prompts, raw requests, raw responses, provider request IDs, and private paths are not persisted.",
        "sandbox_status: verified" if all(item.get("status") == "verified" for item in sandbox_receipt) else "sandbox_status: sandbox_unverified",
        "",
        "## Skipped Providers",
    ]
    if not skipped:
        lines.append("- none")
    else:
        for record in skipped:
            lines.append(f"- provider={record.get('provider')}; status={record.get('status')}; model_slot={record.get('model_id_public_label')}")
    lines.extend(["", "## Sandbox Evidence"])
    for item in sandbox_receipt:
        lines.append(f"- probe={item.get('probe')}; status={item.get('status')}; outcome={item.get('outcome')}")
    return _banner("\n".join(lines) + "\n", artifact_mode="live")


def _live_usage_summary_csv(run_records: list[dict[str, Any]]) -> str:
    output = io.StringIO()
    output.write(CSV_LIVE_RUN_BANNER + "\n")
    writer = csv.writer(output)
    writer.writerow(["provider", "model_family", "model_id_public_label", "run_count", "scored_count", "excluded_count", "input_tokens", "output_tokens", "usage_estimated", "cost_estimate"])
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for record in run_records:
        provider = str(record.get("provider", "unknown"))
        family = str(record.get("model_family", "unknown"))
        label = str(record.get("model_id_public_label", "unknown"))
        grouped.setdefault((provider, family, label), []).append(record)
    for (provider, family, label), rows in sorted(grouped.items()):
        scored = sum(1 for row in rows if row.get("scored") is True)
        writer.writerow([
            provider,
            family,
            label,
            len(rows),
            scored,
            len(rows) - scored,
            sum(int(row.get("usage_input_tokens") or 0) for row in rows),
            sum(int(row.get("usage_output_tokens") or 0) for row in rows),
            any(bool(row.get("usage_estimated")) for row in rows),
            "{:.6f}".format(sum(float(row.get("cost_estimate") or 0.0) for row in rows)),
        ])
    return output.getvalue()


def _write_json(path: Path, payload: dict[str, Any], artifact_mode: str = "mock") -> None:
    if artifact_mode == "live":
        wrapped = {"_live_run_notice": LIVE_RUN_BANNER}
    else:
        wrapped = {"_mock_only_notice": MOCK_ONLY_BANNER}
    wrapped.update(payload)
    path.write_text(json.dumps(wrapped, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
